__author__ = 'adrien'
from backend.constants import FILES_PATHS
from backend.FFmpegSupervisor import start_supervisor
from backend.startup_check import startup_check
from pymongo import MongoClient
import setproctitle
from time import sleep
from autobahn import wamp
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
import asyncio
import signal
from collections import OrderedDict
from multiprocessing import Process
import subprocess
from pprint import pprint
import atexit
import itertools
from datetime import datetime, timedelta
import os
from uuid import uuid4
import multiprocessing


CLOSING_TIME = False


class Backend(ApplicationSession):

    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)

        self.default_dvd_to_h264 = OrderedDict()
        self.default_dvd_to_h264['part1'] = ['nice', '-n', '19', 'ffmpeg', '-y', '-nostdin', '-i']
        self.default_dvd_to_h264['input'] = '/this/is/a/path/video_file.mkv'
        self.default_dvd_to_h264['part2'] = ['-map', '0',
                                             '-c:s', 'copy',
                                             '-c:v', 'libx264', '-crf', '22', '-preset', 'slow',
                                             '-c:a', 'libfdk_aac', '-vbr', '4'
                                             ]
        self.default_dvd_to_h264['output'] = '/this/is/a/path/video_file.mkv'

        self.default_decklink_to_raw = OrderedDict()
        self.default_decklink_to_raw['nice'] = '-n 19'
        self.default_decklink_to_raw['ffmpeg'] = '-y -nostdin -f decklink'
        self.default_decklink_to_raw['-i'] = "'Intensity Pro (1)'@16"
        self.default_decklink_to_raw['-t'] = '10'
        self.default_decklink_to_raw['-acodec'] = 'copy'
        self.default_decklink_to_raw['-vcodec'] = 'copy'
        self.default_decklink_to_raw['-r'] = '25'
        self.default_decklink_to_raw[' '] = '/this/is/a/path/video_file.mkv'

        self.default_raw_to_h264 = OrderedDict()
        self.default_raw_to_h264['nice'] = '-n 19'
        self.default_raw_to_h264['ffmpeg'] = '-y -nostdin'
        self.default_raw_to_h264['-i'] = '/this/is/a/path/video_file.mkv'
        self.default_raw_to_h264['-aspect'] = '4:3'
        self.default_raw_to_h264['-c:v'] = 'libx264 -crf 25 -preset slow -filter:v hqdn3d=3:2:2:3'
        self.default_raw_to_h264['-c:a'] = '-c:a libfdk_aac -vbr 3',
        self.default_raw_to_h264[' '] = '/this/is/a/path/video_file.mkv'

        self.default_log_settings = {
            'action': 'raw_to_h264',
            'dc:identifier': 2,
            'year': 1965,
            'title': 'the holloway',
            'duration': 1/6,
            }

        # this function check that the the directories are writable
        startup_check()

        self.raw_videos_path = FILES_PATHS["raw"]
        self.compressed_videos_path = FILES_PATHS["compressed"]
        self.imported_files_path = FILES_PATHS["imported"]

        self.ffmpeg_supervisor_processes = list()

    @asyncio.coroutine
    def onJoin(self, details):
        print("session ready")

        try:
            res = yield from self.register(self)
            print("{0} procedures registered".format(len(res)))
        except Exception as e:
            print("could not register procedure: {0}".format(e))

        asyncio.async(self.exit_cleanup())
        asyncio.async(self.backend_is_alive_beacon_sender())

    @asyncio.coroutine
    def backend_is_alive_beacon_sender(self):
        while True:
            self.publish('com.digitize_app.backend_is_alive_beacon')
            yield from asyncio.async(asyncio.sleep(2))

    @wamp.register("com.digitize_app.launch_capture")
    def launch_capture(self, metadata):
        print(metadata)
        # todo ajouter les conversions qui doivent attendre dans une liste d'attente et publier cette liste toutes les 2 secondes
        metadata[1]['dc:identifier'] = str(uuid4())
        if metadata[0]["source"] == "decklink_1":
            start_decklink_to_raw(metadata, "Intensity Pro (1)@16", 1)

        elif metadata[0]["source"] == "decklink_2":
            start_decklink_to_raw(metadata, "Intensity Pro (2)@16", 2)

        elif metadata[0]["source"] == "DVD":
            process = start_dvd_conversion(metadata=metadata, ffmpeg_command=self.default_dvd_to_h264,
                                           log_settings=self.default_log_settings)
            self.ffmpeg_supervisor_processes.append(process)

        elif metadata[0]["source"] == "decklink_raw":
            start_raw_to_h264(metadata)

        elif metadata[0]["source"] == "file":
            start_file_import(metadata)

        else:
            raise ValueError("This is not a valid capture request\n" + metadata)

    @asyncio.coroutine
    def exit_cleanup(self):
        while True:
            yield from asyncio.sleep(2)
            self.ffmpeg_supervisor_processes = [process for process in self.ffmpeg_supervisor_processes
                                                if process.is_alive()]
            if CLOSING_TIME and len(self.ffmpeg_supervisor_processes) != 0:
                print("waiting for subprocess to terminate")
            elif CLOSING_TIME and len(self.ffmpeg_supervisor_processes) == 0:
                print("CLOSING_TIME = True")
                break

        loopy = asyncio.get_event_loop()
        for task in asyncio.Task.all_tasks():
            # this is to avoid the cancellation of this coroutine because this coroutine need to be the last one running
            # to cancel all the others.
            if task is not asyncio.Task.current_task():
                task.cancel()

        # little trick to allow the event loop to process the cancel events
        yield from asyncio.sleep(1)

        loopy.stop()


def get_mkv_file_duration(file_path):
    command = [  'ffprobe',
                 '-v',
                 'error',
                 '-select_streams',
                 'v:0',
                 '-show_entries',
                 'format=duration',
                 '-of',
                 'default=noprint_wrappers=1:nokey=1',
                 file_path
               ]

    output = subprocess.check_output(command)
    output = float(output)
    print(output)
    return output


def copy_file(src, dst, doc):
    """
    copy files and ask for low I/O priority

    :param src: string "/this/is/a/source/path.mkv"
    :param dst: string "/this/is/a/destination/path.mkv"
    :param doc: a document from the "waiting_conversions" collection

    :return:
    """
    vuid = doc["metadata"][1]["dc:identifier"]

    db_client = MongoClient("mongodb://localhost:27017/")
    ffmpeg_db = db_client["ffmpeg_conversions"]
    ongoing_conversions_collection = ffmpeg_db["ongoing_conversions"]

    ongoing_conversions_document = {"vuid": vuid,
                                "action": "file_import",
                                "year": doc["metadata"][1]["dcterms:created"],
                                "title": doc["metadata"][1]["dc:title"],
                                "start_date": datetime.now(),
                                "pid": os.getpid(),
                                "return_code": None,
                                "end_date": None,
                                "converted_file_path": None,
                                "log_data": {}
                                }

    ongoing_conversions_document_id = ongoing_conversions_collection.insert(ongoing_conversions_document)
    print("copy function")
    shell_command = ["ionice", "-c", "2", "-n", "7", "cp", "-f", src, dst]
    process = subprocess.Popen(shell_command, stdout=None, stderr=None, universal_newlines=True)
    while True:
        if process.poll() is not None:  # returns None while subprocess is running
            return_code = process.returncode

            ongoing_conversions_collection.find_and_modify(query={"_id": ongoing_conversions_document_id},
                                                update={"$set": {"end_date": datetime.now(),
                                                                 "return_code": return_code,
                                                                 "converted_file_path": dst}}, fsync=True)
            break
        sleep(1)

    db_client.close()


def start_dvd_conversion(metadata, ffmpeg_command, log_settings):
    """
    Gather necessary metadata and launch FFmpeg

    :param metadata: a document from the "waiting_conversions" collection

    :return:
    """
    duration = get_mkv_file_duration(file_path=metadata[0]["file_path"])

    metadata[1]["dc:format"]["duration"] = duration
    ffmpeg_command['input'] = (metadata[0]["file_path"],)
    ffmpeg_command['output'] = (FILES_PATHS['compressed'] + metadata[1]["dc:title"][0] + " -- " + \
        str(metadata[1]["dcterms:created"]) + " -- " + metadata[1]['dc:identifier'] + ".mkv",)

    log_settings["action"] = "dvd_to_h264"
    log_settings["dc:identifier"] = metadata[1]["dc:identifier"]
    log_settings["year"] = metadata[1]["dcterms:created"]
    log_settings["title"] = metadata[1]["dc:title"]
    log_settings["duration"] = duration

    ffmpeg_command = [value for value in ffmpeg_command.values()]
    ffmpeg_command = list(itertools.chain(*ffmpeg_command))
    print(ffmpeg_command)

    p = Process(target=start_supervisor, args=(ffmpeg_command, log_settings))
    p.start()
    return p


def start_decklink_to_raw(doc, decklink_card, decklink_id):
    """
    Gather necessary metadata and launch FFmpeg

    :param doc: a document from the "waiting_conversions" collection
    :param decklink_card: "Intensity Pro (1)@16" or "Intensity Pro (2)@16"
    :param decklink_id: 1 or 2

    :return:
    """
    duration = doc["metadata"][1]["dc:format"]["duration"]

    temp_decklink_to_raw = self.decklink_to_raw.copy()
    temp_decklink_to_raw[9] = decklink_card
    temp_decklink_to_raw[11] = str(duration)
    temp_decklink_to_raw[-1] = self.raw_videos_path + doc["metadata"][1]["dc:title"][0] + " -- " +\
                               str(doc["metadata"][1]["dc:identifier"]) + ".nut"

    temp_log_settings = self.log_settings.copy()
    temp_log_settings["action"] = "decklink_to_raw"
    temp_log_settings["vuid"] = doc["metadata"][1]["dc:identifier"]
    temp_log_settings["year"] = doc["metadata"][1]["dcterms:created"]
    temp_log_settings["title"] = doc["metadata"][1]["dc:title"]
    temp_log_settings["duration"] = duration
    temp_log_settings["decklink_id"] = decklink_id

    p = Process(target=run_ffmpeg, args=(temp_decklink_to_raw, temp_log_settings))
    p.start()


def start_raw_to_h264(doc):
    """
    Gather necessary metadata and launch FFmpeg

    :param doc: a document from the "waiting_conversions" collection

    :return:
    """
    duration = doc["metadata"][1]["dc:format"]["duration"]
    filename = doc["metadata"][0]["filename"]
    size_ratio = doc["metadata"][1]["dc:format"]["size_ratio"]

    temp_raw_to_h264 = self.raw_to_h264.copy()
    temp_raw_to_h264[7] = filename
    temp_raw_to_h264[9] = size_ratio
    temp_raw_to_h264[-1] = self.compressed_videos_path + doc["metadata"][1]["dc:title"][0] + " -- " +\
                           str(doc["metadata"][1]["dc:identifier"]) + ".mkv"

    temp_log_settings = self.log_settings.copy()
    temp_log_settings["action"] = "raw_to_h264"
    temp_log_settings["vuid"] = doc["metadata"][1]["dc:identifier"]
    temp_log_settings["year"] = doc["metadata"][1]["dcterms:created"]
    temp_log_settings["title"] = doc["metadata"][1]["dc:title"]
    temp_log_settings["duration"] = duration

    p = Process(target=run_ffmpeg, args=(temp_raw_to_h264, temp_log_settings))
    p.start()


def start_file_import(doc):
    """
    Gather necessary metadata and launch the copy_file function

    :param doc: a document from the "waiting_conversions" collection

    :return:
    """
    print("start file import")
    filename = doc["metadata"][0]["filename"]
    dest_path = self.imported_files_path + doc["metadata"][1]["dc:title"][0] + " -- " + \
                str(doc["metadata"][1]["dc:identifier"]) + "." + filename.split(sep=".")[-1]

    p = Process(target=copy_file, args=(filename, dest_path, doc))
    p.start()


class GracefulKiller:

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    @staticmethod
    def exit_gracefully(signum, frame):
        global CLOSING_TIME
        CLOSING_TIME = True


if __name__ == "__main__":
    multiprocessing.set_start_method('spawn')
    setproctitle.setproctitle("digitize_backend")
    killer = GracefulKiller()
    runner = ApplicationRunner(url="ws://127.0.0.1:8080/ws", realm="realm1")
    runner.run(Backend)
    print("backend has gracefully exited")

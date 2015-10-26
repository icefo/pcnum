__author__ = 'adrien'
from backend.shared import FILES_PATHS
from backend.CaptureSupervisor import start_supervisor
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
        self.default_decklink_to_raw['part1'] = ['nice', '-n', '19', 'ffmpeg', '-y', '-nostdin', '-f', 'decklink']
        self.default_decklink_to_raw['input'] = "'Intensity Pro (1)'@16"
        self.default_decklink_to_raw['recording_duration'] = '-t 10'
        self.default_decklink_to_raw['part2'] = ['-acodec', 'copy', '-vcodec', 'copy']
        self.default_decklink_to_raw['frame_rate'] = '-r 25'
        self.default_decklink_to_raw['output'] = '/this/is/a/path/video_file.mkv'

        self.default_raw_to_h264 = OrderedDict()
        self.default_raw_to_h264['part1'] = ['nice', '-n', '19', 'ffmpeg', '-y', '-nostdin', '-i']
        self.default_raw_to_h264['input'] = '/this/is/a/path/video_file.mkv'
        self.default_raw_to_h264['aspect_ratio'] = '-aspect 4:3'
        self.default_raw_to_h264['part2'] = ['-c:v', 'libx264', '-crf 25', '-preset', 'slow', '-filter:v', 'hqdn3d=3:2:2:3'
                                             '-c:a', 'libfdk_aac', '-vbr', '3']
        self.default_raw_to_h264['output'] = '/this/is/a/path/video_file.mkv'

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
    def exit_cleanup(self):
        while True:
            yield from asyncio.sleep(2)
            self.ffmpeg_supervisor_processes = [process for process in self.ffmpeg_supervisor_processes
                                                if process.is_alive()]
            if CLOSING_TIME and len(self.ffmpeg_supervisor_processes) != 0:
                print("waiting for subprocess to terminate")
            elif CLOSING_TIME and len(self.ffmpeg_supervisor_processes) == 0:
                print("CLOSING_TIME = True for backend")
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

    @asyncio.coroutine
    def backend_is_alive_beacon_sender(self):
        while True:
            self.publish('com.digitize_app.backend_is_alive_beacon')
            yield from asyncio.async(asyncio.sleep(2))

    @wamp.register("com.digitize_app.launch_capture")
    def launch_capture(self, video_metadata):
        """
        this function dispatch the incoming captures request to the correct functions
        :param video_metadata : [digitise_infos, dublincore_dict]
        """

        print(video_metadata)
        # todo ajouter les conversions qui doivent attendre dans une liste d'attente et publier cette liste toutes les 2 secondes
        video_metadata[1]['dc:identifier'] = str(uuid4())
        if video_metadata[0]["source"] == "decklink_1":
            self.start_decklink_to_raw(video_metadata, "Intensity Pro (1)@16", 1)

        elif video_metadata[0]["source"] == "decklink_2":
            self.start_decklink_to_raw(video_metadata, "Intensity Pro (2)@16", 2)

        elif video_metadata[0]["source"] == "DVD":
            self.start_dvd_conversion(video_metadata)

        elif video_metadata[0]["source"] == "file":
            self.start_file_import(video_metadata)

        else:
            raise ValueError("This is not a valid capture request\n" + video_metadata)

    def start_decklink_to_raw(self, video_metadata, decklink_card, decklink_id):
        """
        Gather necessary metadata and launch FFmpeg

        :param video_metadata : [digitise_infos, dublincore_dict]
        :param decklink_card: "Intensity Pro (1)@16" or "Intensity Pro (2)@16"
        :param decklink_id: 1 or 2
        """
        duration = video_metadata[1]["dc:format"]["duration"]

        ffmpeg_command = self.default_decklink_to_raw.copy()
        ffmpeg_command['input'] = (decklink_card,)
        ffmpeg_command['recording_duration'] = ('-t ' + str(duration),)
        ffmpeg_command['output'] = (FILES_PATHS['raw'] + video_metadata[1]["dc:title"][0] + " -- " +
            str(video_metadata[1]["dcterms:created"]) + " -- " + video_metadata[1]['dc:identifier'] + ".mkv",)

        log_settings = self.default_log_settings.copy()
        log_settings["action"] = "decklink_to_raw"
        log_settings["dc:identifier"] = video_metadata[1]["dc:identifier"]
        log_settings["year"] = video_metadata[1]["dcterms:created"]
        log_settings["title"] = video_metadata[1]["dc:title"]
        log_settings["duration"] = duration
        log_settings["decklink_id"] = decklink_id

        ffmpeg_command = [value for value in ffmpeg_command.values()]
        ffmpeg_command = list(itertools.chain(*ffmpeg_command))

        p = Process(target=start_supervisor, args=(log_settings, video_metadata),
                    kwargs={'ffmpeg_command': ffmpeg_command})
        p.start()
        self.ffmpeg_supervisor_processes.append(p)

    @wamp.register("com.digitize_app.start_raw_to_h264")
    def start_raw_to_h264(self, video_metadata):
        """
        Gather necessary metadata and launch FFmpeg

        :param video_metadata : [digitise_infos, dublincore_dict]
        """
        duration = video_metadata[1]["dc:format"]["duration"]
        file_path = video_metadata[0]["file_path"]
        aspect_ratio = video_metadata[1]["dc:format"]["aspect_ratio"]

        ffmpeg_command = self.default_raw_to_h264.copy()
        ffmpeg_command['input'] = (file_path,)
        ffmpeg_command['aspect_ratio'] = ('-aspect ' + aspect_ratio,)
        ffmpeg_command['output'] = (FILES_PATHS['compressed'] + video_metadata[1]["dc:title"][0] + " -- " +
        str(video_metadata[1]["dcterms:created"]) + " -- " + video_metadata[1]['dc:identifier'] + ".mkv",)
        ffmpeg_command = [value for value in ffmpeg_command.values()]
        ffmpeg_command = list(itertools.chain(*ffmpeg_command))
        print(ffmpeg_command)

        log_settings = self.default_log_settings.copy()
        log_settings["action"] = "raw_to_h264"
        log_settings["dc:identifier"] = video_metadata[1]["dc:identifier"]
        log_settings["year"] = video_metadata[1]["dcterms:created"]
        log_settings["title"] = video_metadata[1]["dc:title"]
        log_settings["duration"] = duration

        p = Process(target=start_supervisor, args=(log_settings, video_metadata),
                    kwargs={'ffmpeg_command': ffmpeg_command})
        p.start()
        self.ffmpeg_supervisor_processes.append(p)

    def start_dvd_conversion(self, video_metadata):
        """
        Gather necessary metadata and launch FFmpeg

        :param video_metadata: [digitise_infos, dublincore_dict]
        """
        duration = get_mkv_file_duration(file_path=video_metadata[0]["file_path"])
        video_metadata[1]["dc:format"]["duration"] = duration

        ffmpeg_command = self.default_dvd_to_h264.copy()
        ffmpeg_command['input'] = (video_metadata[0]["file_path"],)
        ffmpeg_command['output'] = (FILES_PATHS['compressed'] + video_metadata[1]["dc:title"][0] + " -- " +
            str(video_metadata[1]["dcterms:created"]) + " -- " + video_metadata[1]['dc:identifier'] + ".mkv",)
        ffmpeg_command = [value for value in ffmpeg_command.values()]
        ffmpeg_command = list(itertools.chain(*ffmpeg_command))
        print(ffmpeg_command)

        log_settings = self.default_log_settings.copy()
        log_settings["action"] = "dvd_to_h264"
        log_settings["dc:identifier"] = video_metadata[1]["dc:identifier"]
        log_settings["year"] = video_metadata[1]["dcterms:created"]
        log_settings["title"] = video_metadata[1]["dc:title"]
        log_settings["duration"] = duration

        p = Process(target=start_supervisor, args=(log_settings, video_metadata),
                    kwargs={'ffmpeg_command': ffmpeg_command})
        p.start()
        self.ffmpeg_supervisor_processes.append(p)

    def start_file_import(self, video_metadata):
        """
        Gather necessary metadata and launch the copy_file function

        :param video_metadata: [digitise_infos, dublincore_dict]

        :return:
        """
        log_settings = self.default_log_settings.copy()
        log_settings["action"] = "file_import"
        log_settings["dc:identifier"] = video_metadata[1]["dc:identifier"]
        log_settings["year"] = video_metadata[1]["dcterms:created"]
        log_settings["title"] = video_metadata[1]["dc:title"]

        src = video_metadata[0]["file_path"]
        dst = FILES_PATHS['imported'] + video_metadata[1]["dc:title"][0] + " -- " + \
              str(video_metadata[1]["dcterms:created"]) + " -- " + video_metadata[1]['dc:identifier'] +\
              "." + src.split(sep=".")[-1]  # to put the same extension back

        p = Process(target=start_supervisor, args=(log_settings, video_metadata),
                    kwargs={'src_dst': [src, dst]})
        p.start()
        self.ffmpeg_supervisor_processes.append(p)


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

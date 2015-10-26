import subprocess
from pymongo import MongoClient
from datetime import datetime
from pprint import pprint
from setproctitle import setproctitle
from autobahn import wamp
from backend.shared import async_call
import asyncio
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
import signal
import os
import functools


CLOSING_TIME = False


def get_complete_logs_document(command, log_settings):
    complete_logs_document = {"dc:identifier": log_settings["dc:identifier"],
                              "action": log_settings["action"],
                              "year": log_settings["year"],
                              "title": log_settings["title"],
                              "duration": log_settings["duration"],
                              "start_date": str(datetime.now()),
                              "pid": os.getpid(),
                              "command": command,
                              "return_code": None,
                              "end_date": None,
                              "converted_file_path": None,
                              "log_data": []
                              }
    return complete_logs_document


def get_ongoing_conversion_document(log_settings):
    ongoing_conversion_document = {"dc:identifier": log_settings["dc:identifier"],
                                   "action": log_settings["action"],
                                   "year": log_settings["year"],
                                   "title": log_settings["title"],
                                   "duration": log_settings["duration"],
                                   "start_date": str(datetime.now()),
                                   "pid": os.getpid(),
                                   "log_data": {}
                                   }
    if log_settings.get("decklink_id", None):
        ongoing_conversion_document["decklink_id"] = log_settings["decklink_id"]
    return ongoing_conversion_document


class FFmpegWampSupervisor(ApplicationSession):

    def __init__(self, config, ffmpeg_command, log_settings, video_metadata):
        ApplicationSession.__init__(self, config)

        self.ffmpeg_process = None

        db_client = MongoClient("mongodb://localhost:27017/")
        ffmpeg_db = db_client["ffmpeg_conversions"]
        self.complete_conversion_logs_collection = ffmpeg_db["complete_conversion_logs"]
        metadata_db = db_client["metadata"]
        self.videos_metadata = metadata_db["videos_metadata"]

        asyncio.async(self.exit_cleanup())
        asyncio.async(self.run_ffmpeg(ffmpeg_command, log_settings, video_metadata))

    @asyncio.coroutine
    def exit_cleanup(self):
        while True:
            yield from asyncio.sleep(2)
            if CLOSING_TIME and self.ffmpeg_process.poll() is None:
                print("Waiting for conversion to terminate")
            if CLOSING_TIME and self.ffmpeg_process.poll() is not None:
                print("CLOSING_TIME = True for ffmpeg supervisor")
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
        print("FFmpeg supervisor has gracefully exited")

    @asyncio.coroutine
    def run_ffmpeg(self, command, log_settings, video_metadata):
        """

        :param command: list because order matter
            example: ['nice', '-n',  '19', 'echo', 'I like kiwis']
        :param log_settings: dictionary
            example: {
                "action": "raw_to_h264",
                "vuid": 1,
                "year": 1995,
                "title": "the killer cactus' story",
                "duration": 2 (min)
                }
        :param video_metadata: [digitise_infos, dublincore_dict]
        :return:
        """
        complete_logs_document = get_complete_logs_document(command, log_settings)
        ongoing_conversion_document = get_ongoing_conversion_document(log_settings)

        self.ffmpeg_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                               universal_newlines=True)

        complete_logs_document_id = self.complete_conversion_logs_collection.insert(complete_logs_document)

        while True:
            if self.ffmpeg_process.poll() is not None:  # returns None while subprocess is running
                return_code = self.ffmpeg_process.returncode
                self.complete_conversion_logs_collection.find_and_modify(query={"_id": complete_logs_document_id},
                                                                         update={"$set": {"end_date": str(datetime.now()),
                                                                                          "return_code": return_code}},
                                                                         fsync=True
                                                                         )
                converted_file_path = command[-1]

                if return_code == 0 and video_metadata[0]['source'] == 'DVD':

                    self.complete_conversion_logs_collection.find_and_modify(query={"_id": complete_logs_document_id},
                                                                             update={"$set": {"converted_file_path": converted_file_path}},
                                                                             fsync=True)
                    dublincore_dict = video_metadata[1]
                    dublincore_dict['files_path'] = {'h264': converted_file_path}
                    dublincore_dict['source'] = video_metadata[0]['source']
                    self.videos_metadata.insert(dublincore_dict, fsync=True)
                elif return_code == 0 and video_metadata[0]['source'].startswith("decklink_"):
                    @async_call
                    @asyncio.coroutine
                    def call_start_raw_to_h264():
                        yield from self.call('com.digitize_app.start_raw_to_h264', video_metadata)
                        # block until completition so that the task is not cancelled
                    asyncio.wait_for(call_start_raw_to_h264)

                else:
                    os.remove(converted_file_path)
                    raise ChildProcessError("FFMPEG process returned with a non zero code \"", str(return_code),
                                            "\" , see complete log for details")

                global CLOSING_TIME
                CLOSING_TIME = True
                break

            # stdout_line example: frame=  288 fps= 16 q=32.0 size=    1172kB time=00:00:09.77 bitrate= 982.4kbits/s
            stdout_complete_line = self.ffmpeg_process.stdout.readline()

            self.complete_conversion_logs_collection.find_and_modify(query={"_id": complete_logs_document_id},
                                                                     update={"$push": {"log_data": stdout_complete_line}}
                                                                     )

            stdout_line = stdout_complete_line[:-5]
            if stdout_line.startswith("frame="):
                list_of_characters = []
                counter = 0
                for character in stdout_line:
                    if not character == " ":
                        list_of_characters.append(character)
                    elif not stdout_line[counter - 1] == "=" and not stdout_line[counter - 1] == " ":
                        list_of_characters.append(character)
                    counter += 1

                # ffmpeg_output example : frame=17 fps=0.0 q=0.0 size=1kB time=00:00:00.34 bitrate=18.0kbits/s
                ffmpeg_output = "".join(list_of_characters)
                stdout_dictionary = {}
                for key_value in ffmpeg_output.split(" "):
                    a = key_value.split("=")
                    stdout_dictionary[a[0]] = a[1]
                # {'fps': '0.0', 'bitrate': '18.0kbits/s', 'frame': '16', 'time': '00:00:00.34', 'q': '0.0', 'size': '1kB'}
                # yield stdout_dictionary
                ongoing_conversion_document["log_data"] = stdout_dictionary
                self.publish('com.digitize_app.ongoing_conversion', ongoing_conversion_document)


class CopyFileSupervisor(ApplicationSession):
    def __init__(self, config, src_dst, log_settings, video_metadata):
        ApplicationSession.__init__(self, config)
        self.rsync_process = None

        db_client = MongoClient("mongodb://localhost:27017/")
        ffmpeg_db = db_client["ffmpeg_conversions"]
        self.complete_conversion_logs_collection = ffmpeg_db["complete_conversion_logs"]
        metadata_db = db_client["metadata"]
        self.videos_metadata = metadata_db["videos_metadata"]

        asyncio.async(self.exit_cleanup())
        asyncio.async(self.run_rsync(src_dst, log_settings, video_metadata))

    @asyncio.coroutine
    def exit_cleanup(self):
        while True:
            yield from asyncio.sleep(2)
            if CLOSING_TIME and self.rsync_process.poll() is None:
                print("Waiting for copy to terminate")
            if CLOSING_TIME and self.rsync_process.poll() is not None:
                print("CLOSING_TIME = True for rsync supervisor")
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
        print("rsync supervisor has gracefully exited")

    @asyncio.coroutine
    def run_rsync(self, src_dst, log_settings, video_metadata):
        """
        copy files and ask for low I/O priority

        :param src_dst: list ["/this/is/a/source/path.mkv" "/this/is/a/destination/path.mkv"]
        :param video_metadata: [digitise_infos, dublincore_dict]

        :return:
        """
        src = src_dst[0]
        dst = src_dst[1]

        ongoing_conversion_document = get_ongoing_conversion_document(log_settings)
        shell_command = ["ionice", "-c", "2", "-n", "7", "rsync", "-ah", '--progress', src, dst]
        rsync_process = subprocess.Popen(shell_command, stdout=None, stderr=None, universal_newlines=True)
        while True:
            if rsync_process.poll() is not None:  # returns None while subprocess is running
                return_code = rsync_process.returncode
                break
            stdout_complete_line = self.rsync_process.stdout.readline()
            # todo send the progress and not the duration, same for run_ffmpeg


class GracefulKiller:

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    @staticmethod
    def exit_gracefully(signum, frame):
        print("CLOSING TIME for FFmpeg supervisor")
        global CLOSING_TIME
        CLOSING_TIME = True


def start_supervisor(log_settings, video_metadata, ffmpeg_command=None, src_dst=None):
    print("FFmpeg wamp service")
    setproctitle("FFmpeg wamp service")
    GracefulKiller()
    runner = ApplicationRunner(url="ws://127.0.0.1:8080/ws", realm="realm1")
    # todo do a pull request for *args, **kwargs, print_exc() addition
    if ffmpeg_command:
        runner.run(FFmpegWampSupervisor, args=(ffmpeg_command, log_settings, video_metadata))
    elif src_dst:
        runner.run(CopyFileSupervisor, args=(src_dst, log_settings, video_metadata))
    else:
        raise ValueError("Both parameters ffmpeg_command and src_dst are None, this shouldn't happen")

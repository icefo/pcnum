import subprocess
from pymongo import MongoClient
from datetime import datetime
from pprint import pprint
from setproctitle import setproctitle
import functools
from backend.shared import wrap_in_future
import asyncio
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
import signal
import os
import re

# todo fix deprecated mongodb calls


def get_complete_logs_document(command, log_settings):
    """
    Prepare a document that will be put in the database

    Args:
        command (list): list that will be passed to the subprocess.Popen constructor
            Example: ['nice', '-n',  '19', 'echo', 'I like kiwis']
        log_settings (dict):
            Example: {
                "action": "raw_to_h264",
                "dc:identifier": 'a29f7c4d-9523-4c10-b66f-da314b7d992e',
                "year": 1995,
                "title": "the killer cactus' story",
                "duration": 2 (min)
                }

    Returns:
        dict:
    """
    complete_logs_document = {"dc:identifier": log_settings["dc:identifier"],
                              "source": log_settings["source"],
                              "action": log_settings["action"],
                              "year": log_settings["year"],
                              "title": log_settings["title"],
                              "start_date": datetime.now().replace(microsecond=0).isoformat(),
                              "pid": os.getpid(),
                              "command": command,
                              "duration": None,
                              "return_code": None,
                              "end_date": None,
                              "log_data": []
                              }

    if not log_settings['action'] == 'file_import':
        complete_logs_document['duration'] = log_settings['duration']
    if log_settings['action'] == 'decklink_to_raw':
        complete_logs_document['decklink_id'] = log_settings['decklink_id']

    return complete_logs_document


def get_ongoing_conversion_document(log_settings):
    """
    Prepare a document that will be sent to the GUI

    Args:
        log_settings (dict):
            Example: {
                "action": "raw_to_h264",
                "dc:identifier": 'a29f7c4d-9523-4c10-b66f-da314b7d992e',
                "year": 1995,
                "title": "the killer cactus' story",
                "duration": 2 (min)
                }

    Returns:
        dict:
    """
    ongoing_conversion_document = {"dc:identifier": log_settings["dc:identifier"],
                                   "source": log_settings["source"],
                                   "action": log_settings["action"],
                                   "year": log_settings["year"],
                                   "title": log_settings["title"],
                                   "start_date": datetime.now().replace(microsecond=0).isoformat(),
                                   "date_data_send": datetime.now().timestamp(),
                                   "progress": None
                                   }

    if log_settings['action'] == 'decklink_to_raw':
        ongoing_conversion_document["decklink_id"] = log_settings["decklink_id"]
    return ongoing_conversion_document


def get_mkv_file_duration(file_path):
    """
    Get video file duration by asking ffmpeg to look at the container metadata
    Work with mkv files, maybe with other containers too.

    Args:
        file_path (str):

    Returns:
        float: duration of the video file in seconds
    """

    command = ['ffprobe',
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


def get_sec(input_string):
    """
    Convert input_string in seconds

    Notes:
        taken from stackoverflow

    Args:
        input_string (str): 00:00:00

    Returns:
        float:
    """
    l = input_string.split(':')
    return float(l[0]) * 3600 + float(l[1]) * 60 + float(l[2])


class FFmpegWampSupervisor(ApplicationSession):
    """
    Launch ffmpeg, monitor and send the progress

    When the capture is done and if the return code is 0, add the metadata to the database.
    """

    def __init__(self, config):
        ApplicationSession.__init__(self, config)
        self.config_extra = config.extra

        #########
        self.ffmpeg_process = None

        #########
        db_client = MongoClient("mongodb://localhost:27017/")
        digitize_app = db_client['digitize_app']
        self.videos_metadata_collection = digitize_app['videos_metadata']
        self.complete_ffmpeg_logs_collection = digitize_app['complete_ffmpeg_logs']

        #########
        self.close_signal = None

        #########
        loop = asyncio.get_event_loop()
        # You should abort any long operation on SIGINT and you can do what you want SIGTERM
        # In both cases the program should exit cleanly
        # SIGINT = Ctrl-C
        loop.add_signal_handler(signal.SIGINT, functools.partial(self.exit_cleanup, 'SIGINT'))
        # the kill command use the SIGTERM signal by default
        loop.add_signal_handler(signal.SIGTERM, functools.partial(self.exit_cleanup, 'SIGTERM'))

    @asyncio.coroutine
    def onJoin(self, details):
        print("session ready")

        ffmpeg_command, log_settings, video_metadata = self.config_extra['capture_parameters']

        yield from self.run_ffmpeg(ffmpeg_command, log_settings, video_metadata)

    @wrap_in_future  # the signal handler can't call a coroutine directly
    @asyncio.coroutine
    def exit_cleanup(self, close_signal):
        """
        Is called when asyncio catch a 'SIGINT' or 'SIGTERM' signal

        Note:
            The function doesn't have to cancel the capture on 'SIGINT' because subprocess.Popen does it.

        Args:
            close_signal (str): 'SIGINT' or 'SIGTERM'
        """

        self.close_signal = close_signal
        while True:
            yield from asyncio.sleep(2)
            if self.ffmpeg_process.poll() is None:
                print("Waiting for conversion to terminate")
            if self.ffmpeg_process.poll() is not None:
                print("CLOSING_TIME = True for ffmpeg supervisor")
                break

        yield from asyncio.sleep(5)  # give time to run_ffmpeg to log what's happening to the database

        loopy = asyncio.get_event_loop()
        for task in asyncio.Task.all_tasks():
            # this is to avoid the cancellation of this coroutine because this coroutine need to be the last one running
            # to cancel all the others.
            if task is not asyncio.Task.current_task():
                task.cancel()

        # Just to make sure that the cancel events are processed
        yield from asyncio.sleep(1)

        loopy.stop()
        print("FFmpeg supervisor has gracefully exited")

    @asyncio.coroutine
    def run_ffmpeg(self, command, log_settings, video_metadata):
        """
        Launch ffmpeg, monitor and send the progress

        When the capture is done and if the return code is 0, add the metadata to the database.
        Args:
            command (list): list that will be passed to the subprocess.Popen constructor
                Example: ['nice', '-n',  '19', 'echo', 'I like kiwis']
            log_settings (dict):
                Example: {
                    "action": "raw_to_h264_aac",
                    "dc:identifier": 'a29f7c4d-9523-4c10-b66f-da314b7d992e',
                    "year": 1995,
                    "title": "the killer cactus' story",
                    "duration": 2 (min)
                    }
            video_metadata (list): [digitise_infos, dublincore_dict]
        """

        complete_logs_document = get_complete_logs_document(command, log_settings)
        ongoing_conversion_document = get_ongoing_conversion_document(log_settings)

        complete_logs_document_id = self.complete_ffmpeg_logs_collection.insert(complete_logs_document)
        self.ffmpeg_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                               universal_newlines=True)

        while True:
            if self.ffmpeg_process.poll() is not None:  # returns None while subprocess is running
                return_code = self.ffmpeg_process.returncode
                converted_file_path = command[-1]
                self.complete_ffmpeg_logs_collection.update_one(
                    filter={"_id": complete_logs_document_id},
                    update={"$set": {"end_date": datetime.now().replace(microsecond=0), "return_code": return_code}})

                if return_code == 0 and log_settings['action'] == 'dvd_to_h264':
                    dublincore_dict = video_metadata[1]
                    dublincore_dict['files_path'] = {'h264': converted_file_path}
                    dublincore_dict['source'] = video_metadata[0]['source']
                    self.videos_metadata_collection.insert(dublincore_dict)

                elif return_code == 0 and log_settings['action'] == 'decklink_to_raw'\
                        and video_metadata[0]["lossless_import"]:

                    video_metadata[0]["file_path"] = converted_file_path
                    yield from self.call('com.digitize_app.start_raw_to_ffv1_flac', video_metadata)

                elif return_code == 0 and log_settings['action'] == 'decklink_to_raw'\
                        and not video_metadata[0]["lossless_import"]:

                    video_metadata[0]["file_path"] = converted_file_path
                    yield from self.call('com.digitize_app.start_raw_to_h264_aac', video_metadata)

                elif return_code == 0 and log_settings['action'] == 'raw_to_h264_aac':
                    dublincore_dict = video_metadata[1]
                    dublincore_dict['files_path'] = {'h264_aac': converted_file_path}
                    dublincore_dict['source'] = video_metadata[0]['source']
                    os.remove(video_metadata[0]["file_path"])
                    self.videos_metadata_collection.insert(dublincore_dict)

                elif return_code == 0 and log_settings['action'] == 'raw_to_ffv1_flac':
                    dublincore_dict = video_metadata[1]
                    dublincore_dict['files_path'] = {'ffv1_flac': converted_file_path}
                    dublincore_dict['source'] = video_metadata[0]['source']
                    os.remove(video_metadata[0]["file_path"])
                    self.videos_metadata_collection.insert(dublincore_dict)

                else:
                    os.remove(converted_file_path)
                    raise ChildProcessError("FFMPEG process returned with a non zero code \"", str(return_code),
                                            "\" , see complete log for details")
                self.exit_cleanup('SIGTERM')
                break

            # stdout_line example: frame=  288 fps= 16 q=32.0 size=    1172kB time=00:00:09.77 bitrate= 982.4kbits/s
            stdout_complete_line = self.ffmpeg_process.stdout.readline()
            self.complete_ffmpeg_logs_collection.find_and_modify(query={"_id": complete_logs_document_id},
                                                                 update={"$push": {"log_data": stdout_complete_line}}
                                                                 )

            stdout_line = stdout_complete_line.strip()
            if stdout_line.startswith("frame="):
                stdout_line = re.sub(' +', ' ', stdout_line)
                list_of_characters = []
                counter = 0
                for character in stdout_line:
                    if not stdout_line[counter - 1] == "=":
                        list_of_characters.append(character)
                    counter += 1

                # ffmpeg_output example : frame=17 fps=0.0 q=0.0 size=1kB time=00:00:00.34 bitrate=18.0kbits/s
                ffmpeg_output = "".join(list_of_characters)
                stdout_dictionary = {}
                for key_value in ffmpeg_output.split(" "):
                    a = key_value.split("=")
                    stdout_dictionary[a[0]] = a[1]
                # {'fps': '0.0', 'bitrate': '18.0kbits/s', 'frame': '16', 'time': '00:00:00.34', 'q': '0.0', 'size': '1kB'}
                done = get_sec(stdout_dictionary["time"])
                total = log_settings["duration"]
                progress = (done / total)*100
                progress = round(progress)

                ongoing_conversion_document['progress'] = progress
                ongoing_conversion_document["date_data_send"] = datetime.now().timestamp()
                self.publish('com.digitize_app.ongoing_capture', ongoing_conversion_document)


class CopyFileSupervisor(ApplicationSession):
    def __init__(self, config):
        ApplicationSession.__init__(self, config)
        self.config_extra = config.extra

        #########
        self.rsync_process = None

        #########
        db_client = MongoClient("mongodb://localhost:27017/")
        digitize_app = db_client['digitize_app']
        self.videos_metadata_collection = digitize_app['videos_metadata']
        self.complete_rsync_logs_collection = digitize_app['complete_rsync_logs']

        #########
        self.close_signal = None
        loop = asyncio.get_event_loop()
        # You should abort any long operation on SIGINT and you can do what you want SIGTERM
        # In both cases the program should exit cleanly
        # SIGINT = Ctrl-C
        loop.add_signal_handler(signal.SIGINT, functools.partial(self.exit_cleanup, 'SIGINT'))
        # the kill command use the SIGTERM signal by default
        loop.add_signal_handler(signal.SIGTERM, functools.partial(self.exit_cleanup, 'SIGTERM'))

    @asyncio.coroutine
    def onJoin(self, details):
        print("session ready")

        src_dst, log_settings, video_metadata = self.config_extra['capture_parameters']
        yield from self.run_rsync(src_dst, log_settings, video_metadata)

    @wrap_in_future
    @asyncio.coroutine
    def exit_cleanup(self, close_signal):
        """
        Is called when asyncio catch a 'SIGINT' or 'SIGTERM' signal

        Note:
            The function doesn't have to cancel the capture on 'SIGINT' because subprocess.Popen does it.

        Args:
            close_signal (str): 'SIGINT' or 'SIGTERM'
        """

        self.close_signal = close_signal
        while True:
            yield from asyncio.sleep(2)
            if self.rsync_process.poll() is None:
                print("Waiting for copy to terminate")
            if self.rsync_process.poll() is not None:
                print("CLOSING_TIME = True for rsync supervisor")
                break

        # give time to run_rsync to log data to the database
        yield from asyncio.sleep(5)

        loopy = asyncio.get_event_loop()
        for task in asyncio.Task.all_tasks():
            # this is to avoid the cancellation of this coroutine because this coroutine need to be the last one running
            # to cancel all the others.
            if task is not asyncio.Task.current_task():
                task.cancel()

        # Just to make sure that the cancel events are processed
        yield from asyncio.sleep(1)

        loopy.stop()
        print("rsync supervisor has gracefully exited")

    @asyncio.coroutine
    def run_rsync(self, src_dst, log_settings, video_metadata):
        """
        Launch rsync, monitor and send the progress

        When the capture is done and if the return code is 0, add the metadata to the database.
        Args:
            src_dst (list): ["/this/is/a/source/path.mkv" "/this/is/a/destination/path.mkv"]
            log_settings (dict):
                Example: {
                    "action": "raw_to_h264",
                    "dc:identifier": 'a29f7c4d-9523-4c10-b66f-da314b7d992e',
                    "year": 1995,
                    "title": "the killer cactus' story",
                    "duration": 2 (min)
                    }
            video_metadata (list): [digitise_infos, dublincore_dict]
        """

        src = src_dst[0]
        dst = src_dst[1]

        command = ["ionice", "-c", "2", "-n", "7", "rsync", "-ah", '--progress', src, dst]

        complete_logs_document = get_complete_logs_document(command, log_settings)
        ongoing_conversion_document = get_ongoing_conversion_document(log_settings)

        complete_logs_document_id = self.complete_rsync_logs_collection.insert(complete_logs_document)

        self.rsync_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                              universal_newlines=True)
        while True:
            if self.rsync_process.poll() is not None:  # returns None while subprocess is running
                return_code = self.rsync_process.returncode
                converted_file_path = command[-1]
                self.complete_rsync_logs_collection.find_and_modify(query={"_id": complete_logs_document_id},
                                                                    update={"$set": {"end_date": datetime.now().replace(microsecond=0),
                                                                                     "return_code": return_code}
                                                                            }
                                                                    )
                if return_code == 0:
                    dublincore_dict = video_metadata[1]
                    dublincore_dict['files_path'] = {'unknown': converted_file_path}
                    dublincore_dict['source'] = video_metadata[0]['source']
                    self.videos_metadata_collection.insert(dublincore_dict)
                self.exit_cleanup('SIGTERM')
                break

            stdout_complete_line = self.rsync_process.stdout.readline()
            self.complete_rsync_logs_collection.find_and_modify(
                query={"_id": complete_logs_document_id},
                update={"$push": {"log_data": stdout_complete_line}}
                )

            stdout_line = stdout_complete_line.strip()
            stdout_list = re.sub(' +', ' ', stdout_line).split(' ')
            for elem in stdout_list:
                if '%' in elem:
                    ongoing_conversion_document['progress'] = round(float(elem[:-1]))
                    ongoing_conversion_document["date_data_send"] = datetime.now().timestamp()
                    self.publish('com.digitize_app.ongoing_capture', ongoing_conversion_document)
                    break


class MakemkvconSupervisor(ApplicationSession):
    def __init__(self, config):
        ApplicationSession.__init__(self, config)
        self.config_extra = config.extra

        #########
        self.makemkvcon_process = None

        #########
        db_client = MongoClient("mongodb://localhost:27017/")
        digitize_app = db_client['digitize_app']
        self.videos_metadata_collection = digitize_app['videos_metadata']
        self.complete_makemkvcon_logs_collection = digitize_app['complete_makemkvcon_logs']

        #########
        self.close_signal = None
        loop = asyncio.get_event_loop()
        # You should abort any long operation on SIGINT and you can do what you want SIGTERM
        # In both cases the program should exit cleanly
        # SIGINT = Ctrl-C
        loop.add_signal_handler(signal.SIGINT, functools.partial(self.exit_cleanup, 'SIGINT'))
        # the kill command use the SIGTERM signal by default
        loop.add_signal_handler(signal.SIGTERM, functools.partial(self.exit_cleanup, 'SIGTERM'))

        #########

    @asyncio.coroutine
    def onJoin(self, details):
        print("session ready")

        makemkvcon_command, log_settings, video_metadata = self.config_extra['capture_parameters']

        yield from self.run_makemkvcon(makemkvcon_command, log_settings, video_metadata)

    @wrap_in_future
    @asyncio.coroutine
    def exit_cleanup(self, close_signal):
        """
        Is called when asyncio catch a 'SIGINT' or 'SIGTERM' signal

        Note:
            The function doesn't have to cancel the capture on 'SIGINT' because subprocess.Popen does it.

        Args:
            close_signal (str): 'SIGINT' or 'SIGTERM'
        """

        self.close_signal = close_signal
        while True:
            yield from asyncio.sleep(2)
            if self.makemkvcon_process.poll() is None:
                print("Waiting for DVD_import to terminate")
            if self.makemkvcon_process.poll() is not None:
                print("CLOSING_TIME = True for makemkvcon supervisor")
                break

        # give time to run_makemkvcon to log data to the database
        yield from asyncio.sleep(5)

        loopy = asyncio.get_event_loop()
        for task in asyncio.Task.all_tasks():
            # this is to avoid the cancellation of this coroutine because this coroutine need to be the last one running
            # to cancel all the others.
            if task is not asyncio.Task.current_task():
                task.cancel()

        # Just to make sure that the cancel events are processed
        yield from asyncio.sleep(1)

        loopy.stop()
        print("makemkvcon supervisor has gracefully exited")

    @asyncio.coroutine
    def run_makemkvcon(self, makemkvcon_command, log_settings, video_metadata):
        """
        Launch makemkvcon, monitor and send the progress

        When the capture is done and if the return code is 0, add the metadata to the database.
        Args:
            makemkvcon_command (list): ['nice', '-n', '11', 'makemkvcon', '-r', '--minlength=1', '--progress=-same',
                                       'mkv', 'disc:0', 'all', '/this/is/a/path']
            log_settings (dict):
                Example: {
                    "action": "raw_to_h264",
                    "dc:identifier": 'a29f7c4d-9523-4c10-b66f-da314b7d992e',
                    "year": 1995,
                    "title": "the killer cactus' story",
                    "duration": 2 (min)
                    }
            video_metadata (list): [digitise_infos, dublincore_dict]
        """

        complete_logs_document = get_complete_logs_document(makemkvcon_command, log_settings)
        ongoing_conversion_document = get_ongoing_conversion_document(log_settings)

        complete_logs_document_id = self.complete_makemkvcon_logs_collection.insert(complete_logs_document)

        DVD_folder = makemkvcon_command[-1]
        os.mkdir(DVD_folder)

        self.makemkvcon_process = subprocess.Popen(makemkvcon_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                                   universal_newlines=True)
        while True:
            if self.makemkvcon_process.poll() is not None:  # returns None while subprocess is running
                return_code = self.makemkvcon_process.returncode
                self.complete_makemkvcon_logs_collection.find_and_modify(
                    query={"_id": complete_logs_document_id},
                    update={"$set": {"end_date": datetime.now().replace(microsecond=0), "return_code": return_code}}
                )

                if return_code == 0:
                    dublincore_dict = video_metadata[1]
                    dublincore_dict['files_path'] = {'folder': DVD_folder}

                    i = 0
                    duration = 0
                    for file_path in os.listdir(DVD_folder):
                        file_path = os.path.join(DVD_folder, file_path)
                        i += 1
                        dublincore_dict['files_path']['mpeg2_unknown_' + str(i)] = file_path
                        duration += get_mkv_file_duration(file_path)

                    dublincore_dict["dc:format"]["duration"] = duration
                    dublincore_dict['source'] = video_metadata[0]['source']
                    self.videos_metadata_collection.insert(dublincore_dict)
                self.exit_cleanup('SIGTERM')
                break

            stdout_complete_line = self.makemkvcon_process.stdout.readline()
            self.complete_makemkvcon_logs_collection.find_and_modify(
                query={"_id": complete_logs_document_id},
                update={"$push": {"log_data": stdout_complete_line}}
            )

            # Progress bar values for current and total progress
            # PRGV:current,total,max
            if stdout_complete_line.startswith('PRGV:'):
                stdout_complete_line = stdout_complete_line[5:]
                progress_list = stdout_complete_line.split(',')
                progress = round((int(progress_list[1])/int(progress_list[2]))*100)

                ongoing_conversion_document['progress'] = progress
                ongoing_conversion_document["date_data_send"] = datetime.now().timestamp()
                self.publish('com.digitize_app.ongoing_capture', ongoing_conversion_document)
            else:
                print(stdout_complete_line)


def start_supervisor(log_settings, video_metadata, ffmpeg_command=None, src_dst=None, makemkvcon_command=None):
    print("Capture wamp service")
    setproctitle("Capture wamp service")

    if ffmpeg_command:
        runner = ApplicationRunner(url="ws://127.0.0.1:8080/ws", realm="realm1",
                                   extra={'capture_parameters': (ffmpeg_command, log_settings, video_metadata)})
        runner.run(FFmpegWampSupervisor)
    elif makemkvcon_command:
        runner = ApplicationRunner(url="ws://127.0.0.1:8080/ws", realm="realm1",
                                   extra={'capture_parameters': (makemkvcon_command, log_settings, video_metadata)})
        runner.run(MakemkvconSupervisor)
    elif src_dst:
        runner = ApplicationRunner(url="ws://127.0.0.1:8080/ws", realm="realm1",
                                   extra={'capture_parameters': (src_dst, log_settings, video_metadata)})
        runner.run(CopyFileSupervisor)
    else:
        raise ValueError("Both parameters ffmpeg_command and src_dst are None, this shouldn't happen")
    print("capture supervisor has exited")

from backend.shared import FILES_PATHS
from backend.CaptureSupervisor import start_supervisor
from backend.startup_check import startup_check
import setproctitle
from pymongo import MongoClient
from autobahn import wamp
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
import asyncio
import signal
from collections import OrderedDict
from multiprocessing import Process
import subprocess
from pprint import pprint
from backend.shared import wrap_in_future
from time import sleep
import itertools
from datetime import datetime, timedelta
import functools
import os
from uuid import uuid4
import multiprocessing
from copy import deepcopy

# todo make the Gui subscribe to an "error" topic and open a pop-up to display the messages
# todo change the "year" dict key to "dc:identifier"


class Backend(ApplicationSession):
    """
    This class launch captures and is a wamp client
    """

    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)

        #########
        self.default_dvd_to_mpeg2_unknown = OrderedDict()
        self.default_dvd_to_mpeg2_unknown['part1'] = ('nice', '-n', '11', 'makemkvcon', '-r', '--minlength=1',
                                                      '--progress=-same', 'mkv', 'disc:0', 'all')
        self.default_dvd_to_mpeg2_unknown['output_folder'] = ['/this/is/a/path', ]

        self.default_decklink_to_raw = OrderedDict()
        self.default_decklink_to_raw['part1'] = ('nice', '-n', '0', 'ffmpeg', '-y', '-nostdin', '-f', 'decklink')
        self.default_decklink_to_raw['input'] = ['-format_code', 'hp60', '-video_input', 'hdmi', '-i', "Intensity Pro (1)"]
        self.default_decklink_to_raw['recording_duration'] = ['-t', '60']  # in seconds
        self.default_decklink_to_raw['part2'] = ('-acodec', 'copy', '-vcodec', 'copy')
        self.default_decklink_to_raw['frame_rate'] = ['-r', '25']
        self.default_decklink_to_raw['output'] = ['/this/is/a/path/video_file.mkv', ]

        self.default_raw_to_h264_aac = OrderedDict()
        self.default_raw_to_h264_aac['part1'] = ('nice', '-n', '11', 'ffmpeg', '-y', '-nostdin', '-i')
        self.default_raw_to_h264_aac['input'] = ['/this/is/a/path/video_file.mkv', ]
        self.default_raw_to_h264_aac['aspect_ratio'] = ['-aspect', '4:3']
        self.default_raw_to_h264_aac['part2'] = ('-c:v', 'libx264', '-crf', '25', '-preset', 'slow', '-filter:v', 'hqdn3d=3:2:2:3',
                                             '-c:a', 'libfdk_aac', '-vbr', '3')
        self.default_raw_to_h264_aac['output'] = ['/this/is/a/path/video_file.mkv', ]

        self.default_raw_to_ffv1_flac = OrderedDict()
        self.default_raw_to_ffv1_flac['part1'] = ('nice', '-n', '11', 'ffmpeg', '-y', '-nostdin', '-i')
        self.default_raw_to_ffv1_flac['input'] = ['/this/is/a/path/video_file.mkv', ]
        self.default_raw_to_ffv1_flac['part2'] = ('-c:v', 'ffv1', '-level', '3', '-g', '1', '-slicecrc', '1',
                                                  '-c:a', 'flac')
        self.default_raw_to_ffv1_flac['output'] = ['/this/is/a/path/video_file.mkv', ]

        #########
        self.default_log_settings = {
            'source': 'decklink_1',
            'action': 'raw_to_h264',
            'dc:identifier': '0c3579f8-97ec-4737-bbaa-daf8aa9d651f',
            'year': 1965,
            'title': 'the holloway',
            'duration': 1/6,
            }

        #########
        self.raw_videos_path = FILES_PATHS["raw"]
        self.compressed_videos_path = FILES_PATHS["compressed"]
        self.imported_files_path = FILES_PATHS["imported"]

        #########
        self.close_signal = None

        #########
        self.ffmpeg_supervisor_processes = list()
        self.waiting_captures_list = list()

        #########
        asyncio.async(self.waiting_conversions_handler())
        asyncio.async(self.ffmpeg_supervisor_processes_list_updater())

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
        """
        Is called if the wamp router is successfully joined

        Args:
            details(class): SessionDetails
        """

        print("session ready")

        try:
            res = yield from self.register(self)
            print("{0} procedures registered".format(len(res)))
        except Exception as e:
            print("could not register procedure: {0}".format(e))

        yield from self.backend_is_alive_beacon_sender()

    @wrap_in_future  # the signal handler can't call a coroutine directly
    @asyncio.coroutine
    def exit_cleanup(self, close_signal):
        """
        Is called when asyncio catch a 'SIGINT' or 'SIGTERM' signal

        If the signal is 'SIGTERM': the function wait for all ongoing and waiting captures to complete before cancelling
         other running coroutines and then exit
        If the signal is 'SIGINT': the function cancel other running coroutines then exit.

        Note:
            The function doesn't have to cancel ongoing captures on 'SIGINT' because subprocess.Popen does it.

        Args:
            close_signal (str): 'SIGINT' or 'SIGTERM'
        """

        self.close_signal = close_signal

        while True:
            self.ffmpeg_supervisor_processes = [process for process in self.ffmpeg_supervisor_processes
                                                if process.is_alive()]

            len_ffmpeg_supervisor_processes_1 = len(self.ffmpeg_supervisor_processes)
            len_waiting_captures_list_1 = len(self.waiting_captures_list)

            # if there is only one waiting_capture left, it might disappear for a brief time before coming back as a process
            # the sleep ensure that the exit loop don't miss it and terminate the program early.
            yield from asyncio.sleep(6)

            self.ffmpeg_supervisor_processes = [process for process in self.ffmpeg_supervisor_processes
                                                if process.is_alive()]

            len_ffmpeg_supervisor_processes_2 = len(self.ffmpeg_supervisor_processes)
            len_waiting_captures_list_2 = len(self.waiting_captures_list)

            len_ffmpeg_supervisor_processes = max(len_ffmpeg_supervisor_processes_1, len_ffmpeg_supervisor_processes_2)
            len_waiting_captures_list = max(len_waiting_captures_list_1, len_waiting_captures_list_2)

            if len_ffmpeg_supervisor_processes != 0 and len_waiting_captures_list != 0:
                print("waiting for {0} subprocess to terminate"
                      " and on {1} captures to start".format(len_ffmpeg_supervisor_processes, len_waiting_captures_list))

            elif len_ffmpeg_supervisor_processes != 0 and close_signal == 'SIGINT':
                print("cancellation of {0} subprocess".format(len_ffmpeg_supervisor_processes))
            elif len_ffmpeg_supervisor_processes != 0:
                print("waiting for {0} subprocess to complete".format(len_ffmpeg_supervisor_processes))

            elif len_waiting_captures_list != 0 and close_signal == 'SIGINT':
                print("cancellation of {0} queued conversions".format(len_waiting_captures_list))
                break
            elif len_waiting_captures_list != 0:
                print("waiting on {0} conversions to start".format(len_waiting_captures_list))

            elif len_ffmpeg_supervisor_processes == 0 and len_waiting_captures_list == 0:
                print("CLOSING_TIME = True for backend")
                break

        loopy = asyncio.get_event_loop()
        for task in asyncio.Task.all_tasks():
            # this is to avoid the cancellation of this coroutine because this coroutine need to be the last one running
            # to cancel all the others.
            if task is not asyncio.Task.current_task():
                task.cancel()

        # just to make sure that the cancel events are processed
        yield from asyncio.sleep(1)

        loopy.stop()
        print("backend has gracefully exited")

    @asyncio.coroutine
    def ffmpeg_supervisor_processes_list_updater(self):
        """
        Infinite loop that update the list of ffmpeg_supervisor_processes because the 'self.exit_cleanup'
         and 'self.launch_capture' need an up to date list
        """

        while True:
            self.ffmpeg_supervisor_processes = [process for process in self.ffmpeg_supervisor_processes if process.is_alive()]
            yield from asyncio.sleep(5)

    @asyncio.coroutine
    def backend_is_alive_beacon_sender(self):
        """
        Infinite loop that send a beacon to the GUI. If the backend stop sending the beacon for whatever reason the GUI
         disable the launch_capture button.
        """
        while True:
            self.publish('com.digitize_app.backend_is_alive_beacon')
            yield from asyncio.sleep(2)

    @asyncio.coroutine
    def waiting_conversions_handler(self):
        """
        This function get a video_metadata dictionary from the 'waiting_captures_list' and call the launch_capture function with it.

        Just like a RPC call from the GUI would do. If the video can still not get captured, it will get back in the queue
        The function also send the waiting_captures_list for the GUI.
        """
        temp_list = list()

        while True:
            if self.close_signal == 'SIGINT':
                break
            try:
                video_metadata = self.waiting_captures_list.pop(0)
                self.launch_capture(video_metadata)
            except IndexError:
                pass

            # Give time to the waiting_capture to come back in the list if it can't be processed
            yield from asyncio.sleep(5)

            temp_list.clear()
            for capture in self.waiting_captures_list:
                temp_capture_dict = dict()

                temp_capture_dict["dc:title"] = capture[1]["dc:title"][0]
                temp_capture_dict["dcterms:created"] = capture[1]["dcterms:created"]
                temp_capture_dict["dc:identifier"] = capture[1]["dc:identifier"]
                temp_capture_dict["source"] = capture[0]["source"]
                temp_capture_dict["date_data_send"] = datetime.now().timestamp()

                temp_list.append(deepcopy(temp_capture_dict))

            self.publish('com.digitize_app.waiting_captures', temp_list)

    @wamp.register("com.digitize_app.launch_capture")
    def launch_capture(self, video_metadata):
        """
        this function dispatch the incoming captures request to the correct functions and put in a Queue the captures
         request that can't be launched yet.

        Args:
            video_metadata (list): [digitise_infos, dublincore_dict]
        """

        ongoing_captures_names = [pa.name for pa in self.ffmpeg_supervisor_processes]
        print(self.ffmpeg_supervisor_processes)
        print(ongoing_captures_names)
        print(video_metadata)
        video_metadata[1]['dc:identifier'] = str(uuid4())
        video_format = video_metadata[1]["dc:format"]["format"]
        if video_metadata[0]["source"] == "decklink_1":
            if video_format == 'PAL':
                self.start_decklink_to_raw(video_metadata,
                                           input_params=['-format_code', 'pal', '-video_input', 'composite', '-i',
                                                         "Intensity Pro (1)"],
                                           frame_rate=[], decklink_id=1)
            elif video_format == 'NTSC':
                self.start_decklink_to_raw(video_metadata,
                                           input_params=['-format_code', 'ntsc', '-video_input', 'composite', '-i',
                                                         "Intensity Pro (1)"],
                                           frame_rate=[], decklink_id=1)

        elif video_metadata[0]["source"] == "decklink_2":
            if video_format == 'PAL' or video_format == 'SECAM':
                self.start_decklink_to_raw(video_metadata,
                                           input_params=['-format_code', 'hp60', '-video_input', 'hdmi', '-i',
                                                         "Intensity Pro (2)"],
                                           frame_rate=['-r', '25'], decklink_id=2)
            elif video_format == 'NTSC':
                self.start_decklink_to_raw(video_metadata,
                                           input_params=['-format_code', 'hp60', '-video_input', 'hdmi', '-i',
                                                         "Intensity Pro (2)"],
                                           frame_rate=['-r', '30000/1001'], decklink_id=2)

        elif video_metadata[0]["source"] == "DVD":
            if 'dvd_to_mpeg2' not in ongoing_captures_names:
                self.start_dvd_to_mpeg2_unknown(video_metadata)
            else:
                print("nope back in the queue")
                self.waiting_captures_list.append(video_metadata)

        elif video_metadata[0]["source"] == "file":
            if 'file_import' not in ongoing_captures_names:
                self.start_file_import(video_metadata)
            else:
                print("nope back in the queue")
                self.waiting_captures_list.append(video_metadata)

        else:
            raise ValueError("This is not a valid capture request\n" + str(video_metadata))

    def start_decklink_to_raw(self, video_metadata, input_params, frame_rate, decklink_id):
        """
        Gather necessary metadata and launch FFmpeg

        Args:
            video_metadata (list): [digitise_infos, dublincore_dict]
            input_params (list): ['-format_code', 'hp60', '-video_input', 'hdmi', '-i', "Intensity Pro (1)"]
            frame_rate (list): ['-r', '25']
            decklink_id (int): 1 or 2
        """

        duration = video_metadata[1]["dc:format"]["duration"]

        ffmpeg_command = self.default_decklink_to_raw.copy()
        ffmpeg_command['input'] = input_params
        ffmpeg_command['frame_rate'] = frame_rate
        ffmpeg_command['recording_duration'][1] = str(duration)
        ffmpeg_command['output'][0] = FILES_PATHS['raw'] + video_metadata[1]["dc:title"][0] + " -- " +\
                    str(video_metadata[1]["dcterms:created"]) + " -- " + video_metadata[1]['dc:identifier'] + ".nut"

        ffmpeg_command = [value for value in ffmpeg_command.values()]
        ffmpeg_command = list(itertools.chain(*ffmpeg_command))

        log_settings = self.default_log_settings.copy()
        log_settings["source"] = video_metadata[0]["source"]
        log_settings["action"] = "decklink_to_raw"
        log_settings["dc:identifier"] = video_metadata[1]["dc:identifier"]
        log_settings["year"] = video_metadata[1]["dcterms:created"]
        log_settings["title"] = video_metadata[1]["dc:title"]
        log_settings["duration"] = duration
        log_settings["decklink_id"] = decklink_id

        print(ffmpeg_command)
        p = Process(target=start_supervisor, args=(log_settings, video_metadata),
                    kwargs={'ffmpeg_command': ffmpeg_command}, name='decklink_to_raw')
        p.start()
        self.ffmpeg_supervisor_processes.append(p)

    @wamp.register("com.digitize_app.start_raw_to_h264_aac")
    def start_raw_to_h264_aac(self, video_metadata):
        """
        Gather necessary metadata and launch FFmpeg to import raw video files lossly

        Notes:
            h264 is a lossy video codec
            aac is a lossy audio codec

        Args:
            video_metadata (list): [digitise_infos, dublincore_dict]
        """
        duration = video_metadata[1]["dc:format"]["duration"]
        file_path = video_metadata[0]["file_path"]
        aspect_ratio = video_metadata[1]["dc:format"]["aspect_ratio"]

        ffmpeg_command = self.default_raw_to_h264_aac.copy()
        ffmpeg_command['input'][0] = file_path
        ffmpeg_command['aspect_ratio'][1] = aspect_ratio
        ffmpeg_command['output'][0] = FILES_PATHS['compressed'] + video_metadata[1]["dc:title"][0] + " -- " +\
                    str(video_metadata[1]["dcterms:created"]) + " -- " + video_metadata[1]['dc:identifier'] + ".mkv"

        ffmpeg_command = [value for value in ffmpeg_command.values()]
        ffmpeg_command = list(itertools.chain(*ffmpeg_command))

        log_settings = self.default_log_settings.copy()
        log_settings["source"] = video_metadata[0]["source"]
        log_settings["action"] = "raw_to_h264_aac"
        log_settings["dc:identifier"] = video_metadata[1]["dc:identifier"]
        log_settings["year"] = video_metadata[1]["dcterms:created"]
        log_settings["title"] = video_metadata[1]["dc:title"]
        log_settings["duration"] = duration

        p = Process(target=start_supervisor, args=(log_settings, video_metadata),
                    kwargs={'ffmpeg_command': ffmpeg_command}, name='raw_to_h264_aac')
        p.start()
        self.ffmpeg_supervisor_processes.append(p)

    @wamp.register("com.digitize_app.start_raw_to_ffv1_flac")
    def start_raw_to_ffv1_flac(self, video_metadata):
        """
        Gather necessary metadata and launch FFmpeg to import the VHS losslessly

        Notes:
            ffv1 is a lossless video codec
            flac is a lossless audio codec

        Args:
            video_metadata (list): [digitise_infos, dublincore_dict]
        """
        duration = video_metadata[1]["dc:format"]["duration"]
        file_path = video_metadata[0]["file_path"]

        ffmpeg_command = self.default_raw_to_ffv1_flac.copy()
        ffmpeg_command['input'][0] = file_path
        ffmpeg_command['output'][0] = FILES_PATHS['compressed'] + video_metadata[1]["dc:title"][0] + " -- " +\
                    str(video_metadata[1]["dcterms:created"]) + " -- " + video_metadata[1]['dc:identifier'] + ".mkv"

        ffmpeg_command = [value for value in ffmpeg_command.values()]
        ffmpeg_command = list(itertools.chain(*ffmpeg_command))

        log_settings = self.default_log_settings.copy()
        log_settings["source"] = video_metadata[0]["source"]
        log_settings["action"] = "raw_to_ffv1_flac"
        log_settings["dc:identifier"] = video_metadata[1]["dc:identifier"]
        log_settings["year"] = video_metadata[1]["dcterms:created"]
        log_settings["title"] = video_metadata[1]["dc:title"]
        log_settings["duration"] = duration

        p = Process(target=start_supervisor, args=(log_settings, video_metadata),
                    kwargs={'ffmpeg_command': ffmpeg_command}, name='raw_to_ffv1_flac')
        p.start()
        self.ffmpeg_supervisor_processes.append(p)

    def start_dvd_to_mpeg2_unknown(self, video_metadata):
        """
        Gather necessary metadata and launch makemkvcon. This software decrypt and wrap DVDs in nice MKV containers

        Notes:
            mpeg2 is the video codec used in DVDs
            unknown is there because MP2, AC3 and PCM are all valid DVD audio codec

        Args:
            video_metadata (list): [digitise_infos, dublincore_dict]
        """

        makemkvcon_command = self.default_dvd_to_mpeg2_unknown.copy()
        makemkvcon_command['output_folder'] = (FILES_PATHS['DVDs'] + video_metadata[1]["dc:title"][0] + " -- " +
            str(video_metadata[1]["dcterms:created"]) + " -- " + video_metadata[1]['dc:identifier'],)
        makemkvcon_command = [value for value in makemkvcon_command.values()]
        makemkvcon_command = list(itertools.chain(*makemkvcon_command))
        print(makemkvcon_command)

        log_settings = self.default_log_settings.copy()
        log_settings["source"] = video_metadata[0]["source"]
        log_settings["action"] = "dvd_to_mpeg2_unknown"
        log_settings["dc:identifier"] = video_metadata[1]["dc:identifier"]
        log_settings["year"] = video_metadata[1]["dcterms:created"]
        log_settings["title"] = video_metadata[1]["dc:title"]

        p = Process(target=start_supervisor, args=(log_settings, video_metadata),
                    kwargs={'makemkvcon_command': makemkvcon_command}, name='dvd_to_mpeg2_unknown')
        p.start()
        self.ffmpeg_supervisor_processes.append(p)

    def start_file_import(self, video_metadata):
        """
        Gather necessary metadata and launch the copy_file function

        Args:
            video_metadata: [digitise_infos, dublincore_dict]
        """

        src = video_metadata[0]["file_path"]
        dst = FILES_PATHS['imported'] + video_metadata[1]["dc:title"][0] + " -- " + \
              str(video_metadata[1]["dcterms:created"]) + " -- " + video_metadata[1]['dc:identifier'] +\
              "." + src.split(sep=".")[-1]  # to put the same extension back

        log_settings = self.default_log_settings.copy()
        log_settings["source"] = video_metadata[0]["source"]
        log_settings["action"] = "file_import"
        log_settings["dc:identifier"] = video_metadata[1]["dc:identifier"]
        log_settings["year"] = video_metadata[1]["dcterms:created"]
        log_settings["title"] = video_metadata[1]["dc:title"]

        p = Process(target=start_supervisor, args=(log_settings, video_metadata),
                    kwargs={'src_dst': [src, dst]}, name='file_import')
        p.start()
        self.ffmpeg_supervisor_processes.append(p)


def startup_cleanup():
    """
    This function remove more than one week old capture logs.
    """
    db_client = MongoClient("mongodb://localhost:27017/")
    digitize_app = db_client['digitize_app']
    complete_ffmpeg_logs_collection = digitize_app['complete_ffmpeg_logs']
    complete_rsync_logs_collection = digitize_app['complete_rsync_logs']
    complete_makemkvcon_logs_collection = digitize_app['complete_makemkvcon_logs']

    one_week_ago = datetime.now() - timedelta(days=7)
    complete_ffmpeg_logs_collection.remove({"return_code": 0, "end_date": {"$lt": one_week_ago}})
    complete_rsync_logs_collection.remove({"return_code": 0, "end_date": {"$lt": one_week_ago}})
    complete_makemkvcon_logs_collection.remove({"return_code": 0, "end_date": {"$lt": one_week_ago}})


def launch_backend():
    print(os.getpid())
    multiprocessing.set_start_method('spawn')
    setproctitle.setproctitle("digitize_backend")
    # this function check if the directories are writable
    startup_check()
    startup_cleanup()

    crossbar_process = subprocess.Popen(['/usr/local/bin/crossbar', "start", "--cbdir",
                                         FILES_PATHS['home_dir'] + '.config/crossbar/default/'])

    sleep(12)
    runner = ApplicationRunner(url="ws://127.0.0.1:8080/ws", realm="realm1")
    runner.run(Backend)
    crossbar_process.terminate()
    crossbar_process.wait()

if __name__ == "__main__":
    launch_backend()

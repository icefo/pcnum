__author__ = 'adrien'
from backend.constants import FILES_PATHS
from backend.ffmpeg_launcher import run_ffmpeg
from backend.startup_check import startup_check
from pymongo import MongoClient
import setproctitle
from time import sleep
from autobahn import wamp
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
import asyncio
import signal

CLOSING_TIME = False


class Backend(ApplicationSession):

    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)

        self.dvd_to_h264 = [
                    'nice', '-n', '19',
                        'ffmpeg', '-y', '-nostdin',
                            '-i', '/home/mediatheque/video/film_name/title00.mkv', '-map', '0',
                                '-c:s', 'copy',
                                '-c:v', 'libx264', '-crf', '22', '-preset', 'slow',
                                '-c:a', 'libfdk_aac', '-vbr', '4',
                            '/home/adrien/Documents/tm/test2.mkv'
                    ]
        self.decklink_to_raw = [
                    'nice', '-n', '0',
                        "ffmpeg", '-y', '-nostdin',
                            "-f", "decklink", "-i", "'Intensity Pro (1)'@16",
                                '-t', '10',
                                "-acodec", "copy",
                                "-vcodec", "copy",
                                "-r", "25",
                            "output.nut"
                    ]

        self.raw_to_h264 = [
                    'nice', '-n', '19',
                        'ffmpeg', '-y', '-nostdin',
                            '-i', '/home/mediatheque/video/film_name/title00.mkv', "-aspect", "4:3",
                                '-c:v', 'libx264', '-crf', '25', '-preset', 'slow', '-filter:v', 'hqdn3d=3:2:2:3',
                                '-c:a', 'libfdk_aac', '-vbr', '3',
                            '/home/adrien/Documents/tm/test2.mkv'
                    ]

        self.log_settings = {
                    "action": "raw_to_h264",
                    "vuid": 2,
                    "year": 1965,
                    "title": "the holloway",
                    "duration": 1/6,
                    "decklink_id": None
                    }

        # this function check that the the directories are writable
        startup_check()

        self.raw_videos_path = FILES_PATHS["raw"]
        self.compressed_videos_path = FILES_PATHS["compressed"]
        self.imported_files_path = FILES_PATHS["imported"]

    @asyncio.coroutine
    def onJoin(self, details):
        print("session ready")

        try:
            res = yield from self.register(self)
            print("{0} procedures registered".format(len(res)))
        except Exception as e:
            print("could not register procedure: {0}".format(e))

        asyncio.async(self.exit_cleanup())

    @wamp.register("com.digitize_app.launch_capture")
    def launch_capture(self, metadata):
        print(metadata)

    @asyncio.coroutine
    def exit_cleanup(self):
        while True:
            yield from asyncio.sleep(2)
            if CLOSING_TIME is True:
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
        print("gracefully exited")


class GracefulKiller:

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    @staticmethod
    def exit_gracefully(signum, frame):
        global CLOSING_TIME
        CLOSING_TIME = True


if __name__ == "__main__":
    setproctitle.setproctitle("digitize_backend")
    killer = GracefulKiller()
    runner = ApplicationRunner(url="ws://127.0.0.1:8080/ws", realm="realm1")
    runner.run(Backend)
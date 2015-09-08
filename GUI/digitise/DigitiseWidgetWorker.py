__author__ = 'adrien'

from PyQt5.QtCore import QObject, pyqtSignal
from time import sleep
from pymongo import MongoClient
import atexit
import subprocess


class DigitiseWidgetWorker(QObject):

    enable_decklink_1_radio = pyqtSignal([bool])

    enable_decklink_2_radio = pyqtSignal([bool])

    enable_digitize_button = pyqtSignal([bool])

    def __init__(self):
        super().__init__()
        print("DigitiseWidget Worker init")
        self.db_client = MongoClient("mongodb://localhost:27017/")
        metadata_db = self.db_client["metadata"]
        self.videos_metadata = metadata_db["videos_metadata_collection"]
        log_database = self.db_client["log-database"]
        self.waiting_conversions = log_database["waiting_conversions_collection"]
        self.ongoing_conversions = log_database["run_ffmpeg_ongoing_conversions"]

        # This function is called when the DigitiseWidgetWorker class is about to be destroyed
        atexit.register(self.cleanup)

    def cleanup(self):
        self.db_client.close()
        print("DigitiseWidget db connection closed")

    def backend_status_check(self):
        backend_launch_count = 0
        while True:
            enable_decklink_1_checkbox = True
            enable_decklink_2_checkbox = True

            for doc in self.ongoing_conversions.find({}, {"decklink_id": True, "_id": False}):
                try:
                    decklink_id = doc["decklink_id"]
                    print(decklink_id)
                    if decklink_id == 1:
                        enable_decklink_1_checkbox = False
                        self.enable_decklink_1_radio.emit(False)
                    elif decklink_id == 2:
                        enable_decklink_2_checkbox = False
                        self.enable_decklink_2_radio.emit(False)
                except KeyError:
                    pass

            if enable_decklink_1_checkbox:
                self.enable_decklink_1_radio.emit(True)
            if enable_decklink_2_checkbox:
                self.enable_decklink_2_radio.emit(True)

            shell_command = ["ps", "-C", "digitize_backend"]
            try:
                subprocess.check_output(shell_command)
                self.enable_digitize_button.emit(True)
            except subprocess.CalledProcessError:
                self.enable_digitize_button.emit(False)
                # if not backend_launch_count > 0:
                #     print("starting backend")
                #     shell_command = ['python3', '/home/mediatheque/Documents/PycharmProjects/pcnum/backend/main.py']
                #     subprocess.Popen(shell_command, stdout=None)
                #     print("backend starting done")
            sleep(2)

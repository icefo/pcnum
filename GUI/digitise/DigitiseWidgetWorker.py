__author__ = 'adrien'

from PyQt5.QtCore import QObject, pyqtSignal
from time import sleep
from pymongo import MongoClient
import atexit
from pprint import pprint
import subprocess


class DigitiseWidgetWorker(QObject):

    launch_digitise_done = pyqtSignal([str])
    finished = pyqtSignal()

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

        atexit.register(self.cleanup)

    def cleanup(self):
        self.db_client.close()
        print("DigitiseWidget Worker exit")

    def backend_status_check(self):
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

            sleep(2)

    def get_and_lock_new_vuid(self):
        list_of_vuids = [0]
        for post in self.videos_metadata.find({}, {"dc:identifier": True, "_id": False}):
            list_of_vuids.append(post["dc:identifier"])
        new_vuid = max(list_of_vuids) + 1
        # Set this vuid as used so that an other acquisition don't use it and mess up the database
        self.videos_metadata.insert({"dc:identifier": new_vuid}, fsync=True)
        return new_vuid

    def digitise(self, metadata):
        print("bridge digitize()")
        vuid = self.get_and_lock_new_vuid()
        metadata[1]["dc:identifier"] = vuid

        metadata = {"vuid": vuid, "metadata": metadata}
        pprint(metadata)
        self.waiting_conversions.insert(metadata, fsync=True)

        self.launch_digitise_done.emit("Okayyyyy")
        self.finished.emit()

    def check_decklink_button(self):
        pass
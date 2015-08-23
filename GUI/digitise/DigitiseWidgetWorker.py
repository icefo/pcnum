__author__ = 'adrien'

from PyQt5.QtCore import QObject, pyqtSignal
from time import sleep
from pymongo import MongoClient
import atexit
from pprint import pprint


class DigitiseWidgetWorker(QObject):

    launch_digitise_done = pyqtSignal([str])
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        print("DigitiseWidget Worker init")
        self.db_client = MongoClient("mongodb://localhost:27017/")
        metadata_db = self.db_client["metadata"]
        self.videos_metadata = metadata_db["videos_metadata_collection"]
        log_database = self.db_client["log-database"]
        self.waiting_conversions = log_database["waiting_conversions_collection"]

        atexit.register(self.cleanup)

    def cleanup(self):
        self.db_client.close()
        print("DigitiseWidget Worker exit")

    def get_and_lock_new_vuid(self):
        list_of_vuids = [0]
        for post in self.videos_metadata.find({}, {"dc:identifier": True, "_id": False}):
            list_of_vuids.append(post["dc:identifier"])
        new_vuid = max(list_of_vuids) + 1
        # Set this vuid as used so that an other acquisition don't use it and mess up the database
        self.videos_metadata.insert({"dc:identifier": new_vuid})
        return new_vuid

    def digitise(self, metadata):
        print("bridge digitize()")
        vuid = self.get_and_lock_new_vuid()
        metadata[1]["dc:identifier"] = vuid

        metadata = {"vuid": vuid, "metadata": metadata}
        pprint(metadata)
        self.waiting_conversions.insert(metadata)

        self.launch_digitise_done.emit("Okayyyyy")
        self.finished.emit()

    def check_decklink_button(self):
        pass
__author__ = 'adrien'

from PyQt5.QtCore import QObject, pyqtSignal
from time import sleep
from pymongo import MongoClient

class DigitiseWidgetWorker(QObject):

    launch_digitise_done = pyqtSignal([str])
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        print("DigitiseWidget Worker init")
        db_client = MongoClient("mongodb://localhost:27017/")
        db = db_client["videos_metadata"]
        self.videos_metadata = db["videos_metadata"]

    def get_new_vuid(self):
        list_of_vuids = []
        for post in self.videos_metadata.find({}, {"dc:identifier": True, "_id": False}):
            list_of_vuids.append(post["dc:identifier"])
        return max(list_of_vuids) + 1

    def digitise(self, command):
        print("bridge digitize()")
        print(command[0])
        sleep(5)
        self.get_new_vuid()
        print(command[1])
        self.launch_digitise_done.emit("Okayyyyy")
        self.finished.emit()

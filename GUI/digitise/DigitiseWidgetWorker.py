__author__ = 'adrien'

from PyQt5 import QtCore
from time import sleep
from pymongo import MongoClient

class DigitiseWidgetWorker(QtCore.QObject):

    launch_digitise_done = QtCore.pyqtSignal([str])
    finished = QtCore.pyqtSignal()

    def __init__(self, mongo_settings):
        super().__init__()
        print("DigitiseWidget Worker init")
        mongo_client = MongoClient([mongo_settings["server_address"]])
        self.log_database = mongo_client[mongo_settings["database"]]
        self.complete_logs = mongo_settings["complete_logs"]
        self.ongoing_conversions = mongo_settings["ongoing_conversions"]

    def digitise(self, command):
        print("bridge digitize()")
        print(command[0])
        sleep(5)
        print(command[1])
        self.launch_digitise_done.emit("Okayyyyy")
        self.finished.emit()
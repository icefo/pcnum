__author__ = 'adrien'

from PyQt5 import QtCore
from pymongo import MongoClient, ASCENDING
from functools import partial
from time import sleep

class StatusWidgetWorker(QtCore.QObject):

    ongoing_conversions_transmit = QtCore.pyqtSignal([list])

    def __init__(self, mongo_settings):
        """

        :param mongo_settings:
                {
                    "server_address": "mongodb://localhost:27017/",
                    "database": "log-database",
                    "complete_logs": "run_ffmpeg_complete_logs",
                    "ongoing_conversions": "run_ffmpeg_ongoing_conversions"
                }
        :return:
        """
        super().__init__()
        print("StatusWidget Worker init")
        mongo_client = MongoClient([mongo_settings["server_address"]])
        self.log_database = mongo_client[mongo_settings["database"]]
        self.complete_logs = mongo_settings["complete_logs"]
        self.ongoing_conversions = mongo_settings["ongoing_conversions"]

    def status_retriever(self):
        print("mongo bridge()")
        while True:
            ongoing_conversions_list = []
            for doc in self.log_database[self.ongoing_conversions].find({}, {'_id': False}).sort([("start_date", ASCENDING)]):
                ongoing_conversions_list.append(doc)
            self.ongoing_conversions_transmit.emit(ongoing_conversions_list)
            sleep(2)

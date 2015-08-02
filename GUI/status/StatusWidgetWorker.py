__author__ = 'adrien'

from PyQt5 import QtCore
from pymongo import MongoClient
from functools import partial

class StatusWidgetWorker(QtCore.QObject):

    ongoing_conversions_signal = QtCore.pyqtSignal([dict])

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
        # go in an infinit loop here
        # send data using signals every sec
        # use Qthread.sleep
        # color in green the completed ones in the table
        # add a button to flush the completed ones
        print("mongo bridge()")
        for doc in self.log_database[self.ongoing_conversions].find({}):
            print(doc)

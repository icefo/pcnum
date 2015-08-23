__author__ = 'adrien'

from PyQt5.QtCore import QObject, pyqtSignal
from pymongo import MongoClient, ASCENDING
import atexit
from pprint import pprint

from time import sleep


class StatusWidgetWorker(QObject):

    ongoing_conversions_transmit = pyqtSignal([list])

    def __init__(self):
        super().__init__()
        print("StatusWidget Worker init")
        self.db_client = MongoClient("mongodb://localhost:27017/")
        log_database = self.db_client["log-database"]
        # self.complete_logs = log_database["run_ffmpeg_complete_logs"]
        self.waiting_conversions = log_database["waiting_conversions_collection"]
        self.ongoing_conversions = log_database["run_ffmpeg_ongoing_conversions"]

        # self.waiting_conversions.drop()
        # self.ongoing_conversions.drop()

        atexit.register(self.cleanup)

    def cleanup(self):
        self.db_client.close()
        print("StatusWidget Worker exit")

    def conversion_status(self):

        while True:
            print("ongoing_conversions")
            ongoing_conversions_list = []
            for doc in self.ongoing_conversions.find({}, {'_id': False}).sort([("start_date", ASCENDING)]):
                ongoing_conversions_list.append(doc)
            self.ongoing_conversions_transmit.emit(ongoing_conversions_list)
            sleep(2)

            print("waiting_conversions")
            waiting_conversion_list = []
            for doc in self.waiting_conversions.find({}, {'_id': False}):
                waiting_conversion_list.append(doc)
            sleep(2)
            # pprint(waiting_conversion_list)


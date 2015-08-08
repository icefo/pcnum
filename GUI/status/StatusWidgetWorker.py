__author__ = 'adrien'

from PyQt5.QtCore import QObject, pyqtSignal
from pymongo import MongoClient, ASCENDING

from time import sleep

class StatusWidgetWorker(QObject):

    ongoing_conversions_transmit = pyqtSignal([list])

    def __init__(self):
        super().__init__()
        print("StatusWidget Worker init")
        mongo_client = MongoClient("mongodb://localhost:27017/")
        log_database = mongo_client["log-database"]
        self.complete_logs = log_database["run_ffmpeg_complete_logs"]
        self.ongoing_conversions = log_database["run_ffmpeg_ongoing_conversions"]

    def status_retriever(self):
        print("mongo bridge()")
        while True:
            ongoing_conversions_list = []
            for doc in self.ongoing_conversions.find({}, {'_id': False}).sort([("start_date", ASCENDING)]):
                ongoing_conversions_list.append(doc)
            self.ongoing_conversions_transmit.emit(ongoing_conversions_list)
            sleep(2)

    def blup(self):
        print("aleluyaaaaaaaaaaaaaaaaaaaaaaa")

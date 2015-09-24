__author__ = 'adrien'

from PyQt5.QtCore import QObject, pyqtSignal
from pymongo import MongoClient, ASCENDING
import atexit
from pprint import pprint

from time import sleep


class StatusWidgetWorker(QObject):

    ongoing_conversions_collection_transmit = pyqtSignal([list])
    waiting_conversions_collection_transmit = pyqtSignal([list])

    def __init__(self):
        super().__init__()
        print("StatusWidget Worker init")

        #########
        self.db_client = MongoClient("mongodb://localhost:27017/")
        ffmpeg_db = self.db_client["ffmpeg_conversions"]
        self.waiting_conversions_collection = ffmpeg_db["waiting_conversions"]
        self.ongoing_conversions_collection = ffmpeg_db["ongoing_conversions"]

        #########
        atexit.register(self.cleanup)

    def cleanup(self):
        self.db_client.close()
        print("StatusWidget Worker's db connection closed")

    def conversion_status(self):

        while True:
            ongoing_conversions_list = []
            for doc in self.ongoing_conversions_collection.find({}, {'_id': False}).sort([("start_date", ASCENDING)]):
                ongoing_conversions_list.append(doc)
            self.ongoing_conversions_collection_transmit.emit(ongoing_conversions_list)

            waiting_conversion_list = []
            for doc in self.waiting_conversions_collection.find({}, {'_id': False}):
                # elements in the ongoing_conversions_collection are in the waiting_conversions_collection too
                # and I don't want to confuse the user, so I hide them
                print("waiting conversion")
                pprint(doc)
                if not self.ongoing_conversions_collection.find_one({"vuid": doc["metadata"][1]["dc:identifier"]}):
                    waiting_conversion_list.append(doc)
            self.waiting_conversions_collection_transmit.emit(waiting_conversion_list)

            sleep(3)

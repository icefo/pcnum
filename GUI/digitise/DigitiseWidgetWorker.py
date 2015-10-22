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

        #########
        self.db_client = MongoClient("mongodb://localhost:27017/")
        metadata_db = self.db_client["metadata"]
        self.videos_metadata = metadata_db["videos_metadata"]
        ffmpeg_db = self.db_client["ffmpeg_conversions"]
        self.ongoing_conversions_collection = ffmpeg_db["ongoing_conversions"]

        #########
        atexit.register(self.cleanup)

    def cleanup(self):
        """
        This function is called when the DigitiseWidgetWorker class is about to be destroyed

        :return:
        """
        self.db_client.close()
        print("DigitiseWidget Worker's db connection closed")

    def backend_status_check(self):
        """
        This function check if the backend is alive, if not the "Numériser" button is disabled

        This function also check if the decklink 1 and 2 cards are digitising something atm and disable their button if
        necessary
        :return:
        """
        while True:
            enable_decklink_1_checkbox = True
            enable_decklink_2_checkbox = True

            for doc in self.ongoing_conversions_collection.find({}, {"decklink_id": True, "_id": False}):
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


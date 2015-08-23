__author__ = 'adrien'

from PyQt5.QtCore import QObject, pyqtSignal
from pymongo import MongoClient, ASCENDING
import atexit


class SearchWidgetWorker(QObject):

    search_done = pyqtSignal([list])
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        print("SearchWidget Worker init")
        self.db_client = MongoClient('mongodb://localhost:27017/')
        db = self.db_client['metadata']
        self.videos_metadata_collection = db['videos_metadata_collection']
        atexit.register(self.cleanup)

    def cleanup(self):
        self.db_client.close()
        print("SearchWidget Worker exit")

    def search(self, command):
        print("bridge search()")

        mongo_query = {"$and": []}
        for dc_item, dict_query in command.items():
            print(dc_item, dict_query)
            for query_type, query in dict_query.items():
                if query_type == "equal":
                    for query_item in query:
                        if isinstance(query_item, str):
                            mongo_query["$and"].append({dc_item: {"$regex": "^" + query_item + "$", "$options": "i"}})
                        else:
                            mongo_query["$and"].append({dc_item: query_item})
                elif query_type == "contain":
                    for query_item in query:
                        mongo_query["$and"].append({dc_item: {"$regex": ".*" + query_item + ".*", "$options": "i"}})
                elif query_type == "greater":
                    mongo_query["$and"].append({dc_item: {"$gt": query[0]}})
                elif query_type == "inferior":
                    mongo_query["$and"].append({dc_item: {"$lt": query[0]}})

        print(mongo_query)
        result_list = []
        for post in self.videos_metadata_collection.find(mongo_query, {'_id': False}).sort([("dc:format.duration", ASCENDING)]):
            result_list.append(post)
            print(post)

        self.search_done.emit(result_list)
        self.finished.emit()

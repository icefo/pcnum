__author__ = 'adrien'

from PyQt5 import QtCore
from pymongo import MongoClient, ASCENDING


class SearchWidgetWorker(QtCore.QObject):

    search_done = QtCore.pyqtSignal([list])
    finished = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        print("SearchWidget Worker init")

    def search(self, command):
        print("bridge search()")

        db_client = MongoClient('mongodb://localhost:27017/')
        db = db_client['test-database']
        videos_metadata = db['videos_metadata']

        mongo_query = {"$and": []}
        for dc_item, dict_query in command.items():
            print(dc_item, dict_query)
            for query_type, query in dict_query.items():
                if query_type == "equal":
                    for query_item in query:
                        if isinstance(query_item, str):
                            mongo_query["$and"].append({dc_item: {"$regex": query_item, "$options": "i"}})
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
        for post in videos_metadata.find(mongo_query, {'_id': False}).sort([("dc:format.duration", ASCENDING)]):
            result_list.append(post)
            print(post)

        db_client.close()

        self.search_done.emit(result_list)
        self.finished.emit()

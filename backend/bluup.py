from pymongo import MongoClient
from pprint import pprint
from time import sleep
import os

# db_client = MongoClient("mongodb://localhost:27017/")
# print(db_client.drop_database("log-database"))
# ffmpeg_db = db_client["ffmpeg_conversions"]
# metadata_db = db_client["metadata"]
#
# videos_metadata_collection = metadata_db["videos_metadata"]
# waiting_conversions_collection = ffmpeg_db["waiting_conversions"]
# ongoing_conversions_collection = ffmpeg_db["ongoing_conversions"]
# complete_logs = ffmpeg_db["complete_conversion_logs"]


# while True:
#     for doc in complete_logs.find({}):
#         print("\ncomplete logs")
#         #pprint(doc)
#
#     for doc in waiting_conversions_collection.find({}):
#         print("\nwaiting conversions")
#         pprint(doc)
#
#     for doc in videos_metadata_collection.find({}):
#         print("\nvideos_metadata")
#         pprint(doc)
#
#     for doc in ongoing_conversions_collection.find({}):
#         print("\nongoing_conversions")
#         pprint(doc)
#     sleep(5)

# complete_logs.drop()
# waiting_conversions_collection.drop()
# ongoing_conversions_collection.drop()
# videos_metadata_collection.drop()

# os.remove("/media/storage/raw/j'ai plus d'idées -- 7.nut")

from backend.constants import FILES_PATHS

for x in FILES_PATHS.values():
    print(x)
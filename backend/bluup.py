from pymongo import MongoClient
from pprint import pprint

db_client = MongoClient("mongodb://localhost:27017/")
log_database = db_client["log-database"]
metadata_db = db_client["metadata"]

videos_metadata_collection = metadata_db["videos_metadata_collection"]
waiting_conversions_collection = log_database["waiting_conversions_collection"]
ongoing_conversions_collection = log_database["run_ffmpeg_ongoing_conversions"]
complete_logs = log_database["run_ffmpeg_complete_logs"]

complete_logs.drop()
waiting_conversions_collection.drop()
ongoing_conversions_collection.drop()
videos_metadata_collection.drop()


for doc in complete_logs.find({}):
    pprint(doc)

for doc in waiting_conversions_collection.find({}):
    pprint(doc)

for doc in videos_metadata_collection.find({'$and': [{'dc:contributor': {'$regex': '^claire sougner$', '$options': 'i'}}]}):
    pprint(doc)


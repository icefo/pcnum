from pymongo import MongoClient

db_client = MongoClient("mongodb://localhost:27017/")
digitize_app = db_client['digitize_app']
videos_metadata_collection = digitize_app['videos_metadata']
complete_rsync_logs_collection = digitize_app['complete_rsync_logs']

for log in complete_rsync_logs_collection.find():
    print(log)
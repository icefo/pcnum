from pymongo import MongoClient
from pprint import pprint
from multiprocessing import Process

from time import sleep

db_client = MongoClient("mongodb://localhost:27017/")
log_database = db_client["log-database"]
metadata_db = db_client["metadata"]

videos_metadata_collection = metadata_db["videos_metadata_collection"]
waiting_conversions_collection = log_database["waiting_conversions_collection"]
ongoing_conversions_collection = log_database["run_ffmpeg_ongoing_conversions"]
complete_logs = log_database["run_ffmpeg_complete_logs"]

for doc in complete_logs.find({}):
    print("\ncomplete logs")
    pprint(doc)

for doc in waiting_conversions_collection.find({}):
    print("\nwaiting conversions")
    pprint(doc)

for doc in videos_metadata_collection.find({}):
    print("\nvideos_metadata")
    pprint(doc)

for doc in ongoing_conversions_collection.find({}):
    print("\nongoing_conversions")
    pprint(doc)

# complete_logs.drop()
# waiting_conversions_collection.drop()
# ongoing_conversions_collection.drop()
# videos_metadata_collection.drop()


def long_blocking_operation(param):
    sleep(2)
    print("first nap done")
    sleep(2)
    print("returning")
    return True

p = Process(target=long_blocking_operation, args=("hehehe",))
p.start()
print("joining")
p.join()
print("joined")
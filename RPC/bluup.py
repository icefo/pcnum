__author__ = 'adrien'
from pymongo import MongoClient
from time import sleep

mongo_client = MongoClient("mongodb://localhost:27017/")
log_db = mongo_client["log-database"]
ffmpeg_complete_logs = log_db["run_ffmpeg_complete_logs"]
#ffmpeg_complete_logs.drop()

# for doc in ffmpeg_complete_logs.find({}):
#     for elem in doc:
#         if elem == "log_data":
#             for blup in doc[elem]:
#                 # print(blup)
#                 pass
#         else:
#             print(elem, doc[elem])

ongoing_conversions = log_db["run_ffmpeg_ongoing_conversions"]
ongoing_conversions.drop()

while True:
    try:
        for doc in ongoing_conversions.find({}):
            print(doc)
            sleep(1)
    except KeyboardInterrupt:
        break

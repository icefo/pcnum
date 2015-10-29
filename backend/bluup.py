from pymongo import MongoClient
from pprint import pprint
from backend.shared import PYPY_PATH
import shlex

db_client = MongoClient("mongodb://localhost:27017/")
digitize_app = db_client['digitize_app']
videos_metadata_collection = digitize_app['videos_metadata']
videos_metadata_collection.drop()
complete_ffmpeg_logs_collection = digitize_app['complete_ffmpeg_logs']

for doc in complete_ffmpeg_logs_collection.find({}):
    pprint(doc)

complete_ffmpeg_logs_collection.drop()

print(shlex.quote(" ".join([PYPY_PATH + 'bin/crossbar', "start", "--cbdir",
                            PYPY_PATH + 'config/crossbar/default/.crossbar'])))
#from pymongo import MongoClient
from pprint import pprint
from time import sleep
import os
import subprocess
import signal

# db_client = MongoClient("mongodb://localhost:27017/")
# ffmpeg_db = db_client["ffmpeg_conversions"]
# metadata_db = db_client["metadata"]
#
# videos_metadata_collection = metadata_db["videos_metadata"]
# waiting_conversions_collection = ffmpeg_db["waiting_conversions"]
# ongoing_conversions_collection = ffmpeg_db["ongoing_conversions"]
# complete_logs = ffmpeg_db["complete_conversion_logs"]



# for doc in complete_logs.find({}):
#     print("\ncomplete logs")
#     pprint(doc)


#complete_logs.drop()
# waiting_conversions_collection.drop()
# ongoing_conversions_collection.drop()
# videos_metadata_collection.drop()

# os.remove("/media/storage/raw/j'ai plus d'idées -- 7.nut")

CLOSING_TIME = False


class GracefulKiller:

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    @staticmethod
    def exit_gracefully(signum, frame):
        print("CLOSING TIME for FFmpeg supervisor")
        global CLOSING_TIME
        CLOSING_TIME = True

GracefulKiller()

ffmpeg_command = ['nice', '-n', '19', 'ffmpeg', '-y', '-nostdin', '-i', '/home/adrien/Vidéos/piere.webm', '-map', '0', '-c:s', 'copy', '-c:v', 'libx264', '-crf', '22', '-preset', 'slow', '-c:a', 'libfdk_aac', '-vbr', '4', '/home/adrien/Documents/tm/compressed/cvbvc -- 2158 -- 3d6a628d-d41d-4d58-afca-b58f2686557a.mkv']

ffmpeg_process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                               universal_newlines=True)
while True:
    if ffmpeg_process.poll() is not None:  # returns None while subprocess is running
        print(ffmpeg_process.returncode)
        break
    line = ffmpeg_process.stdout.readline()
    print(line)

__author__ = 'adrien'
from multiprocessing import Process
from backend.command_launcher import run_ffmpeg
from pymongo import MongoClient
from time import sleep
from subprocess import Popen, PIPE
from pprint import pprint

# todo store converted video with vuid -- video_name; same for raw videos
# todo copy all audio track + subtitles

# The last value give the final size of the file (audio + video + mux)
# {'time': '00:00:10.00', 'bitrate': '2771.4kbits/s', 'fps': '8.0', 'q': '-1.0', 'Lsize': '3385kB', 'frame': '250'}
# use Variable bitrate for the conversion!!!


def get_mkv_file_duration(file):
    command = [  'ffprobe',
                 '-v',
                 'error',
                 '-select_streams',
                 'v:0',
                 '-show_entries',
                 'format=duration',
                 '-of',
                 'default=noprint_wrappers=1:nokey=1',
                 file
               ]

    process = Popen(command, stdout=PIPE)
    (output, err) = process.communicate()
    output = float(output)
    print(output)
    return output


class Backend(object):
    def __init__(self):

        self.dvd_to_h264 = [
                    'nice', '-n', '19',
                        'ffmpeg',
                            '-i', '/home/mediatheque/video/film_name/title00.mkv', '-map', '0',
                                '-c:s', 'copy',
                                '-c:v', 'libx264', '-crf', '20', '-preset', 'medium',
                                '-c:a', 'libfdk_aac', '-vbr', '4',
                            '/home/adrien/Documents/tm/test2.mkv'
                    ]

        self.raw_to_h264 = [
                    'nice', '-n', '19',
                        'ffmpeg',
                            '-i', '/home/mediatheque/video/film_name/title00.mkv',
                                '-t', '10',
                                '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-filter:v', 'hqdn3d=3:2:2:3',
                                '-c:a', 'libfdk_aac', '-vb:a', '192k',
                            '/home/adrien/Documents/tm/test2.mkv'
                    ]

        self.log_settings = {
                    "action": "raw_to_h264",
                    "vuid": 2,
                    "year": 1965,
                    "title": "the holloway",
                    "duration": 1/6
                    }

        self.raw_videos_path = None
        self.compressed_videos_path = "/home/adrien/Documents/tm/"

        db_client = MongoClient("mongodb://localhost:27017/")
        log_database = db_client["log-database"]
        self.waiting_conversions = log_database["waiting_conversions"]

    def start_dvd_conversion(self, doc):
        filename = doc["metadata"][0]["filename"]
        duration = get_mkv_file_duration(filename)
        self.waiting_conversions.find_and_modify(query={"_id": doc["_id"]},
                                        update={"$set": {"metadata.1.format.duration": duration}})

        temp_dvd_to_h264 = self.dvd_to_h264.copy()
        temp_dvd_to_h264[5] = filename
        temp_dvd_to_h264[-1] = self.compressed_videos_path + doc["metadata"][1]["dc:title"][0] + " -- " +\
                               str(doc["metadata"][1]["dcterms:created"]) + ".mkv"

        temp_log_settings = self.log_settings.copy()
        temp_log_settings["action"] = "dvd_to_h264"
        temp_log_settings["vuid"] = doc["metadata"][1]["dc:identifier"]
        temp_log_settings["year"] = doc["metadata"][1]["dcterms:created"]
        temp_log_settings["title"] = doc["metadata"][1]["dc:title"]
        temp_log_settings["duration"] = duration

        p = Process(target=run_ffmpeg, args=(temp_dvd_to_h264, temp_log_settings))
        p.start()

    def start_watch(self):
        print("Night gathers, and now my watch begins. It shall not end until my death...")
        currently_processing = []
        while True:
            waiting_conversions_list = []

            for doc in self.waiting_conversions.find({}):
                if doc["metadata"][0]["source"] == "DVD" and doc["_id"] not in currently_processing:
                    pprint(doc)
                    currently_processing.append(doc["_id"])
                    self.start_dvd_conversion(doc)
                elif doc["metadata"][0]["source"] == "file" and doc["_id"] not in currently_processing:
                    pass
                else:
                    print("else called")

            sleep(5)


if __name__ == '__main__':
    # infinite loop here
    # check for waiting_conversions table
    # start in priority decklink acquisition jobs, when they are done start the jobs that need the raw decklink files
    # even if this will be checked in the gui check if the decklink card is not already in use
    # use first startup check every time
    backend = Backend()
    backend.start_watch()





print("knooooooooooookonk")
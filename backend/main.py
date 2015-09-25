__author__ = 'adrien'
from multiprocessing import Process
from backend.ffmpeg_launcher import run_ffmpeg
from pymongo import MongoClient
from time import sleep
import subprocess
from pprint import pprint
import atexit
from datetime import datetime, timedelta
import os
import setproctitle

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

    output = subprocess.check_output(command)
    output = float(output)
    print(output)
    return output


def copy_file(src, dst, doc):
    vuid = doc["metadata"][1]["dc:identifier"]

    db_client = MongoClient("mongodb://localhost:27017/")
    ffmpeg_db = db_client["ffmpeg_conversions"]
    ongoing_conversions_collection = ffmpeg_db["ongoing_conversions"]

    ongoing_conversions_document = {"vuid": vuid,
                                "action": "file_import",
                                "year": doc["metadata"][1]["dcterms:created"],
                                "title": doc["metadata"][1]["dc:title"],
                                "start_date": datetime.now(),
                                "pid": os.getpid(),
                                "return_code": None,
                                "end_date": None,
                                "converted_file_path": None,
                                "log_data": {}
                                }

    ongoing_conversions_document_id = ongoing_conversions_collection.insert(ongoing_conversions_document)
    print("copy function")
    shell_command = ["ionice", "-c", "2", "-n", "7", "cp", "-f", src, dst]
    process = subprocess.Popen(shell_command, stdout=None, stderr=None, universal_newlines=True)
    while True:
        if process.poll() is not None:  # returns None while subprocess is running
            return_code = process.returncode

            ongoing_conversions_collection.find_and_modify(query={"_id": ongoing_conversions_document_id},
                                                update={"$set": {"end_date": datetime.now(),
                                                                 "return_code": return_code,
                                                                 "converted_file_path": dst}}, fsync=True)
            break
        sleep(1)

    db_client.close()


class Backend(object):
    def __init__(self):

        self.dvd_to_h264 = [
                    'nice', '-n', '19',
                        'ffmpeg', '-y', '-nostdin',
                            '-i', '/home/mediatheque/video/film_name/title00.mkv', '-map', '0',
                                '-c:s', 'copy',
                                '-c:v', 'libx264', '-crf', '22', '-preset', 'slow',
                                '-c:a', 'libfdk_aac', '-vbr', '4',
                            '/home/adrien/Documents/tm/test2.mkv'
                    ]
        self.decklink_to_raw = [
                    'nice', '-n', '0',
                        "ffmpeg", '-y', '-nostdin',
                            "-f", "decklink", "-i", "'Intensity Pro (1)'@16",
                                '-t', '10',
                                "-acodec", "copy",
                                "-vcodec", "copy",
                                "-r", "25",
                            "output.nut"
                    ]

        self.raw_to_h264 = [
                    'nice', '-n', '19',
                        'ffmpeg', '-y', '-nostdin',
                            '-i', '/home/mediatheque/video/film_name/title00.mkv', "-aspect", "4:3",
                                '-c:v', 'libx264', '-crf', '25', '-preset', 'slow', '-filter:v', 'hqdn3d=3:2:2:3',
                                '-c:a', 'libfdk_aac', '-vbr', '3',
                            '/home/adrien/Documents/tm/test2.mkv'
                    ]

        self.log_settings = {
                    "action": "raw_to_h264",
                    "vuid": 2,
                    "year": 1965,
                    "title": "the holloway",
                    "duration": 1/6,
                    "decklink_id": None
                    }

        self.raw_videos_path = "/media/storage/raw/"
        self.compressed_videos_path = "/media/storage/compressed/"
        self.imported_files_path = "/media/storage/imported/"

        self.db_client = MongoClient("mongodb://localhost:27017/")
        ffmpeg_db = self.db_client["ffmpeg_conversions"]
        self.waiting_conversions_collection = ffmpeg_db["waiting_conversions"]
        self.ongoing_conversions_collection = ffmpeg_db["ongoing_conversions"]
        self.complete_conversion_logs_collection = ffmpeg_db["complete_conversion_logs"]
        metadata_db = self.db_client["metadata"]
        self.videos_metadata_collection = metadata_db["videos_metadata"]

        self.startup_cleanup()
        atexit.register(self.exit_cleanup)

    def startup_cleanup(self):
        """
        the function remove unfinished decklink acquisitions at startup. This avoid launching an unwanted conversion
        when recovering from an power outage. This function also remove more than one week old logs.
        """
        for doc in self.waiting_conversions_collection.find({}):
            if doc["metadata"][0]["source"] == "decklink_1" or "decklink_2":
                try:
                    raw_file_path = self.raw_videos_path + doc["metadata"][1]["dc:title"][0] + " -- " +\
                                str(doc["metadata"][1]["dc:identifier"]) + ".nut"
                    os.remove(raw_file_path)
                except (KeyError, FileNotFoundError):
                    pass
                self.waiting_conversions_collection.remove({"metadata.1.dc:identifier": doc["_id"]}, fsync=True)
        self.ongoing_conversions_collection.drop()

        one_week_ago = datetime.now() - timedelta(days=7)
        self.complete_conversion_logs_collection.remove({"return_code": 0, "end_date": {"$lt": one_week_ago}})

    def exit_cleanup(self):
        self.db_client.close()
        print("Backend's db connection closed")

    def start_dvd_conversion(self, doc):
        filename = doc["metadata"][0]["filename"]
        duration = get_mkv_file_duration(filename)
        self.waiting_conversions_collection.find_and_modify(query={"_id": doc["_id"]},
                                                 update={"$set": {"metadata.1.dc:format.duration": duration}}, fsync=True)

        temp_dvd_to_h264 = self.dvd_to_h264.copy()
        temp_dvd_to_h264[7] = filename
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

    def start_decklink_to_raw(self, doc, decklink_card, decklink_id):
        duration = doc["metadata"][1]["dc:format"]["duration"]

        temp_decklink_to_raw = self.decklink_to_raw.copy()
        temp_decklink_to_raw[9] = decklink_card
        temp_decklink_to_raw[11] = str(duration)
        temp_decklink_to_raw[-1] = self.raw_videos_path + doc["metadata"][1]["dc:title"][0] + " -- " +\
                                   str(doc["metadata"][1]["dc:identifier"]) + ".nut"

        temp_log_settings = self.log_settings.copy()
        temp_log_settings["action"] = "decklink_to_raw"
        temp_log_settings["vuid"] = doc["metadata"][1]["dc:identifier"]
        temp_log_settings["year"] = doc["metadata"][1]["dcterms:created"]
        temp_log_settings["title"] = doc["metadata"][1]["dc:title"]
        temp_log_settings["duration"] = duration
        temp_log_settings["decklink_id"] = decklink_id

        p = Process(target=run_ffmpeg, args=(temp_decklink_to_raw, temp_log_settings))
        p.start()

    def start_raw_to_h264(self, doc):
        duration = doc["metadata"][1]["dc:format"]["duration"]
        filename = doc["metadata"][0]["filename"]
        size_ratio = doc["metadata"][1]["dc:format"]["size_ratio"]

        temp_raw_to_h264 = self.raw_to_h264.copy()
        temp_raw_to_h264[7] = filename
        temp_raw_to_h264[9] = size_ratio
        temp_raw_to_h264[-1] = self.compressed_videos_path + doc["metadata"][1]["dc:title"][0] + " -- " +\
                               str(doc["metadata"][1]["dc:identifier"]) + ".mkv"

        temp_log_settings = self.log_settings.copy()
        temp_log_settings["action"] = "raw_to_h264"
        temp_log_settings["vuid"] = doc["metadata"][1]["dc:identifier"]
        temp_log_settings["year"] = doc["metadata"][1]["dcterms:created"]
        temp_log_settings["title"] = doc["metadata"][1]["dc:title"]
        temp_log_settings["duration"] = duration

        p = Process(target=run_ffmpeg, args=(temp_raw_to_h264, temp_log_settings))
        p.start()

    def start_file_import(self, doc):
        print("start file import")
        filename = doc["metadata"][0]["filename"]
        dest_path = self.imported_files_path + doc["metadata"][1]["dc:title"][0] + " -- " + \
                    str(doc["metadata"][1]["dc:identifier"]) + "." + filename.split(sep=".")[-1]

        p = Process(target=copy_file, args=(filename, dest_path, doc))
        p.start()

    def start_watch(self):
        print("Night gathers, and now my watch begins. It shall not end until my death...")
        currently_processing = [[], [], []]  # [decklink], [other_conversions], [file_import]
        while True:
            print(currently_processing)
            for doc in self.waiting_conversions_collection.find({}):
                vuid = doc["metadata"][1]["dc:identifier"]

                if doc["metadata"][0]["source"] == "decklink_1" and vuid not in currently_processing[0]:
                    currently_processing[0].append(vuid)
                    self.start_decklink_to_raw(doc, "Intensity Pro (1)@16", 1)

                elif doc["metadata"][0]["source"] == "decklink_2" and vuid not in currently_processing[0]:
                    currently_processing[0].append(vuid)
                    self.start_decklink_to_raw(doc, "Intensity Pro (2)@16", 2)

                elif doc["metadata"][0]["source"] == "DVD" and len(currently_processing[1]) == 0:
                    currently_processing[1].append(vuid)
                    self.start_dvd_conversion(doc)

                elif doc["metadata"][0]["source"] == "decklink_raw" and len(currently_processing[1]) == 0:
                    currently_processing[1].append(vuid)
                    self.start_raw_to_h264(doc)

                elif doc["metadata"][0]["source"] == "file" and vuid not in currently_processing[2]:
                    currently_processing[2].append(vuid)
                    self.start_file_import(doc)

                else:
                    print("else called")

            for doc in self.ongoing_conversions_collection.find({}):
                vuid = doc["vuid"]
                converted_file_path = doc["converted_file_path"]
                video_metadata = []
                for metadata in self.waiting_conversions_collection.find(query={"metadata.1.dc:identifier": vuid}):
                    video_metadata.append(metadata)

                if doc["action"] == "decklink_to_raw" and doc["return_code"] == 0:
                    self.waiting_conversions_collection.find_and_modify(
                        query={"metadata.1.dc:identifier": vuid},
                        update={"$set": {"metadata.0.filename": converted_file_path,
                                         "metadata.0.source": "decklink_raw"}}, fsync=True)

                    self.ongoing_conversions_collection.remove(spec_or_id={"_id": doc["_id"]}, fsync=True)
                    currently_processing[0].remove(vuid)

                elif doc["action"] == "dvd_to_h264" and doc["return_code"] == 0:

                    dublin_dict = video_metadata[0]["metadata"][1]
                    dublin_dict["files_path"] = {"h264": converted_file_path}
                    dublin_dict["source"] = "DVD"

                    self.videos_metadata_collection.update(spec={"dc:identifier": vuid}, document={"$set": dublin_dict}, upsert=False, fsync=True)
                    self.waiting_conversions_collection.remove(spec_or_id={"metadata.1.dc:identifier": vuid}, fsync=True)
                    self.ongoing_conversions_collection.remove(spec_or_id={"vuid": vuid}, fsync=True)
                    currently_processing[1].remove(vuid)

                elif doc["action"] == "raw_to_h264" and doc["return_code"] == 0:
                    pprint(video_metadata)

                    dublin_dict = video_metadata[0]["metadata"][1]
                    dublin_dict["files_path"] = {"h264": converted_file_path}
                    dublin_dict["source"] = "Decklink"
                    self.videos_metadata_collection.update(spec={"dc:identifier": vuid}, document={"$set": dublin_dict}, upsert=False, fsync=True)
                    self.waiting_conversions_collection.remove(spec_or_id={"metadata.1.dc:identifier": vuid}, fsync=True)
                    self.ongoing_conversions_collection.remove(spec_or_id={"vuid": vuid}, fsync=True)
                    currently_processing[1].remove(vuid)
                    raw_file_path = video_metadata[0]["metadata"][0]["filename"]
                    os.remove(raw_file_path)

                elif doc["action"] == "file_import" and doc["return_code"] == 0:
                    pprint(video_metadata)

                    dublin_dict = video_metadata[0]["metadata"][1]
                    dublin_dict["files_path"] = {"unknown": converted_file_path}
                    dublin_dict["source"] = "File import"
                    dublin_dict["dc:format"]["format"] = "unknown"
                    dublin_dict["dc:format"]["size_ratio"] = "unknown"
                    print("database part")
                    self.videos_metadata_collection.update(spec={"dc:identifier": vuid}, document={"$set": dublin_dict}, upsert=False, fsync=True)
                    self.waiting_conversions_collection.remove(spec_or_id={"metadata.1.dc:identifier": vuid}, fsync=True)
                    self.ongoing_conversions_collection.remove(spec_or_id={"vuid": vuid}, fsync=True)
                    print("removing vuid")
                    currently_processing[2].remove(vuid)
                    print("done")

            sleep(5)


if __name__ == '__main__':
    # infinite loop here
    # check for waiting_conversions_collection
    # start in priority decklink acquisition jobs, when they are done start the jobs that need the raw decklink files
    # even if this will be checked in the gui check if the decklink card is not already in use
    # use first startup check every time
    setproctitle.setproctitle("digitize_backend")
    backend = Backend()
    try:
        backend.start_watch()
    except KeyboardInterrupt:
        pass





print("knooooooooooookonk")

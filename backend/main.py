__author__ = 'adrien'
from multiprocessing import Process
from backend.command_launcher import run_ffmpeg
from pymongo import MongoClient
from time import sleep
from subprocess import Popen, PIPE
from pprint import pprint

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
        self.decklink_to_raw = [
                    'nice', '-n', '0',
                        "ffmpeg",
                            "-f", "decklink", "-i", "'Intensity Pro (1)'@16",
                                '-t', '10',
                                "-acodec", "copy",
                                "-vcodec", "copy",
                                "-r", "25",
                            "output.nut"
                    ]

        self.raw_to_h264 = [
                    'nice', '-n', '19',
                        'ffmpeg',
                            '-i', '/home/mediatheque/video/film_name/title00.mkv', "-aspect", "4:3",
                                '-c:v', 'libx264', '-crf', '23', '-preset', 'medium', '-filter:v', 'hqdn3d=3:2:2:3',
                                '-c:a', 'libfdk_aac', '-vbr', '3',
                            '/home/adrien/Documents/tm/test2.mkv'
                    ]

        self.log_settings = {
                    "action": "raw_to_h264",
                    "vuid": 2,
                    "year": 1965,
                    "title": "the holloway",
                    "duration": 1/6
                    }

        self.raw_videos_path = "/media/storage/raw/"
        self.compressed_videos_path = "/media/storage/compressed/"

        db_client = MongoClient("mongodb://localhost:27017/")
        log_database = db_client["log-database"]
        self.waiting_conversions_collection = log_database["waiting_conversions_collection"]
        self.ongoing_conversions_collection = log_database["run_ffmpeg_ongoing_conversions"]

        metadata_db = db_client["metadata"]
        self.videos_metadata_collection = metadata_db["videos_metadata_collection"]

    def start_dvd_conversion(self, doc):
        filename = doc["metadata"][0]["filename"]
        duration = get_mkv_file_duration(filename)
        self.waiting_conversions_collection.find_and_modify(query={"_id": doc["_id"]},
                                                 update={"$set": {"metadata.1.dc:format.duration": duration}})

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

    def start_decklink_to_raw(self, doc, decklink_id):
        duration = doc["metadata"][1]["dc:format"]["duration"]

        temp_decklink_to_raw = self.decklink_to_raw.copy()
        temp_decklink_to_raw[7] = decklink_id
        temp_decklink_to_raw[9] = str(duration*60)  # convert minutes to seconds
        temp_decklink_to_raw[-1] = self.raw_videos_path + doc["metadata"][1]["dc:title"][0] + " -- " +\
                                   str(doc["metadata"][1]["dcterms:created"]) + ".nut"

        temp_log_settings = self.log_settings.copy()
        temp_log_settings["action"] = "decklink_to_raw"
        temp_log_settings["vuid"] = doc["metadata"][1]["dc:identifier"]
        temp_log_settings["year"] = doc["metadata"][1]["dcterms:created"]
        temp_log_settings["title"] = doc["metadata"][1]["dc:title"]
        temp_log_settings["duration"] = duration

        p = Process(target=run_ffmpeg, args=(temp_decklink_to_raw, temp_log_settings))
        p.start()

    def start_raw_to_h264(self, doc):
        duration = doc["metadata"][1]["dc:format"]["duration"]
        filename = doc["metadata"][0]["filename"]
        size_ratio = doc["metadata"][1]["dc:format"]["size_ratio"]

        temp_raw_to_h264 = self.raw_to_h264.copy()
        temp_raw_to_h264[5] = filename
        temp_raw_to_h264[7] = size_ratio
        temp_raw_to_h264[-1] = self.compressed_videos_path + doc["metadata"][1]["dc:title"][0] + " -- " +\
                               str(doc["metadata"][1]["dcterms:created"]) + ".mkv"

        temp_log_settings = self.log_settings.copy()
        temp_log_settings["action"] = "raw_to_h264"
        temp_log_settings["vuid"] = doc["metadata"][1]["dc:identifier"]
        temp_log_settings["year"] = doc["metadata"][1]["dcterms:created"]
        temp_log_settings["title"] = doc["metadata"][1]["dc:title"]
        temp_log_settings["duration"] = duration

        p = Process(target=run_ffmpeg, args=(temp_raw_to_h264, temp_log_settings))
        p.start()

    def start_watch(self):
        print("Night gathers, and now my watch begins. It shall not end until my death...")
        currently_processing = [[], []]  # [decklink], [other_conversions]
        while True:
            for doc in self.waiting_conversions_collection.find({}):
                vuid = doc["metadata"][1]["dc:identifier"]

                if doc["metadata"][0]["source"] == "decklink_1" and vuid not in currently_processing[0]:
                    currently_processing[0].append(vuid)
                    self.start_decklink_to_raw(doc, "Intensity Pro (1)@16")

                elif doc["metadata"][0]["source"] == "decklink_2" and vuid not in currently_processing[0]:
                    currently_processing[0].append(vuid)
                    self.start_decklink_to_raw(doc, "Intensity Pro (2)@16")

                elif doc["metadata"][0]["source"] == "DVD" and len(currently_processing[1]) == 0:
                    currently_processing[1].append(vuid)
                    self.start_dvd_conversion(doc)

                elif doc["metadata"][0]["source"] == "decklink_raw" and len(currently_processing[1]) == 0:
                    currently_processing[1].append(vuid)
                    self.start_raw_to_h264(doc)

                elif doc["metadata"][0]["source"] == "file":
                    pass

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
                                         "metadata.0.source": "decklink_raw"}})
                    currently_processing[0].remove(vuid)
                    self.ongoing_conversions_collection.remove(query={"_id": doc["_id"]})

                elif doc["action"] == "DVD" and doc["return_code"] == 0:
                    if len(video_metadata) == 1:
                        dublin_dict = video_metadata[0]["metadata"][1]
                        dublin_dict["files_path"] = {"h264": converted_file_path}
                        dublin_dict["source"] = "DVD"
                        self.videos_metadata_collection.update(query={"dc:identifier": vuid},
                                                               update=dublin_dict)
                        currently_processing[1].remove(vuid)
                    else:
                        raise ValueError("Vuid shouldn't repeat in the waiting_conversions_collection. I messed up ")

                elif doc["action"] == "raw_to_h264" and doc["return_code"] == 0:
                    pprint(video_metadata)
                    if len(video_metadata) == 1:
                        dublin_dict = video_metadata[0]["metadata"][1]
                        dublin_dict["files_path"] = {"h264": converted_file_path}
                        dublin_dict["source"] = "Decklink"
                        self.videos_metadata_collection.update(spec={"dc:identifier": vuid}, document={"$set": dublin_dict}, upsert=False)
                        self.waiting_conversions_collection.remove(spec_or_id={"metadata.1.dc:identifier": vuid})
                        self.ongoing_conversions_collection.remove(spec_or_id={"vuid": vuid})
                        currently_processing[1].remove(vuid)
                    else:
                        raise ValueError("Vuid shouldn't repeat in the waiting_conversions_collection. I messed up ")
            sleep(5)


if __name__ == '__main__':
    # infinite loop here
    # check for waiting_conversions_collection
    # start in priority decklink acquisition jobs, when they are done start the jobs that need the raw decklink files
    # even if this will be checked in the gui check if the decklink card is not already in use
    # use first startup check every time
    backend = Backend()
    try:
        backend.start_watch()
    except KeyboardInterrupt:
        pass





print("knooooooooooookonk")
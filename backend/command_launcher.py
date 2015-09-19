import subprocess
from pymongo import MongoClient
from datetime import datetime
from os import getpid
from pprint import pprint


def run_ffmpeg(shell_command, log_settings):
    """

    :param shell_command: list, order matter
        example: ['nice', '-n', '19', "echo", "I like kiwis"]
    :param log_settings: dictionary
        example: {
            "action": "raw_to_h264",
            "vuid": 1,
            "year": 1995,
            "title": "the killer cactus' story",
            "duration": 2 (min)
            }


    :return:
    """

    pprint(shell_command)
    process = subprocess.Popen(shell_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

    db_client = MongoClient("mongodb://localhost:27017/")
    log_database = db_client["log-database"]

    complete_logs = log_database["run_ffmpeg_complete_logs"]
    complete_logs_document = {"vuid": log_settings["vuid"],
                              "action": log_settings["action"],
                              "year": log_settings["year"],
                              "title": log_settings["title"],
                              "duration": log_settings["duration"],
                              "start_date": datetime.now(),
                              "pid": getpid(),
                              "shell_command": shell_command,
                              "return_code": None,
                              "end_date": None,
                              "converted_file_path": None,
                              "log_data": []
                              }
    complete_logs_document_id = complete_logs.insert(complete_logs_document)

    ongoing_conversions = log_database["run_ffmpeg_ongoing_conversions"]
    ongoing_conversions_document = {"vuid": log_settings["vuid"],
                                    "action": log_settings["action"],
                                    "year": log_settings["year"],
                                    "title": log_settings["title"],
                                    "duration": log_settings["duration"],
                                    "start_date": datetime.now(),
                                    "pid": getpid(),
                                    "return_code": None,
                                    "end_date": None,
                                    "converted_file_path": None,
                                    "log_data": {}
                                    }

    if log_settings["decklink_id"]:
        ongoing_conversions_document["decklink_id"] = log_settings["decklink_id"]

    ongoing_conversions_document_id = ongoing_conversions.insert(ongoing_conversions_document)

    while True:
        if process.poll() is not None:  # returns None while subprocess is running
            return_code = process.returncode
            complete_logs.find_and_modify(query={"_id": complete_logs_document_id},
                                          update={"$set": {"end_date": datetime.now(), "return_code": return_code}}, fsync=True)
            ongoing_conversions.find_and_modify(query={"_id": ongoing_conversions_document_id},
                                                update={"$set": {"end_date": datetime.now(), "return_code": return_code}}, fsync=True)

            if return_code is 0:
                converted_file_path = shell_command[-1]
                complete_logs.find_and_modify(query={"_id": complete_logs_document_id},
                                              update={"$set": {"converted_file_path": converted_file_path}}, fsync=True)
                ongoing_conversions.find_and_modify(query={"_id": ongoing_conversions_document_id},
                                                    update={"$set": {"converted_file_path": converted_file_path}}, fsync=True)
            else:
                db_client.close()
                raise ChildProcessError("FFMPEG process returned with a non zero code \"", str(return_code),
                                        "\" , see complete log for details")
            break

        # stdout_line example: frame=  288 fps= 16 q=32.0 size=    1172kB time=00:00:09.77 bitrate= 982.4kbits/s
        stdout_complete_line = process.stdout.readline()

        complete_logs.find_and_modify(query={"_id": complete_logs_document_id},
                                      update={"$push": {"log_data": stdout_complete_line}})

        stdout_line = stdout_complete_line[:-5]
        if stdout_line.startswith("frame="):
            list_of_characters = []
            counter = 0
            for character in stdout_line:
                if not character == " ":
                    list_of_characters.append(character)
                elif not stdout_line[counter - 1] == "=" and not stdout_line[counter - 1] == " ":
                    list_of_characters.append(character)
                counter += 1

            # ffmpeg_output example : frame=17 fps=0.0 q=0.0 size=1kB time=00:00:00.34 bitrate=18.0kbits/s
            ffmpeg_output = "".join(list_of_characters)
            stdout_dictionary = {}
            for key_value in ffmpeg_output.split(" "):
                a = key_value.split("=")
                stdout_dictionary[a[0]] = a[1]
            # {'fps': '0.0', 'bitrate': '18.0kbits/s', 'frame': '16', 'time': '00:00:00.34', 'q': '0.0', 'size': '1kB'}
            # yield stdout_dictionary
            ongoing_conversions.find_and_modify(query={"_id": ongoing_conversions_document_id},
                                                update={"$set": {"log_data": stdout_dictionary}})
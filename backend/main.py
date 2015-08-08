__author__ = 'adrien'
from multiprocessing import Process
from backend.command_launcher import run_ffmpeg

# todo store converted video with vuid -- video_name name; same for raw videos

# The last value give the final size of the file (audio + video + mux)
# {'time': '00:00:10.00', 'bitrate': '2771.4kbits/s', 'fps': '8.0', 'q': '-1.0', 'Lsize': '3385kB', 'frame': '250'}
# use Variable bitrate for the conversion!!!
shell_command = [
            'nice', '-n', '19',
                'ffmpeg',
                    '-i', '/home/adrien/Documents/tm/test1.avi',
                        '-strict', '-2',
                        '-t', '10',
                        '-c:v', 'libx264', '-crf', '26', '-preset', 'slow', '-filter:v', 'hqdn3d=3:2:2:3',
                        '-c:a', 'libfdk_aac', '-b:a', '128k',
                    '/home/adrien/Documents/tm/test2.mkv'
            ]

log_settings = {
            "mongo_db": {
                "server_address": "mongodb://localhost:27017/",
                "database": "log-database",
                "complete_logs": "run_ffmpeg_complete_logs",
                "ongoing_conversions": "run_ffmpeg_ongoing_conversions"},
            "action": "raw_to_h264",
            "vuid": 2,
            "year": 1965,
            "title": "the holloway",
            "duration": 1/6
            }

if __name__ == '__main__':
    # infinite loop here
    # check for waiting_conversions table
    # start in priority decklink acquisition jobs, when they are done start the jobs that need the raw decklink files
    # even if this will be checked in the gui check if the decklink card is not already in use
    p = Process(target=run_ffmpeg, args=(shell_command, log_settings))
    p.start()
    #p.de

print("knooooooooooookonk")
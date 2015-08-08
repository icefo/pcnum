__author__ = 'adrien'

try:
    from pymongo import MongoClient
except ImportError as import_error:
    print("Impossible d'importer le module pour acceder à la base de donnée")
    raise import_error

try:
    mongo_client = MongoClient("mongodb://localhost:27017/")
    log_database = mongo_client["log-database"]
    complete_logs = log_database["run_ffmpeg_complete_logs"]
    ongoing_conversions = log_database["run_ffmpeg_ongoing_conversions"]
except Exception as e:
    print("Impossible de se connecter à la base de donnée")
    raise e

try:
    import PyQt5
except ImportError as import_error:
    print("Impossible d'importer le module d'interface graphique")
    raise import_error

video_paths = ["/media/raw_videos/", "/media/compressed_videos"]
for videos_path in video_paths:
    try:
        with open(videos_path + "testfile.txt", "w"):
            kkll = True
    except IOError as io_error:
        print("Impossible d'écrire sur le dossier \"" + videos_path)
        raise io_error

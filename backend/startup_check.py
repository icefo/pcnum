__author__ = 'adrien'

try:
    from pymongo import MongoClient
except ImportError as import_error:
    print("Impossible d'importer le module pour acceder à la base de donnée")
    raise import_error

try:
    mongo_client = MongoClient("mongodb://localhost:27017/")

    ffmpeg_db = mongo_client["ffmpeg_conversions"]
    complete_conversions_logs_collection = ffmpeg_db["complete_conversion_logs"]
    ongoing_conversions_collection = ffmpeg_db["ongoing_conversions"]
    waiting_conversions_collection = ffmpeg_db["waiting_conversions"]

    metadata_database = mongo_client["metadata"]
    videos_metadata_collection = metadata_database["videos_metadata"]
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

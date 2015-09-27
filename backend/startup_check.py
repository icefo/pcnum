__author__ = 'adrien'


def startup_check():
    video_paths = ["/media/storage/raw/", "/media/storage/compressed", "/media/storage/imported/"]
    for videos_path in video_paths:
        try:
            with open(videos_path + "testfile.txt", "w"):
                kkll = True
        except IOError as io_error:
            print("Impossible d'écrire sur le dossier \"" + videos_path)
            raise io_error

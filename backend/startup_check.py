__author__ = 'adrien'

from backend.shared import FILES_PATHS
import os


def startup_check():
    for files_path in FILES_PATHS.values():
        try:
            with open(files_path + "testfile.txt", "w"):
                pass
            os.remove(files_path + "testfile.txt")
        except IOError as io_error:
            print("Impossible d'écrire sur le dossier \"" + files_path)
            raise io_error

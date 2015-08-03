__author__ = 'adrien'

from PyQt5 import QtCore
from time import sleep

class DigitiseWidgetWorker(QtCore.QObject):

    launch_digitise_done = QtCore.pyqtSignal([str])
    finished = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        print("DigitiseWidget Worker init")

    def digitise(self, command):
        print("bridge digitize()")
        print(command[0])
        sleep(5)
        print(command[1])
        self.launch_digitise_done.emit("Okayyyyy")
        self.finished.emit()
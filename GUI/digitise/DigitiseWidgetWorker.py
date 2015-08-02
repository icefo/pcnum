__author__ = 'adrien'

from PyQt5 import QtCore
import xmlrpc.client

class DigitiseWidgetWorker(QtCore.QObject):

    client = xmlrpc.client.ServerProxy('http://localhost:8000')

    launch_digitise_done = QtCore.pyqtSignal([str])
    finished = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        print("DigitiseWidget Worker init")

    def digitise(self, command=None):
        print("bridge digitize()")
        return_status = self.client.launch_digitise(command)
        self.launch_digitise_done.emit(return_status)
        self.finished.emit()
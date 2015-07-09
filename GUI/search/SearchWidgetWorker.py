__author__ = 'adrien'

from PyQt5 import QtCore
import xmlrpc.client


class SearchWidgetWorker(QtCore.QObject):

    client = xmlrpc.client.ServerProxy('http://localhost:8000')

    search_done = QtCore.pyqtSignal([list])
    finished = QtCore.pyqtSignal()
    print("SearchWidget worker init")

    def __init__(self):
        super().__init__()

    def search(self, command):
        print("bridge search()")
        return_payload = self.client.search(command)
        #print(return_payload)
        self.search_done.emit(return_payload)
        self.finished.emit()
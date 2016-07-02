from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5.QtWidgets import (QWidget,
                             QHeaderView, QGridLayout,
                             QProgressBar, QLabel, QTableWidget)
from PyQt5.QtGui import QFont
from backend.shared import TimedKeyDeleteDict
from random import randint

from PyQt5 import QtGui, QtCore, Qt
from PyQt5.QtWidgets import QApplication, QTableView, QItemDelegate, QStyleOptionProgressBar, QStyle, QMainWindow, QWidget
from sortedcontainers.sorteddict import SortedDict
import sys
from datetime import datetime
from uuid import uuid4
from copy import deepcopy


class CaptureModel(QtCore.QAbstractTableModel):
    def __init__(self, captures=SortedDict(), parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.__captures = captures
        self.__captures_time = dict()

    def rowCount(self, parent):
        return len(self.__captures)

    def columnCount(self, parent):
        return 4

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            column = index.column()
            value = self.__captures.peekitem(row)[1][column]
            return value

    # def setData(self, index, value, role=QtCore.Qt.EditRole):
    #     if role == QtCore.Qt.EditRole:
    #
    #         row = index.row()
    #         column = index.column()
    #
    #         self.__captures[row][column] = value
    #         self.dataChanged.emit(index, index)
    #         return True
    #     return False

    def insertData(self, capture_data):

        temp_list = list()
        for dico in capture_data:
            temp_list.clear()
            self.__captures_time[dico["dc:identifier"]] = dico["date_data_send"]

            temp_list.append(dico["title"])
            temp_list.append(dico["dcterms:created"])
            temp_list.append(dico["dc:identifier"])
            temp_list.append(dico["source"])

            if dico["dc:identifier"] not in self.__captures:
                pos = self.__captures.bisect(dico["dc:identifier"])
                self.beginInsertRows(QtCore.QModelIndex(), pos, pos)
                self.__captures[dico["dc:identifier"]] = deepcopy(temp_list)
                self.endInsertRows()
            else:
                self.__captures[dico["dc:identifier"]] = deepcopy(temp_list)

        time_now = datetime.now().timestamp()
        capture_keys_to_be_deleted = list()
        for uuid, timestamp in self.__captures_time.items():
            if time_now - timestamp > 120:
                capture_keys_to_be_deleted.append(uuid)

        if capture_keys_to_be_deleted:
            for key in capture_keys_to_be_deleted:
                pos = self.__captures.index(key)
                self.beginRemoveRows(QtCore.QModelIndex(), pos, pos)
                del self.__captures[key]
                del self.__captures_time[key]
                self.endRemoveRows()
        capture_keys_to_be_deleted.clear()
        self.dataChanged.emit(self.index(0, 0), self.index(len(self.__captures), 4))


    def headerData(self, section, orientation, role):

        headers = ["title", "dcterms:created", "dc:identifier", "source"]

        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            if section < len(headers):
                return headers[section]
            else:
                return "not implemented"

    # def insertRow(self, position, rows, parent=QtCore.QModelIndex()):
    #     self.beginInsertRow(parent, position, position + rows - 1)
    #
    #     for i in range(rows):
    #         defaultValues = [QtGui.QColor("#000000") for i in range(self.columnCount(None))]
    #         self.__captures.insert(position, defaultValues)
    #
    #     self.endInsertRows()
    #
    #     return True

    #
    # def removeRows(self, position, rows, parent=QtCore.QModelIndex()):
    #     self.beginRemoveRows(parent, position, position + rows - 1)
    #
    #     for i in range(rows):
    #         value = self.__captures[position]
    #         self.__captures.remove(value)
    #
    #     self.endRemoveRows()
    #     return True


class MainWindow(QMainWindow):
    """
    This class is a wamp client and adds the CaptureWidget, MainSearchWidget and StatusWidget in a QTabWidget.

    This class acts as a proxy for the widgets that want to communicate with the backend because they can't have a valid
     ApplicationSession that would allow them to be a wamp client and a QWidget.
    """

    def __init__(self, config=None):
        QMainWindow.__init__(self)

        self.my_timer = QTimer()

        self.main_window_init()
        self.timed_key_delete_dict_updater()

    def timed_key_delete_dict_updater(self):
        """
        Update the dictionary by iterating over it, this delete keys that are older than 60 seconds

        Enable or disable the decklink_radio_button to avoid launching to capture on the same card by mistake
        """
        l = ['75293c71-cbc4-4ab0-9038-eaa51522912f', '24ec269c-3e9d-4569-9590-0871116a7a54', '9aa268a2-179b-4042-b05d-055b3ae20a3e', '36deb919-330b-424a-8b8e-3586850891b5', '94996314-b5ff-4930-8c04-cea1d255c1c1', '62d6ad1c-0deb-4db5-a4c3-01eed4f7ccaa', '444d6a65-c873-4a06-9f67-b69e20bec1cc']
        l2 = list()
        for _ in range(3):
            l2.append({"title": "hey", "dcterms:created": "15:98:65", "dc:identifier": l[randint(1, 6)],
              "source": randint(0, 10), "date_data_send": datetime.now().timestamp()})

        self.waiting_model.insertData(l2)
        self.my_timer.singleShot(1500, self.timed_key_delete_dict_updater)

    def main_window_init(self):
        """
        This function init the main window

        It sets the status bar, menu bar and set the tabs class as central widget
        """
        self.setFont(QFont(QFont().defaultFamily(), 12))

        self.waiting_model = CaptureModel()
        self.waiting_model.insertData(
            [{"title": "ouill", "dcterms:created": "15:98:65", "dc:identifier": '75293c71-cbc4-4ab0-9038-eaa51522912f',
              "source": "bidule", "date_data_send": datetime.now().timestamp()}])
        tableView = QTableView()
        tableView.setModel(self.waiting_model)


        #########
        self.setCentralWidget(tableView)

        #########
        self.setGeometry(300, 300, 500, 400)
        self.setWindowTitle('Logiciel Numérisation')
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())

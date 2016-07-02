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


class CaptureModel(QtCore.QAbstractTableModel):
    def __init__(self, captures=SortedDict(), parent=None, capture_type=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.__captures = captures
        self.__captures_time = dict()
        if capture_type == "ongoing":
            self.__capture_type = (capture_type, 7)
        elif capture_type == "waiting":
            self.__capture_type = (capture_type, 4)
        else:
            raise ValueError

    def rowCount(self, parent):
        return len(self.__captures)

    def columnCount(self, parent):
        return self.__capture_type[1]

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

        self.__captures_time[capture_data["dc:identifier"]] = capture_data["date_data_send"]

        temp_list = list()
        if self.__capture_type[0] == "ongoing":
            temp_list.append(capture_data["title"])
            temp_list.append(capture_data["year"])
            temp_list.append(capture_data["dc:identifier"])
            temp_list.append(capture_data["start_date"])
            temp_list.append(capture_data["source"])
            temp_list.append(capture_data["action"])
            temp_list.append(capture_data["progress"])

            if capture_data["dc:identifier"] not in self.__captures:
                pos = self.__captures.bisect(capture_data["dc:identifier"])
                self.beginInsertRows(QtCore.QModelIndex(), pos, pos)
                self.__captures[capture_data["dc:identifier"]] = temp_list
                self.endInsertRows()
            else:
                self.__captures[capture_data["dc:identifier"]] = temp_list

        elif self.__capture_type[0] == "waiting":
            for dico in capture_data:
                temp_list.append(dico["title"])
                temp_list.append(dico["dcterms:created"])
                temp_list.append(dico["dc:identifier"])
                temp_list.append(dico["source"])

                if dico["dc:identifier"] not in self.__captures:
                    pos = self.__captures.bisect(dico["dc:identifier"])
                    self.beginInsertRows(QtCore.QModelIndex(), pos, pos)
                    self.__captures[dico["dc:identifier"]] = temp_list
                    self.endInsertRows()
                else:
                    self.__captures[dico["dc:identifier"]] = temp_list

                temp_list.clear()

        time_now = datetime.now().timestamp()
        capture_keys_to_be_deleted = list()
        for uuid, timestamp in self.__captures_time.items():
            if time_now - timestamp > 15:
                capture_keys_to_be_deleted.append(uuid)
        if capture_keys_to_be_deleted:
            for key in capture_keys_to_be_deleted:
                pos = self.__captures.index(key)
                self.beginRemoveRows(QtCore.QModelIndex(), pos, pos)
                del self.__captures[key]
                del self.__captures_time[key]
                self.endRemoveRows()
        capture_keys_to_be_deleted.clear()

        self.dataChanged.emit(self.index(0, 0), self.index(len(self.__captures),
                                                           self.__capture_type[1]))

    def headerData(self, section, orientation, role):
        if self.__capture_type[0] == "ongoing":
            headers = ["title", "year", "dc:identifier", "start_date", "source", "action", "progress"]
        elif self.__capture_type[0] == "waiting":
            headers = ["title", "dcterms:created", "dc:identifier", "source"]
        else:
            headers = None

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


class ProgressBarDelegate(QItemDelegate):
    def __init__(self):
        QItemDelegate.__init__(self)

    # def createEditor(self, parent, option, index):
    #     print(parent)
    #     editor = QProgressBar(parent)
    #     editor.setMinimum(0)
    #     editor.setMaximum(100)
    #     print("dfndn")
    #     return editor
    #
    # def setEditorData(self, editor, index):
    #     value = index.model().data(index, QtCore.Qt.EditRole)
    #     editor.setValue(value)

    def paint(self, QPainter, QStyleOptionViewItem, QModelIndex):
        opts = QStyleOptionProgressBar()
        opts.rect = QStyleOptionViewItem.rect
        opts.minimum = 1
        opts.maximum = 100

        percent = QModelIndex.model().data(QModelIndex, QtCore.Qt.DisplayRole)
        opts.progress = percent

        if percent == 0:
            opts.textVisible = False
        else:
            opts.textVisible = True

        opts.text = str(percent) + "% E"
        QApplication.style().drawControl(QStyle.CE_ProgressBar, opts, QPainter)


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

        for _ in range(10):
            self.ongoing_model.insertData(
                {"title": "your other honor", "year": 1896, "dc:identifier": str(randint(1, 10)),
                 "start_date": "16:86:96", "source": "vhs", "action": "digitise", "progress": randint(0, 100),
                 "date_data_send": datetime.now().timestamp()})

        self.my_timer.singleShot(2000, self.timed_key_delete_dict_updater)

    def main_window_init(self):
        """
        This function init the main window

        It sets the status bar, menu bar and set the tabs class as central widget
        """
        self.setFont(QFont(QFont().defaultFamily(), 12))

        # self.ongoing_model = OngoingCapturesModel(capture_type="ongoing")
        self.waiting_model = CaptureModel(capture_type="waiting")
        # model.insertColumns(0, 5)
        # model.removeRows(3, 1)
        # model.setData(model.index(0, 6), 12)
        # self.ongoing_model.insertData({"title": "l'honneur", "year": 1896, "dc:identifier": '65293c71-cbc4-4ab0-9038-eaa51522912f',
        #                                "start_date": "16:86:96", "source": "vhs", "action": "digitise", "progress": 22,
        #                                "date_data_send": datetime.now().timestamp()})
        self.waiting_model.insertData(
            [{"title": "hey", "dcterms:created": "15:98:65", "dc:identifier": '75293c71-cbc4-4ab0-9038-eaa51522912f',
              "source": "bidule", "date_data_send": datetime.now().timestamp()}])
        tableView = QTableView()
        tableView.setModel(self.wa)

        delegate = ProgressBarDelegate()
        # tableView.setItemDelegateForColumn(6, delegate)

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
from PyQt5 import QtCore

from sortedcontainers.sorteddict import SortedDict
from datetime import datetime
from copy import deepcopy

# todo fusion the two models ? They turned out to be very similar

class WaitingCapturesModel(QtCore.QAbstractTableModel):
    """
    This class is the model for the waiting captures, it gets updated every 5 seconds or so if there is captures waiting

    This model use a SortedDict because I felt that a regular dict would have needed ugly hacks to do what I want and
    after some head-scratching I managed to write a working model thanks to that wonderful datastructure
    """
    def __init__(self, captures=SortedDict(), parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.__captures = captures
        self.__captures_time = dict()

    def rowCount(self, parent=None):
        return len(self.__captures)

    def columnCount(self, parent=None):
        return 4

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            column = index.column()
            return self.__captures.peekitem(row)[1][column]

    def insertData(self, capture_data):
        """
        This function insert or update data in the model, it also automatically delete old data from the model
        Args:
            capture_data (list): contains a list of dictionaries containing the following keys:
                                title, date_data_send, dcterms:created, dc:identifier, source

        """

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
            if time_now - timestamp > 30:
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


class OngoingCapturesModel(QtCore.QAbstractTableModel):
    """
    This class is the model for the ongoing captures, it gets updated randomly

    This model use a SortedDict because I felt that a regular dict would have needed ugly hacks to do what I want and
    after some head-scratching I managed to write a working model thanks to that wonderful datastructure
    """
    def __init__(self, captures=SortedDict(), parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.__captures = captures
        self.__captures_time = dict()

    def rowCount(self, parent=None):
        return len(self.__captures)

    def columnCount(self, parent=None):
        return 7

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            column = index.column()
            return self.__captures.peekitem(row)[1][column]
        elif role == 'decklink_check':
            row = index
            try:
                value = self.__captures.peekitem(row)[1][7]
                print(value)
            except IndexError:
                value = None
            return value

    def insertData(self, capture_data):
        """
        This function insert or update data in the model, it also automatically delete old data from the model
        Args:
            capture_data (dict): Is a dictionary containing the following keys:
                title, year, dc:identifier, start_date, source, action, progress, decklink_id (if applicable)

        """

        self.__captures_time[capture_data["dc:identifier"]] = capture_data["date_data_send"]

        temp_list = list()
        temp_list.append(capture_data["title"])
        temp_list.append(capture_data["year"])
        temp_list.append(capture_data["dc:identifier"])
        temp_list.append(capture_data["start_date"])
        temp_list.append(capture_data["source"])
        temp_list.append(capture_data["action"])
        temp_list.append(capture_data["progress"])
        if 'decklink_id' in capture_data:
            temp_list.append(capture_data['decklink_id'])

        if capture_data["dc:identifier"] not in self.__captures:
            pos = self.__captures.bisect(capture_data["dc:identifier"])
            self.beginInsertRows(QtCore.QModelIndex(), pos, pos)
            self.__captures[capture_data["dc:identifier"]] = temp_list
            self.endInsertRows()
        else:
            self.__captures[capture_data["dc:identifier"]] = temp_list

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

        self.dataChanged.emit(self.index(0, 0), self.index(len(self.__captures), 7))

    def headerData(self, section, orientation, role):
        headers = ["title", "year", "dc:identifier", "start_date", "source", "action", "progress"]

        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            if section < len(headers):
                return headers[section]
            else:
                return "not implemented"

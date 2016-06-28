from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5.QtWidgets import (QWidget,
                             QHeaderView, QGridLayout,
                             QProgressBar, QLabel, QTableWidget)
from PyQt5.QtGui import QFont
from backend.shared import TimedKeyDeleteDict

# todo check the ffmpeg_complete_logs collection at startup and warn the user that something went wrong if the return code != 0

from PyQt5 import QtGui, QtCore, Qt
from PyQt5.QtWidgets import QApplication, QTableView, QItemDelegate, QStyleOptionProgressBar, QStyle
import sys


class CaptureModel(QtCore.QAbstractTableModel):
    def __init__(self, captures=[[]], headers=[], parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.__captures = captures
        self.__headers = headers

    def rowCount(self, parent):
        return len(self.__captures)

    def columnCount(self, parent):
        return len(self.__captures[0])

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            column = index.column()
            value = self.__captures[row][column]
            return  value
        elif role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()
            value = self.__captures[row][column]
            return value

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:

            row = index.row()
            column = index.column()

            self.__captures[row][column] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                if section < len(self.__headers):
                    return self.__headers[section]
                else:
                    return "not implemented"

    def insertRows(self, position, rows, parent=QtCore.QModelIndex()):
        self.beginInsertRows(parent, position, position + rows - 1)

        for i in range(rows):
            defaultValues = [QtGui.QColor("#000000") for i in range(self.columnCount(None))]
            self.__captures.insert(position, defaultValues)

        self.endInsertRows()

        return True

    def removeRows(self, position, rows, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(parent, position, position + rows - 1)

        for i in range(rows):
            value = self.__captures[position]
            self.__captures.remove(value)

        self.endRemoveRows()
        return True


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


if __name__ == '__main__':
    app = QApplication(sys.argv)

    headers = ["title", "year", "dc:identifier", "start_date", "source", "action", "progress"]
    tableData0 = [[0, '', '', '', '', '', 0]]

    model = CaptureModel(tableData0, headers)
    # model.insertColumns(0, 5)
    # model.removeRows(3, 1)
    model.setData(model.index(0, 6), 12)

    tableView = QTableView()
    tableView.setModel(model)

    delegate = ProgressBarDelegate()
    tableView.setItemDelegateForColumn(6, delegate)
    tableView.show()

    sys.exit(app.exec_())
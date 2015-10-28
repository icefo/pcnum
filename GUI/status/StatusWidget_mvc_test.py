
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (QWidget,
                             QHeaderView, QGridLayout,
                             QProgressBar, QLabel, QTableWidget)
from PyQt5.QtGui import QFont
from backend.shared import AutoKeyDeleteDict
from pprint import pprint
import operator
from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex, QTimer
from PyQt5.QtWidgets import QTabWidget, QWidget, QTableView


class StatusWidget(QWidget):
    ongoing_capture_status_transmit = pyqtSignal([dict])
    waiting_capture_status_update = pyqtSignal([dict])

    def __init__(self):
        # Initialize the parent class QWidget
        super().__init__()

        #########
        self.widget_font = QFont(QFont().defaultFamily(), 12)

        #########
        self.ongoing_conversions = QTableWidget()
        self.waiting_conversions = QTableWidget()
        ongoing_captures_model = OnGoingCapturesTableModel(self)
        self.ongoing_capture_status_transmit.connect(ongoing_captures_model.ongoing_capture_status_update)
        self.ongoing_conversions = QTableView()
        self.ongoing_conversions.setModel(ongoing_captures_model)

        #########
        self.ongoing_conversions_label = QLabel("Conversions en cours:")
        self.waiting_conversions_label = QLabel("Conversions en attente:")

        #########
        self.waiting_conversions_dict = AutoKeyDeleteDict(timeout=5)

        #########
        self.tab_init()

    def tab_init(self):
        grid = QGridLayout()
        self.setLayout(grid)

        self.ongoing_capture_status_update.connect(self.ongoing_conversions_table_updater)

        #########
        grid.addWidget(self.ongoing_conversions_label, 0, 0)
        grid.addWidget(self.ongoing_conversions, 1, 0, 3, 2)
        grid.addWidget(self.waiting_conversions_label, 4, 0)
        grid.addWidget(self.waiting_conversions, 5, 0, 7, 2)


class OnGoingCapturesTableModel(QAbstractTableModel):
    ongoing_capture_status_update = pyqtSignal([dict])

    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self.ongoing_capture_status_update.connect(self.dict_updater)

        self.ongoing_captures_dict = AutoKeyDeleteDict(timeout=5)
        self.row_list = []
        self.header = ["titre", "année", "dc:identifier", "date début", "action", "progès"]

    def dict_updater(self, status):
        self.ongoing_captures_dict[status['dc:identifier']] = status

    def table_updater(self):
        for values in self.ongoing_captures_dict.values():
            self.row_list.append((values['title'][0],
                                  values['year'],
                                  values['dc:identifier'],
                                  values['start_date'],
                                  values['action']))

    def insertRow(self, p_int, row, QModelIndex_parent=QModelIndex(), *args, **kwargs):
        self.beginInsertRows(QModelIndex_parent, p_int, p_int)
        self.row_list.append(('assetic acid', 81.6, -43.8, 0.786))
        self.endInsertRows()

    def removeRow(self, p_int, QModelIndex_parent=None, *args, **kwargs):
        self.beginRemoveRows(QModelIndex_parent, p_int, p_int)

    def rowCount(self, QModelIndex_parent=QModelIndex(), *args, **kwargs):
        return len(self.row_list)

    def columnCount(self, QModelIndex_parent=QModelIndex(), *args, **kwargs):
        return len(self.row_list[0])

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        elif role != Qt.DisplayRole:
            return None
        return self.row_list[index.row()][index.column()]

    def headerData(self, p_int, Qt_Orientation, int_role=None):
        if Qt_Orientation == Qt.Horizontal and int_role == Qt.DisplayRole:
            return self.header[p_int]
        return None

    def sort(self, p_int, Qt_SortOrder_order=None):
        """sort table by given column number col"""
        self.layoutAboutToBeChanged.emit()
        self.row_list = sorted(self.row_list,
            key=operator.itemgetter(p_int))
        if Qt_SortOrder_order == Qt.DescendingOrder:
            self.row_list.reverse()
        self.layoutChanged.emit()
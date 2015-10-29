__author__ = 'adrien'
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

# todo check the ffmpeg_complete_logs collection at startup and warn the user that something went wrong if the return code != 0


class StatusWidget(QWidget):
    ongoing_capture_status_update = pyqtSignal([dict])
    waiting_captures_status_update = pyqtSignal([list])

    def __init__(self):
        # Initialize the parent class QWidget
        super().__init__()

        #########
        self.widget_font = QFont(QFont().defaultFamily(), 12)

        #########
        self.ongoing_captures = QTableWidget()
        self.waiting_captures = QTableWidget()

        #########
        self.ongoing_conversions_label = QLabel("Acquisitions en cours:")
        self.waiting_conversions_label = QLabel("Acquisitions en attente:")

        #########
        self.ongoing_conversions_dict = AutoKeyDeleteDict(timeout=5)
        self.waiting_conversions_dict = AutoKeyDeleteDict(timeout=5)

        #########
        self.tab_init()

    def ongoing_captures_table_updater(self, status):

        self.ongoing_conversions_dict[status['dc:identifier']] = status
        self.ongoing_captures.clearContents()
        self.ongoing_captures.setRowCount(0)
        for row in self.ongoing_conversions_dict.values():
            row_count = self.ongoing_captures.rowCount()
            self.ongoing_captures.insertRow(row_count)
            self.ongoing_captures.setCellWidget(row_count, 0, QLabel(row["title"][0]))
            self.ongoing_captures.setCellWidget(row_count, 1, QLabel(str(row["year"])))
            self.ongoing_captures.setCellWidget(row_count, 2, QLabel(str(row["dc:identifier"])))
            self.ongoing_captures.setCellWidget(row_count, 3, QLabel(row["start_date"]))
            self.ongoing_captures.setCellWidget(row_count, 4, QLabel(row["action"]))
            progress_bar = QProgressBar()
            progress_bar.setValue(row["progress"])
            self.ongoing_captures.setCellWidget(row_count, 5, progress_bar)

    def waiting_captures_table_updater(self, waiting_conversions_list):
        self.waiting_captures.clearContents()
        self.waiting_captures.setRowCount(0)
        for video_metadata in waiting_conversions_list:
            row_count = self.waiting_captures.rowCount()
            self.waiting_captures.insertRow(row_count)
            self.waiting_captures.setCellWidget(row_count, 0, QLabel(video_metadata[1]["dc:title"][0]))
            self.waiting_captures.setCellWidget(row_count, 1, QLabel(str(video_metadata[1]["dcterms:created"])))
            self.waiting_captures.setCellWidget(row_count, 2, QLabel(str(video_metadata[1]["dc:identifier"])))
            self.waiting_captures.setCellWidget(row_count, 3, QLabel(video_metadata[0]["source"]))

    def tab_init(self):
        grid = QGridLayout()
        self.setLayout(grid)

        self.ongoing_capture_status_update.connect(self.ongoing_captures_table_updater)
        self.waiting_captures_status_update.connect(self.waiting_captures_table_updater)
        #########
        self.ongoing_conversions_label.setFont(self.widget_font)
        self.waiting_conversions_label.setFont(self.widget_font)

        #########
        self.ongoing_captures.setRowCount(0)
        self.ongoing_captures.setColumnCount(6)
        self.ongoing_captures.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        # self.ongoing_captures.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.ongoing_captures.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.ongoing_captures.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.ongoing_captures.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        # self.ongoing_captures.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.ongoing_captures.setFont(self.widget_font)
        self.ongoing_captures.setHorizontalHeaderLabels(["titre", "année", "dc:identifier", "date début", "action", "progès"])

        #########
        self.waiting_captures.setRowCount(0)
        self.waiting_captures.setColumnCount(4)
        self.waiting_captures.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.waiting_captures.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.waiting_captures.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.waiting_captures.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.waiting_captures.setFont(self.widget_font)
        self.waiting_captures.setHorizontalHeaderLabels(["titre", "année", "vuid", "source"])

        #########
        grid.addWidget(self.ongoing_conversions_label, 0, 0)
        grid.addWidget(self.ongoing_captures, 1, 0, 3, 2)
        grid.addWidget(self.waiting_conversions_label, 4, 0)
        grid.addWidget(self.waiting_captures, 5, 0, 7, 2)

__author__ = 'adrien'
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QWidget,
                             QHeaderView, QGridLayout, QVBoxLayout,
                             QRadioButton, QTextEdit, QLabel, QTableWidget, QComboBox, QPushButton)
from PyQt5.QtGui import QFont
from collections import OrderedDict
from datetime import datetime
from functools import partial
from GUI.status.StatusWidgetWorker import StatusWidgetWorker

class StatusWidget(QWidget):
    def __init__(self):
        # Initialize the parent class QWidget
        super().__init__()

        self.ongoing_conversions = QTableWidget()
        self.waiting_conversions = QTableWidget()

        self.table_font = QFont(QFont().defaultFamily(), 12)

        # they have to be attached to the object, if not they are destroyed when the function exit
        self.worker_thread_status = None
        self.worker_object_status = None

        self.tab_init()
        self.status_worker()
        self.status_table_auto_updater()

    def tab_init(self):
        grid = QGridLayout()
        self.setLayout(grid)

        grid.addWidget(self.ongoing_conversions, 0, 0, 3, 2)
        grid.addWidget(self.waiting_conversions, 3, 0, 4, 2)

        self.ongoing_conversions.setRowCount(0)
        self.ongoing_conversions.setColumnCount(5)
        self.ongoing_conversions.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.ongoing_conversions.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.ongoing_conversions.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.ongoing_conversions.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.ongoing_conversions.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.ongoing_conversions.setFont(self.table_font)
        self.ongoing_conversions.setHorizontalHeaderLabels(["nom", "année", "vuid", "date début", "progès"])

    def status_worker(self):
        mongo_settings =\
            {
                "server_address": "mongodb://localhost:27017/",
                "database": "log-database",
                "complete_logs": "run_ffmpeg_complete_logs",
                "ongoing_conversions": "run_ffmpeg_ongoing_conversions"
            }

        self.worker_thread_status = QtCore.QThread()
        self.worker_object_status = StatusWidgetWorker(mongo_settings)
        self.worker_object_status.moveToThread(self.worker_thread_status)

        self.worker_thread_status.started.connect(self.worker_object_status.status_retriever)
        self.worker_object_status.ongoing_conversions_transmit.connect(self.status_table_auto_updater)

        self.worker_thread_status.start()

    def status_table_auto_updater(self, blup=[]):

        # self.ongoing_conversions.insertRow(0)
        # for column in range(5):
        #     self.ongoing_conversions.setCellWidget(0, column, QLabel("colonne" + str(column)))
        for sf in blup:
            print(sf)



__author__ = 'adrien'
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QWidget,
                             QHeaderView, QGridLayout,
                             QProgressBar, QLabel, QTableWidget)
from PyQt5.QtGui import QFont
from GUI.status.StatusWidgetWorker import StatusWidgetWorker
from pprint import pprint



class StatusWidget(QWidget):
    def __init__(self):
        # Initialize the parent class QWidget
        super().__init__()

        self.widget_font = QFont(QFont().defaultFamily(), 12)

        self.ongoing_conversions = QTableWidget()
        self.waiting_conversions = QTableWidget()

        self.ongoing_conversions_label = QLabel("Conversions en cours:")
        self.ongoing_conversions_label.setFont(self.widget_font)
        self.waiting_conversions_label = QLabel("Conversions en attente:")
        self.waiting_conversions_label.setFont(self.widget_font)

        # they have to be attached to the object, if not they are destroyed when the function exit
        self.worker_thread_status = None
        self.worker_object_status = None

        self.tab_init()
        self.status_worker()

    def status_worker(self):

        self.worker_thread_status = QtCore.QThread()
        self.worker_object_status = StatusWidgetWorker()
        self.worker_object_status.moveToThread(self.worker_thread_status)

        self.worker_thread_status.started.connect(self.worker_object_status.conversion_status)
        self.worker_object_status.ongoing_conversions_transmit.connect(self.ongoing_conversions_table_updater)
        self.worker_object_status.waiting_conversions_transmit.connect(self.waiting_conversions_table_updater)

        self.worker_thread_status.start()

    def ongoing_conversions_table_updater(self, ongoing_conversions_list):
        def get_sec(s):
            l = s.split(':')
            return float(l[0]) * 3600 + float(l[1]) * 60 + float(l[2])

        self.ongoing_conversions.clearContents()
        self.ongoing_conversions.setRowCount(0)
        for row in ongoing_conversions_list:
            row_count = self.ongoing_conversions.rowCount()
            self.ongoing_conversions.insertRow(row_count)
            self.ongoing_conversions.setCellWidget(row_count, 0, QLabel(row["title"][0]))
            self.ongoing_conversions.setCellWidget(row_count, 1, QLabel(str(row["year"])))
            self.ongoing_conversions.setCellWidget(row_count, 2, QLabel(str(row["vuid"])))
            start_date = row["start_date"].replace(microsecond=0).isoformat()
            self.ongoing_conversions.setCellWidget(row_count, 3, QLabel(start_date))
            self.ongoing_conversions.setCellWidget(row_count, 4, QLabel(row["action"]))
            try:
                done = get_sec(row["log_data"]["time"])
                total = row["duration"]
                progress = (done / total)*100
                progress = round(progress)
                progress_bar = QProgressBar()
                progress_bar.setRange(0, 100)
                progress_bar.setValue(progress)
                self.ongoing_conversions.setCellWidget(row_count, 5, progress_bar)
            except KeyError:
                pass
            print("Ongoing conversions")
            pprint(row)

    def waiting_conversions_table_updater(self, waiting_conversions_list):
        self.waiting_conversions.clearContents()
        self.waiting_conversions.setRowCount(0)
        for row in waiting_conversions_list:
            row_count = self.waiting_conversions.rowCount()
            self.waiting_conversions.insertRow(row_count)
            self.waiting_conversions.setCellWidget(row_count, 0, QLabel(row["metadata"][1]["dc:title"][0]))
            self.waiting_conversions.setCellWidget(row_count, 1, QLabel(str(row["metadata"][1]["dcterms:created"])))
            self.waiting_conversions.setCellWidget(row_count, 2, QLabel(str(row["metadata"][1]["dc:identifier"])))
            self.waiting_conversions.setCellWidget(row_count, 3, QLabel(row["metadata"][0]["source"]))

    def tab_init(self):
        grid = QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.ongoing_conversions_label, 0, 0)
        grid.addWidget(self.ongoing_conversions, 1, 0, 3, 2)
        grid.addWidget(self.waiting_conversions_label, 4, 0)
        grid.addWidget(self.waiting_conversions, 5, 0, 7, 2)

        self.ongoing_conversions.setRowCount(0)
        self.ongoing_conversions.setColumnCount(6)
        self.ongoing_conversions.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.ongoing_conversions.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.ongoing_conversions.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.ongoing_conversions.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.ongoing_conversions.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.ongoing_conversions.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.ongoing_conversions.setFont(self.widget_font)
        self.ongoing_conversions.setHorizontalHeaderLabels(["titre", "année", "vuid", "date début", "action", "progès"])

        self.waiting_conversions.setRowCount(0)
        self.waiting_conversions.setColumnCount(4)
        self.waiting_conversions.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.waiting_conversions.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.waiting_conversions.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.waiting_conversions.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.waiting_conversions.setFont(self.widget_font)
        self.waiting_conversions.setHorizontalHeaderLabels(["titre", "année", "vuid", "source"])



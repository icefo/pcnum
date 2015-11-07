from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (QWidget,
                             QHeaderView, QGridLayout,
                             QProgressBar, QLabel, QTableWidget)
from PyQt5.QtGui import QFont
from backend.shared import TimedKeyDeleteDict

# todo check the ffmpeg_complete_logs collection at startup and warn the user that something went wrong if the return code != 0


class StatusWidget(QWidget):
    """
    This QWidget gather the search query, transform it in a suitable format for MongoDB and then run it
    Attributes:
        self.receive_ongoing_capture_status (pyqtSignal([dict])): Dict sent by MainWindow
        self.receive_waiting_captures_status (pyqtSignal([list])): List of dict sent by MainWindow
    """

    receive_ongoing_capture_status = pyqtSignal([dict])
    receive_waiting_captures_status = pyqtSignal([list])

    def __init__(self):
        # Initialize the parent class QWidget
        super().__init__()

        #########
        self.widget_font = QFont(QFont().defaultFamily(), 12)

        #########
        self.ongoing_captures_table = QTableWidget()
        self.waiting_captures_table = QTableWidget()

        #########
        self.ongoing_conversions_label = QLabel("Acquisitions en cours:")
        self.waiting_conversions_label = QLabel("Acquisitions en attente:")

        #########
        self.ongoing_conversions_dict = TimedKeyDeleteDict(timeout=5)
        self.waiting_conversions_dict = TimedKeyDeleteDict(timeout=5)

        #########
        self.tab_init()

    def ongoing_captures_table_updater(self, capture_status):
        """
        This function is called when the self.receive_ongoing_capture_status signal is fired.
        This signal is fired whenever one of the ongoing capture has an update which happens randomly.

        Args:
            capture_status (dict): Dict that contain the following keys:
                title, year, dc:identifier, start_date, action

        Examples:
            When the function is called, it add the 'dc:identifier' key with the 'capture_status' argument as value
             to a TimedKeyDeleteDict.

            This dictionary is set to delete the keys that are older than 5 seconds so when an ongoing_capture stop to
             send updates, its key is deleted after 5 seconds and doesn't show up anymore
             in the 'self.ongoing_captures_table'

        Returns:
            nothing
        """

        self.ongoing_conversions_dict[capture_status['dc:identifier']] = capture_status
        self.ongoing_captures_table.clearContents()
        self.ongoing_captures_table.setRowCount(0)
        for row in self.ongoing_conversions_dict.values():
            row_count = self.ongoing_captures_table.rowCount()
            self.ongoing_captures_table.insertRow(row_count)
            self.ongoing_captures_table.setCellWidget(row_count, 0, QLabel(row["title"][0]))
            self.ongoing_captures_table.setCellWidget(row_count, 1, QLabel(str(row["year"])))
            self.ongoing_captures_table.setCellWidget(row_count, 2, QLabel(str(row["dc:identifier"])))
            self.ongoing_captures_table.setCellWidget(row_count, 3, QLabel(row["start_date"]))
            self.ongoing_captures_table.setCellWidget(row_count, 4, QLabel(row["action"]))
            progress_bar = QProgressBar()
            progress_bar.setValue(row["progress"])
            self.ongoing_captures_table.setCellWidget(row_count, 5, progress_bar)

    def waiting_captures_table_updater(self, waiting_captures):
        """
        This function is called when the self.receive_waiting_captures_status signal is fired.
        This signal is fired every 5 seconds.

        Args:
            waiting_captures (list): List of dicts. These dicts contain the following keys:
                dc:title, dcterms:created, dc:identifier, source

        Returns:
            nothing
        """

        self.waiting_captures_table.clearContents()
        self.waiting_captures_table.setRowCount(0)
        for row in waiting_captures:
            row_count = self.waiting_captures_table.rowCount()
            self.waiting_captures_table.insertRow(row_count)
            self.waiting_captures_table.setCellWidget(row_count, 0, QLabel(row[1]["dc:title"][0]))
            self.waiting_captures_table.setCellWidget(row_count, 1, QLabel(str(row[1]["dcterms:created"])))
            self.waiting_captures_table.setCellWidget(row_count, 2, QLabel(str(row[1]["dc:identifier"])))
            self.waiting_captures_table.setCellWidget(row_count, 3, QLabel(row[0]["source"]))

    def tab_init(self):
        """
        This function is called when the StatusWidget class init
        Its job is to put the widgets instantiated in the init function to their place and set some link between
         functions and buttons

        Returns:
            nothing
        """

        grid = QGridLayout()
        self.setLayout(grid)

        self.receive_ongoing_capture_status.connect(self.ongoing_captures_table_updater)
        self.receive_waiting_captures_status.connect(self.waiting_captures_table_updater)
        #########
        self.ongoing_conversions_label.setFont(self.widget_font)
        self.waiting_conversions_label.setFont(self.widget_font)

        #########
        self.ongoing_captures_table.setRowCount(0)
        self.ongoing_captures_table.setColumnCount(6)
        self.ongoing_captures_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        # self.ongoing_captures_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.ongoing_captures_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.ongoing_captures_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.ongoing_captures_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        # self.ongoing_captures_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.ongoing_captures_table.setFont(self.widget_font)
        self.ongoing_captures_table.setHorizontalHeaderLabels(["titre", "année", "dc:identifier", "date début", "action", "progès"])

        #########
        self.waiting_captures_table.setRowCount(0)
        self.waiting_captures_table.setColumnCount(4)
        self.waiting_captures_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.waiting_captures_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.waiting_captures_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.waiting_captures_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.waiting_captures_table.setFont(self.widget_font)
        self.waiting_captures_table.setHorizontalHeaderLabels(["titre", "année", "vuid", "source"])

        #########
        grid.addWidget(self.ongoing_conversions_label, 0, 0)
        grid.addWidget(self.ongoing_captures_table, 1, 0, 3, 2)
        grid.addWidget(self.waiting_conversions_label, 4, 0)
        grid.addWidget(self.waiting_captures_table, 5, 0, 7, 2)

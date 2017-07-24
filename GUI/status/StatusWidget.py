from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5.QtWidgets import (QWidget,
                             QHeaderView, QGridLayout,
                             QLabel, QTableView)
from PyQt5.QtGui import QFont

from GUI.status.Models import OngoingCapturesModel, WaitingCapturesModel
from GUI.status.Views import ProgressBarDelegate

# todo check the ffmpeg_complete_logs collection at startup and warn the user that something went wrong if the return code != 0


class StatusWidget(QWidget):
    """
    This QWidget gather the search query, transform it in a suitable format for MongoDB and then run it

    Attributes:
        self.send_enable_decklink_radio_1 (pyqtSignal([bool])): bool sent to the CaptureWidget
        self.send_enable_decklink_radio_2 (pyqtSignal([bool])): bool sent to the CaptureWidget
        self.receive_ongoing_capture_status (pyqtSignal([dict])): Dict sent by MainWindow
        self.receive_waiting_captures_status (pyqtSignal([list])): List of dict sent by MainWindow
    """

    send_enable_decklink_radio_1 = pyqtSignal([bool])
    send_enable_decklink_radio_2 = pyqtSignal([bool])

    def __init__(self):
        # Initialize the parent class QWidget
        # this allow the use of the parent's methods when needed
        super(StatusWidget, self).__init__()

        #########
        self.widget_font = QFont(QFont().defaultFamily(), 12)

        #########
        self.ongoing_captures_model = OngoingCapturesModel()
        self.waiting_captures_model = WaitingCapturesModel()

        #########
        self.ongoing_captures_table = QTableView()
        self.waiting_captures_table = QTableView()

        #########
        self.ongoing_conversions_label = QLabel("Acquisitions en cours:")
        self.waiting_conversions_label = QLabel("Acquisitions en attente:")

        #########
        self.my_timer = QTimer()
        self.timed_decklink_check()

        #########
        self.tab_init()

    def ongoing_capture_receiver(self, capture_status):
        """
        Is called whenever one of the ongoing capture has an update which happens randomly.

        Args:
            capture_status (dict): Dict that contain the following keys:
                'date_data_send', 'source', 'start_date', 'dc:identifier', 'action', 'progress', 'title', 'year',
                'decklink_id' (if applicable)
        """

        self.ongoing_captures_model.insertData(capture_status)

    def waiting_captures_receiver(self, waiting_captures):

        """
        Is called when the backend publish a list of waiting captures

        Notes:
            If there is at least one capture waiting this function is called every 5 seconds.

        Args:
            waiting_captures (list): List of dicts. These dicts contain the following keys:
                dc:title, dcterms:created, dc:identifier, source, date_data_send
        """

        self.waiting_captures_model.insertData(waiting_captures)

    def timed_decklink_check(self):
        """

        Enable or disable the decklink_radio_button to avoid launching to capture on the same card by mistake
        """

        activate_decklink_button = {1: True, 2: True}
        column_count = self.ongoing_captures_model.columnCount()
        for i in range(column_count):

            decklink_id = self.ongoing_captures_model.data(i, 'decklink_check')
            if decklink_id: # possible values: None, 1, 2
                activate_decklink_button[decklink_id] = False
        self.send_enable_decklink_radio_1.emit(activate_decklink_button[1])
        self.send_enable_decklink_radio_2.emit(activate_decklink_button[2])

        self.my_timer.singleShot(2000, self.timed_decklink_check)

    def tab_init(self):
        """
        This function is called when the StatusWidget class init

        Its job is to put the widgets instantiated in the init function to their place and set some link between
         functions and buttons
        """

        grid = QGridLayout()
        self.setLayout(grid)
        self.setFont(self.widget_font)

        #########
        self.ongoing_captures_table.setModel(self.ongoing_captures_model)

        self.ongoing_captures_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        # self.ongoing_captures_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.ongoing_captures_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.ongoing_captures_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        # self.ongoing_captures_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.ongoing_captures_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        # self.ongoing_captures_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)

        delegate = ProgressBarDelegate()
        self.ongoing_captures_table.setItemDelegateForColumn(6, delegate)

        #########
        self.waiting_captures_table.setModel(self.waiting_captures_model)

        self.waiting_captures_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.waiting_captures_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.waiting_captures_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.waiting_captures_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

        #########
        grid.addWidget(self.ongoing_conversions_label, 0, 0)
        grid.addWidget(self.ongoing_captures_table, 1, 0, 3, 2)
        grid.addWidget(self.waiting_conversions_label, 4, 0)
        grid.addWidget(self.waiting_captures_table, 5, 0, 7, 2)

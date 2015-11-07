import sys

from PyQt5.QtWidgets import QMainWindow, QApplication, QTabWidget

from GUI.digitise.CaptureWidget import CaptureWidget
from GUI.search.MainSearchWidget import MainSearchWidget
from GUI.status.StatusWidget import StatusWidget
import setproctitle
from backend.startup_check import startup_check

from backend.shared import async_call

import asyncio
from autobahn.asyncio.wamp import ApplicationRunner
from autobahn.asyncio.wamp import ApplicationSession

from quamash import QEventLoop

# very testable class (hint: you can use mock.Mock for the signals)
# post corrected solution :
# http://stackoverflow.com/questions/24820063/python-pyqt-how-to-call-a-gui-function-from-a-worker-thread
# http://stackoverflow.com/questions/6783194/background-thread-with-qthread-in-pyqt
# and thanks :-)


class MainWindow(ApplicationSession, QMainWindow):
    """
    This class is a wamp client and adds the CaptureWidget, MainSearchWidget and StatusWidget in a QTabWidget.

    This class acts as a proxy for the widgets that want to communicate with the backend because they can't have a valid
     ApplicationSession that would allow them to be a wamp client and a QWidget.
    """

    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        QMainWindow.__init__(self)

        #########
        self.capture_tab = CaptureWidget()
        self.search_tab = MainSearchWidget()
        self.status_tab = StatusWidget()

        #########
        self.statusBar()
        self.main_window_init()

    @asyncio.coroutine
    def onJoin(self, details):
        """
        Is called if the wamp router is successfully joined

        Args:
            details(class): SessionDetails
        """
        print("session ready ")
        yield from self.subscribe(self.backend_is_alive_beacon, 'com.digitize_app.backend_is_alive_beacon')
        yield from self.subscribe(self.ongoing_capture, 'com.digitize_app.ongoing_capture')
        yield from self.subscribe(self.waiting_captures, 'com.digitize_app.waiting_captures')

    @async_call
    @asyncio.coroutine
    def launch_capture(self, metadata):
        """
        Is called by the CaptureWidget and call the 'launch_capture' function in the backend

        Args:
            metadata (list): [digitise_infos, dublincore_dict]
        """

        yield from self.call('com.digitize_app.launch_capture', metadata)

    def backend_is_alive_beacon(self):
        """
        Is called when the backend send a beacon and fire the 'backend_is_alive_signal' signal in the 'capture_tab' class.
        """

        self.capture_tab.backend_is_alive_signal.emit(4000)

    def ongoing_capture(self, capture_status):
        """
        Is called whenever one of the ongoing capture has an update which happens randomly.

        Args:
            capture_status (dict): Dict that contain the following keys:
                title, year, dc:identifier, start_date, action
        """

        self.status_tab.receive_ongoing_capture_status.emit(capture_status)

    def waiting_captures(self, waiting_captures):
        """
        Is called when the backend publish a list of waiting captures

        If there is at least one capture waiting this function is called every 5 seconds.

        Args:
            waiting_captures (list): List of dicts. These dicts contain the following keys:
                dc:title, dcterms:created, dc:identifier, source
        """

        self.status_tab.receive_waiting_captures_status.emit(waiting_captures)

    def set_status_bar_message(self, message):
        """
        Args:
            message (str):
        """
        self.statusBar().showMessage(message, msecs=10000)

    def main_window_init(self):
        """
        This function init the main window

        It sets the status bar, menu bar and set the tabs class as central widget
        """

        tabs = QTabWidget()
        self.capture_tab.set_statusbar_text_signal.connect(self.set_status_bar_message)
        self.capture_tab.launch_capture_signal.connect(self.launch_capture)

        #########
        tabs.addTab(self.capture_tab, "Numérisation")
        tabs.addTab(self.search_tab, "Recherche")
        tabs.addTab(self.status_tab, "Statuts des conversions")

        #########
        self.setCentralWidget(tabs)

        #########
        self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle('Logiciel Numérisation')
        self.show()


if __name__ == '__main__':
    # this function check if the directories are writable
    startup_check()

    setproctitle.setproctitle("digitise_gui")
    QT_app = QApplication(sys.argv)

    loop = QEventLoop(QT_app)
    asyncio.set_event_loop(loop)

    runner = ApplicationRunner(url="ws://127.0.0.1:8080/ws", realm="realm1")
    runner.run(MainWindow)

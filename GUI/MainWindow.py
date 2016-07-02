import sys

from PyQt5.QtWidgets import QMainWindow, QApplication, QTabWidget

from GUI.digitise.CaptureWidget import CaptureWidget
from GUI.search.MainSearchWidget import MainSearchWidget
from GUI.status.StatusWidget import StatusWidget
import setproctitle
from backend.startup_check import startup_check

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
        self.capture_tab = CaptureWidget(parent=self)
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

        self.capture_tab.delayed_init()

        print("session ready ")
        yield from self.subscribe(self.capture_tab.backend_is_alive_beacon, 'com.digitize_app.backend_is_alive_beacon')
        yield from self.subscribe(self.status_tab.ongoing_capture_dict_receiver, 'com.digitize_app.ongoing_capture')
        yield from self.subscribe(self.status_tab.waiting_captures_table_receiver, 'com.digitize_app.waiting_captures')

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

        #########
        self.capture_tab.set_statusbar_text_signal.connect(self.set_status_bar_message)
        self.status_tab.send_enable_decklink_radio_1.connect(self.capture_tab.receive_enable_decklink_radio_1)
        self.status_tab.send_enable_decklink_radio_2.connect(self.capture_tab.receive_enable_decklink_radio_2)

        #########
        tabs.addTab(self.capture_tab, "Numérisation")
        tabs.addTab(self.search_tab, "Recherche")
        tabs.addTab(self.status_tab, "Statuts des conversions")

        #########
        self.setCentralWidget(tabs)

        #########
        self.setGeometry(300, 300, 1024, 800)
        self.setWindowTitle('Logiciel Numérisation')
        self.show()


def launch_gui():
    # this function check if the directories are writable
    startup_check()

    setproctitle.setproctitle("digitise_gui")
    QT_app = QApplication(sys.argv)

    loop = QEventLoop(QT_app)
    asyncio.set_event_loop(loop)

    runner = ApplicationRunner(url="ws://127.0.0.1:8080/ws", realm="realm1")
    runner.run(MainWindow)

if __name__ == '__main__':
    launch_gui()

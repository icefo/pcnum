import sys

from PyQt5.QtWidgets import QMainWindow, QApplication, QTabWidget

from PyQt5.QtCore import pyqtSignal

from GUI.digitise.DigitiseWidget import DigitiseWidget
from GUI.search.MainSearchWidget import MainSearchWidget
from GUI.status.StatusWidget import StatusWidget
import setproctitle
from backend.startup_check import startup_check

import functools

import asyncio
from autobahn.asyncio.wamp import ApplicationRunner
from autobahn.asyncio.wamp import ApplicationSession

from quamash import QEventLoop

# very testable class (hint: you can use mock.Mock for the signals)
# post corrected solution :
# http://stackoverflow.com/questions/24820063/python-pyqt-how-to-call-a-gui-function-from-a-worker-thread
# http://stackoverflow.com/questions/6783194/background-thread-with-qthread-in-pyqt
# and thanks :-)


def async_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        asyncio.async(func(*args, **kwargs))
    return wrapper


class MainWindow(ApplicationSession, QMainWindow):

    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        QMainWindow.__init__(self)

        self.digitise_tab = DigitiseWidget()
        self.search_tab = MainSearchWidget()
        self.status_tab = StatusWidget()

        self.statusBar()
        self.main_window_init()

    def set_status_bar_message(self, arg):
        self.statusBar().showMessage(arg, msecs=10000)

    @async_call
    @asyncio.coroutine
    def launch_capture(self, metadata):
        yield from self.call('com.digitize_app.launch_capture', metadata)

    def backend_is_alive_beacon(self):
        self.digitise_tab.backend_is_alive_signal.emit(1000000)

    def ffmpeg_supervisor_ongoing_conversion(self, report):
        print(report)

    @asyncio.coroutine
    def onJoin(self, details):
        print("session ready")
        yield from self.subscribe(self.backend_is_alive_beacon, 'com.digitize_app.backend_is_alive_beacon')
        yield from self.subscribe(self.ffmpeg_supervisor_ongoing_conversion, 'com.digitize_app.ongoing_conversion')

    def main_window_init(self):
        """
        This function init the main window
        It sets the status bar, menu bar and set the tabs class as central widget

        :return: nothing
        """
        tabs = QTabWidget()
        self.digitise_tab.set_statusbar_text_signal.connect(self.set_status_bar_message)
        self.digitise_tab.launch_digitise_signal.connect(self.launch_capture)
        tabs.addTab(self.digitise_tab, "Numérisation")

        tabs.addTab(self.search_tab, "Recherche")

        tabs.addTab(self.status_tab, "Statuts des conversions")

        self.setCentralWidget(tabs)

        self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle('Logiciel Numérisation')
        self.show()


if __name__ == '__main__':
    # this function check that the directories are writable
    startup_check()

    setproctitle.setproctitle("digitise_gui")
    QT_app = QApplication(sys.argv)

    loop = QEventLoop(QT_app)
    asyncio.set_event_loop(loop)

    runner = ApplicationRunner(url="ws://127.0.0.1:8080/ws", realm="realm1")
    runner.run(MainWindow)

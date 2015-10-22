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
    def wrapper(*args, **kw):
        res = func(*args, **kw)
        asyncio.async(res)
    return wrapper

class MainWindow(ApplicationSession, QMainWindow):

    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        QMainWindow.__init__(self)

        self.statusBar()

        self.main_window_init()

    def tabs_init(self):
        tabs = QTabWidget()
        digitise_tab = DigitiseWidget()
        digitise_tab.set_statusbar_text_signal.connect(self.set_status_bar_message)
        digitise_tab.launch_digitise_signal.connect(self.launch_capture)
        tabs.addTab(digitise_tab, "Numérisation")

        search_tab = MainSearchWidget()
        tabs.addTab(search_tab, "Recherche")

        status_tab = StatusWidget()
        tabs.addTab(status_tab, "Statuts des conversions")
        return tabs

    def set_status_bar_message(self, arg):
        self.statusBar().showMessage(arg, msecs=10000)

    @async_call
    @asyncio.coroutine
    def launch_capture(self, metadata):
        result = yield from self.call('com.digitize_app.launch_capture', metadata)
        # print("I called baby ! ", result)
        # self.the_widget.addition_result_signal.emit(str(result))

    def main_window_init(self):
        """
        This function init the main window
        It sets the status bar, menu bar and set the tabs class as central widget

        :return: nothing
        """
        tabs = self.tabs_init()
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

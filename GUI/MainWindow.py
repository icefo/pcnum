import sys

from PyQt5.QtWidgets import QMainWindow, QApplication, QTabWidget

from PyQt5 import QtCore

from GUI.digitise.DigitiseWidget import DigitiseWidget
from GUI.search.MainSearchWidget import MainSearchWidget
from GUI.status.StatusWidget import StatusWidget
import setproctitle
from backend.startup_check import startup_check

# very testable class (hint: you can use mock.Mock for the signals)
# post corrected solution :
# http://stackoverflow.com/questions/24820063/python-pyqt-how-to-call-a-gui-function-from-a-worker-thread
# http://stackoverflow.com/questions/6783194/background-thread-with-qthread-in-pyqt
# and thanks :-)


class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()

        #########
        self.bar_statusbar = self.statusBar()

        #########
        self.main_window_init()

    def main_window_init(self):
        """
        This function init the main window
        It sets the status bar, menu bar and set the Tabs class as the central widget

        :return: nothing
        """
        tabs = Tabs(self)
        tabs.set_statusbar_text_2.connect(self.set_status_bar_message)
        self.setCentralWidget(tabs)

        #########
        self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle('Logiciel Numérisation')
        self.show()

    def set_status_bar_message(self, arg):
        print("heyy message")
        self.bar_statusbar.showMessage(arg, msecs=10000)


class Tabs(QTabWidget):

    set_statusbar_text_2 = QtCore.pyqtSignal([str])

    def __init__(self, parent):
        super().__init__(parent)
        self.tabs_init()

    def tabs_init(self):
        digitise_tab = DigitiseWidget()
        digitise_tab.set_statusbar_text_1.connect(self.set_statusbar_text_2)
        self.addTab(digitise_tab, "Numérisation")

        #########
        search_tab = MainSearchWidget()
        self.addTab(search_tab, "Recherche")

        #########
        status_tab = StatusWidget()
        self.addTab(status_tab, "Statuts des conversions")


if __name__ == '__main__':
    # this function check that the mandatory modules are importable and the directories writable
    startup_check()

    setproctitle.setproctitle("digitise_gui")
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())

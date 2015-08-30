import sys

from PyQt5.QtWidgets import QMainWindow, QAction, QApplication, QTabWidget

from PyQt5.QtGui import QIcon

from PyQt5 import QtCore

from GUI.digitise.DigitiseWidget import DigitiseWidget
from GUI.search.MainSearchWidget import MainSearchWidget
from GUI.status.StatusWidget import StatusWidget
import setproctitle

# very testable class (hint: you can use mock.Mock for the signals)
# post corrected solution :
# http://stackoverflow.com/questions/24820063/python-pyqt-how-to-call-a-gui-function-from-a-worker-thread
# http://stackoverflow.com/questions/6783194/background-thread-with-qthread-in-pyqt
# and thanks :-)


class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        self.init_main_window()

    def init_main_window(self):
        """
        this function init the main window
        it set the status bar, menu bar and set the Tabs class as the central widget

        :return: nothing
        """

        exitAction = QAction(QIcon('exit.png'), 'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        statusbar = self.statusBar()


        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)

        #toolbar = self.addToolBar('Exit')
        #toolbar.addAction(exitAction)

        # font = QFont(QFont().defaultFamily(), 12)
        # self.setFont(font)
        tabs = Tabs(self)
        tabs.set_statusbar_text_2.connect(statusbar.showMessage)
        self.setCentralWidget(tabs)
        
        self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle('Logiciel Numérisation')
        self.show()


class Tabs(QTabWidget):

    set_statusbar_text_2 = QtCore.pyqtSignal([str])

    def __init__(self, parent):
        super().__init__(parent)
        self.tabs_init()

    def tabs_init(self):
        digitise_tab = DigitiseWidget()
        digitise_tab.set_statusbar_text_1.connect(self.set_statusbar_text_2)
        self.addTab(digitise_tab, "Numérisation")

        search_tab = MainSearchWidget()
        self.addTab(search_tab, "Recherche")

        status_tab = StatusWidget()
        self.addTab(status_tab, "Status")


if __name__ == '__main__':
    setproctitle.setproctitle("digitize_gui")
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())

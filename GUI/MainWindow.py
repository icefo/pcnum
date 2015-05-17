import sys
from PyQt5.QtWidgets import QMainWindow, QAction, QApplication, QTabWidget
from PyQt5.QtGui import QIcon, QFont
from GUI.DigitiseTab import DigitiseTab
from GUI.SearchTab import SearchTab
# very testable class (hint: you can use mock.Mock for the signals)
# post corrected solution :
# http://stackoverflow.com/questions/24820063/python-pyqt-how-to-call-a-gui-function-from-a-worker-thread
# http://stackoverflow.com/questions/6783194/background-thread-with-qthread-in-pyqt
# and thanks :-)
# Ecrire des securitées qui disent si le backend tourne pas, bloquer le bouton pour eviter de flooder le backend
# liberer le bouton quand le thread est terminé
# Utiliser plusieurs fois la même classe ou réinitialer a chaque fois + une classe par fonction ? Nope...


class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        self.init_ui()

    def init_ui(self):
        
        tabs = Tabs(self)
        self.setCentralWidget(tabs)

        exitAction = QAction(QIcon('exit.png'), 'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        self.statusBar()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)

        #toolbar = self.addToolBar('Exit')
        #toolbar.addAction(exitAction)
        
        self.setGeometry(300, 300, 500, 600)
        self.setWindowTitle('Main window')    
        self.show()


class Tabs(QTabWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.DigitiseTab = DigitiseTab()
        self.addTab(self.DigitiseTab, "heyyy macalenaaaa")

        self.SearchTab = SearchTab()
        self.addTab(self.SearchTab, "heyyy ceeepalaaaa")


if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())
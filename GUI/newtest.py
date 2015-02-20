import sys
from PyQt5.QtWidgets import (QMainWindow, QAction, QApplication, QTabWidget, QWidget,
                             QHeaderView, QGridLayout,
                             QRadioButton, QTextEdit, QLabel, QLineEdit, QCheckBox, QTableWidget, QComboBox, QPushButton)
from PyQt5.QtGui import QIcon
# from functools import partial


class Example(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        self.initUI()
        
        
    def initUI(self):               
        
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

        toolbar = self.addToolBar('Exit')
        toolbar.addAction(exitAction)
        
        self.setGeometry(300, 300, 500, 600)
        self.setWindowTitle('Main window')    
        self.show()


class Tabs(QTabWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.tab1 = Tab1()
        self.addTab(self.tab1, "heyyy")




class Tab1(QWidget):
    def __init__(self):
        super().__init__()

        self.table = None
        self.tab1_init()
        #print(self.truc)

    def tab1_init(self):
        grid = QGridLayout()

        # Decklink card choice
        decklink_label = QLabel("Choisissez la carte utilisée pour l'enregistrement")
        decklink_radio_1 = QRadioButton("Decklink 1")
        decklink_radio_2 = QRadioButton("Decklink 2")
        grid.addWidget(decklink_label, 0, 0)
        grid.addWidget(decklink_radio_1, 0, 1)
        grid.addWidget(decklink_radio_2, 0, 2)
        # Si la carte est dejà utilisée empêcher une autre numérisation de commencer avec
        # Button.setEnabled(False) avec une demande sur le socket du conversion deamon

        # Compressed files to create
        compressed_file_label = QLabel("Choisissez le format des fichiers compressés à créer")
        compressed_file_h264 = QCheckBox("H264")
        compressed_file_h265 = QCheckBox("H265")
        grid.addWidget(compressed_file_label, 1, 0)
        grid.addWidget(compressed_file_h264, 1, 1)
        grid.addWidget(compressed_file_h265, 1, 2)

        # Package mediatheque
        package_mediatheque = QCheckBox("Créer package mediatheque")
        grid.addWidget(package_mediatheque, 2, 0)

        ###############

        # Table
        self.table = QTableWidget()
        self.table.setRowCount(0)
        self.table.setColumnCount(3)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.resizeRowsToContents()

        grid.addWidget(self.table, 3, 0, 5,2)

        new_table_row = QPushButton("Nouveau")
        grid.addWidget(new_table_row, 3, 3)

        # here happen the magic :

        def addrow():
            row_count = self.table.rowCount()
            print(row_count)
            self.table.insertRow(row_count)
            combo_list = ["bla", "blu", "bli", "blop"]
            self.table.setCellWidget(row_count, 0, QComboBox())
            self.table.cellWidget(row_count, 0).addItems(combo_list)
            self.table.setCellWidget(row_count, 1, QTextEdit())
            self.table.setCellWidget(row_count, 2, QPushButton("Delete"))
            self.table.cellWidget(row_count, 2).clicked.connect(self.delete_table_row)
            # self.table.cellClicked.connect(self.cell_was_clicked)


        new_table_row.clicked.connect(addrow)

        self.setLayout(grid)

    def delete_table_row(self):
        sender = self.sender()
        index = self.table.indexAt(sender.pos())
        if index.isValid():
            print(index.row(), index.column())
            self.table.removeRow(index.row())





    def tab2_init(self):

        self.addTab(self.tab2, "huyyy")



if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
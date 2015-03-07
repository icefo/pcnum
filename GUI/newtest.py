import sys
from PyQt5.QtWidgets import (QMainWindow, QAction, QApplication, QTabWidget, QWidget,
                             QHeaderView, QGridLayout,
                             QRadioButton, QTextEdit, QLabel, QLineEdit, QCheckBox, QTableWidget, QComboBox, QPushButton)
from PyQt5.QtGui import QIcon, QFont
# from functools import partial
# pas besoin finalement mais a garder ca peut etre utile
# partial( self.myFunction, myArgument='something')


class Example(QMainWindow):
    
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
        self.tab1 = Tab1()
        self.addTab(self.tab1, "heyyy macalenaaaa")

        self.tab2 = Tab2()
        self.addTab(self.tab2, "heyyy ceeepalaaaa")


class Tab1(QWidget):
    def __init__(self):
        # Initialize the parent class QWidget
        super().__init__()

        #########

        self.decklink_label = QLabel("Choisissez la carte utilisée pour l'enregistrement")
        self.decklink_radio_1 = QRadioButton("Decklink 1")
        self.decklink_radio_2 = QRadioButton("Decklink 2")

        #########

        self.compressed_file_label = QLabel("Choisissez le format des fichiers compressés à créer")
        self.compressed_file_h264 = QCheckBox("H264")
        self.compressed_file_h265 = QCheckBox("H265")

        #########

        self.package_mediatheque = QCheckBox("Créer package mediatheque")

        #########

        self.table = QTableWidget()
        self.table_font = QFont(QFont().defaultFamily(), 12)
        self.new_table_row = QPushButton("Nouveau")
        self.launch_digitise = QPushButton("Numériser")

        self.tab_init()

    def delete_table_row(self):
        sender = self.sender()
        index = self.table.indexAt(sender.pos())
        if index.isValid():
            self.table.removeRow(index.row())

    def combobox_changed(self, text):
        sender = self.sender()
        index = self.table.indexAt(sender.pos())
        if index.isValid():
            row = index.row()
            if text == "dc:description":
                print(self.table.rowHeight(row))
                self.table.removeCellWidget(row, 1)
                self.table.setCellWidget(row, 1, QTextEdit())
                self.table.setRowHeight(row, 60)
            else:
                self.table.removeCellWidget(row, 1)
                self.table.setCellWidget(row, 1, QLineEdit())
                self.table.setRowHeight(row, 30)

    def add_row(self):
        combo_list = [
            'dc:contributor', 'dc:coverage', 'dc:creator', 'dc:date', 'dc:description', 'dc:format',
            'dc:identifier', 'dc:language', 'dc:publisher', 'dc:relation', 'dc:rights',
            'dc:source', 'dc:subject', 'dc:title', 'dc:type', 'dcterms:abstract',
            'dcterms:accepted', 'dcterms:accessRights', 'dcterms:alternative', 'dcterms:audience', 'dcterms:available',
            'dcterms:bibliographicCitation', 'dcterms:conformsTo', 'dcterms:copyrighted', 'dcterms:created', 'dcterms:educationLevel',
            'dcterms:extent', 'dcterms:hasFormat', 'dcterms:hasPart', 'dcterms:hasVersion', 'dcterms:isFormatOf',
            'dcterms:isPartOf', 'dcterms:isReferencedBy', 'dcterms:isReplacedBy', 'dcterms:isRequiredBy', 'dcterms:isVersionOf',
            'dcterms:issued', 'dcterms:mediator', 'dcterms:medium', 'dcterms:modified', 'dcterms:references',
            'dcterms:replaces', 'dcterms:requires', 'dcterms:spatial', 'dcterms:submitted', 'dcterms:tableOfContents',
            'dcterms:temporal', 'dcterms:valid'
        ]
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        self.table.setCellWidget(row_count, 0, QComboBox())
        self.table.cellWidget(row_count, 0).addItems(combo_list)
        self.table.cellWidget(row_count, 0).activated[str].connect(self.combobox_changed)
        self.table.setCellWidget(row_count, 1, QLineEdit())
        self.table.setCellWidget(row_count, 2, QPushButton("Delete"))
        self.table.cellWidget(row_count, 2).clicked.connect(self.delete_table_row)

    def digitise(self):
        # utiliser les sockets unix pour passer les dicos au conversion_deamon
        # http://stackoverflow.com/questions/6920858/interprocess-communication-in-python
        # https://docs.python.org/3/library/multiprocessing.html#multiprocessing-listeners-clients

        # Handle the dublincore metadata
        dublincore_dict = {}
        for row in range(self.table.rowCount()):
            combobox_text = self.table.cellWidget(row, 0).currentText()
            try:
                text_widget_value = self.table.cellWidget(row, 1).displayText()
            except AttributeError:
                text_widget_value = self.table.cellWidget(row, 1).toPlainText()

            if text_widget_value is not "":
                try:
                    dublincore_dict[combobox_text].append(text_widget_value)
                except KeyError:
                    dublincore_dict[combobox_text] = [text_widget_value]
        print(dublincore_dict)

        # Handle the other stuff
        digitise_infos = {}
        if self.decklink_radio_1.isChecked():
            digitise_infos["decklink_card"] = "1"
        else:
            digitise_infos["decklink_card"] = "2"
        digitise_infos["H264"] = self.compressed_file_h264.isChecked()
        digitise_infos["H265"] = self.compressed_file_h265.isChecked()
        digitise_infos["package_mediatheque"] = self.package_mediatheque.isChecked()
        print(digitise_infos)

    def tab_init(self):
        grid = QGridLayout()

        # Decklink card choice
        grid.addWidget(self.decklink_label, 0, 0)
        grid.addWidget(self.decklink_radio_1, 0, 1)
        grid.addWidget(self.decklink_radio_2, 0, 2)
        # Si la carte est dejà utilisée empêcher une autre numérisation de commencer avec
        # Button.setEnabled(False) avec une demande sur le socket du conversion deamon

        # Compressed files to create
        grid.addWidget(self.compressed_file_label, 1, 0)
        grid.addWidget(self.compressed_file_h264, 1, 1)
        grid.addWidget(self.compressed_file_h265, 1, 2)

        # Package mediatheque
        grid.addWidget(self.package_mediatheque, 2, 0)

        ###############

        # Table
        self.table.setRowCount(0)
        self.table.setColumnCount(3)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 170)
        self.table.setFont(self.table_font)
        grid.addWidget(self.table, 3, 0, 5, 2)

        grid.addWidget(self.new_table_row, 3, 3)

        grid.addWidget(self.launch_digitise, 5, 3)
        self.launch_digitise.clicked.connect(self.digitise)

        self.new_table_row.clicked.connect(self.add_row)

        # set the layout on the QWidget instantiated class
        self.setLayout(grid)


class Tab2(QWidget):
    def __init__(self):
        # Initialize the parent class QWidget
        super().__init__()

        #########

        self.textedit = QTextEdit()

        self.tab_init()

    def tab_init(self):
        grid = QGridLayout()

        grid.addWidget(self.textedit, 0, 0)

        self.setLayout(grid)





if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
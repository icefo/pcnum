import sys
from PyQt5.QtWidgets import (QMainWindow, QAction, QApplication, QTabWidget, QWidget,
                             QHeaderView, QGridLayout,
                             QRadioButton, QTextEdit, QLabel, QLineEdit, QCheckBox, QTableWidget, QComboBox, QPushButton)
from PyQt5.QtGui import QIcon, QFont
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
        self.addTab(self.tab1, "heyyy macalenaaaa")




class Tab1(QWidget):
    def __init__(self):
        super().__init__()

        self.table = None
        self.tab1_init()

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
        self.table.setColumnWidth(0, 170)
        table_font = QFont(QFont().defaultFamily(), 12)
        self.table.setFont(table_font)


        grid.addWidget(self.table, 3, 0, 5, 2)

        new_table_row = QPushButton("Nouveau")
        grid.addWidget(new_table_row, 3, 3)

        def digitise():
            # Handle the dublincore metadata
            dublincore_dict = {}
            for row in range(self.table.rowCount()):
                combobox_text = self.table.cellWidget(row, 0).currentText()
                try:
                    text_widget_value = self.table.cellWidget(row, 1).displayText()
                except AttributeError:
                    text_widget_value = self.table.cellWidget(row, 1).toPlainText()

                try:
                    dublincore_dict[combobox_text].append(text_widget_value)
                except KeyError:
                    dublincore_dict[combobox_text] = [text_widget_value]
            print(dublincore_dict)

            # Handle the other stuff
            digitise_infos = {}
            if decklink_radio_1.isChecked():
                digitise_infos["decklink_card"] = "1"
            else:
                digitise_infos["decklink_card"] = "2"
            digitise_infos["H264"] = compressed_file_h264.isChecked()
            digitise_infos["H265"] = compressed_file_h265.isChecked()
            digitise_infos["package_mediatheque"] = package_mediatheque.isChecked()
            print(digitise_infos)


        launch_digitise = QPushButton("Numériser")
        grid.addWidget(launch_digitise, 5, 3)
        launch_digitise.clicked.connect(digitise)

        # here happen the magic :

        def addrow():
            row_count = self.table.rowCount()
            self.table.insertRow(row_count)
            combo_list = ['dc:contributor', 'dc:coverage', 'dc:creator', 'dc:date', 'dc:description', 'dc:format', 'dc:identifier', 'dc:language', 'dc:publisher', 'dc:relation', 'dc:rights', 'dc:source', 'dc:subject', 'dc:title', 'dc:type', 'dcterms:abstract', 'dcterms:accepted', 'dcterms:accessRights', 'dcterms:alternative', 'dcterms:audience', 'dcterms:available', 'dcterms:bibliographicCitation', 'dcterms:conformsTo', 'dcterms:copyrighted', 'dcterms:created', 'dcterms:educationLevel', 'dcterms:extent', 'dcterms:hasFormat', 'dcterms:hasPart', 'dcterms:hasVersion', 'dcterms:isFormatOf', 'dcterms:isPartOf', 'dcterms:isReferencedBy', 'dcterms:isReplacedBy', 'dcterms:isRequiredBy', 'dcterms:isVersionOf', 'dcterms:issued', 'dcterms:mediator', 'dcterms:medium', 'dcterms:modified', 'dcterms:references', 'dcterms:replaces', 'dcterms:requires', 'dcterms:spatial', 'dcterms:submitted', 'dcterms:tableOfContents', 'dcterms:temporal', 'dcterms:valid']
            self.table.setCellWidget(row_count, 0, QComboBox())
            self.table.cellWidget(row_count, 0).addItems(combo_list)
            self.table.cellWidget(row_count, 0).activated[str].connect(self.combobox_changed)
            self.table.setCellWidget(row_count, 1, QLineEdit())
            self.table.setCellWidget(row_count, 2, QPushButton("Delete"))
            self.table.cellWidget(row_count, 2).clicked.connect(self.delete_table_row)


        new_table_row.clicked.connect(addrow)

        self.setLayout(grid)





    def tab2_init(self):

        self.addTab(self.tab2, "huyyy")



if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
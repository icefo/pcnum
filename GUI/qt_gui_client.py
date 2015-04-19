import sys
from PyQt5 import QtCore
from PyQt5.QtCore import QDateTime
import xmlrpc.client
from PyQt5.QtWidgets import (QMainWindow, QAction, QApplication, QTabWidget, QWidget,
                             QHeaderView, QGridLayout,
                             QRadioButton, QTextEdit, QLabel, QLineEdit, QCheckBox, QTableWidget, QComboBox, QPushButton, QCalendarWidget)
from PyQt5.QtGui import QIcon, QFont
from functools import partial
# pas besoin finalement mais a garder ca peut etre utile
#partial( self.myFunction, myArgument='something')


# very testable class (hint: you can use mock.Mock for the signals)
# post corrected solution :
# http://stackoverflow.com/questions/24820063/python-pyqt-how-to-call-a-gui-function-from-a-worker-thread
# http://stackoverflow.com/questions/6783194/background-thread-with-qthread-in-pyqt
# and thanks :-)
# Ecrire des securitées qui disent si le backend tourne pas, bloquer le bouton pour eviter de flooder le backend
# liberer le bouton quand le thread est terminé
# Utiliser plusieurs fois la même classe ou réinitialer a chaque fois + une classe par fonction ? Nope...


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


class Tab1Worker(QtCore.QObject):

    client = xmlrpc.client.ServerProxy('http://localhost:8000')

    launch_digitise_done = QtCore.pyqtSignal([str])
    finished = QtCore.pyqtSignal()
    print("Tab1 Worker init")

    def __init__(self):
        super().__init__()

    def digitise(self, command=None):
        print("bridge digitize()")
        return_status = self.client.launch_digitise(command)
        self.launch_digitise_done.emit(return_status)
        self.finished.emit()


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
        self.result_digitise = QLabel("et patapon")

        #########

        self.workerThread_digitise = None
        self.workerObject_digitise = None

        #########

        self.tab_init()

    def tab1_worker(self, action, parameter):

        if action == "digitise":
            self.workerThread_digitise = QtCore.QThread()
            self.workerObject_digitise = Tab1Worker()
            self.workerObject_digitise.moveToThread(self.workerThread_digitise)

            self.launch_digitise.setEnabled(False)

            self.workerThread_digitise.started.connect(partial(self.workerObject_digitise.digitise, command=parameter))
            self.workerObject_digitise.finished.connect(self.workerThread_digitise.quit)
            self.workerObject_digitise.finished.connect(partial(self.launch_digitise.setEnabled, True))
            self.workerObject_digitise.launch_digitise_done.connect(self.result_digitise.setText)

            self.workerThread_digitise.start()

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
                self.table.removeCellWidget(row, 1)
                self.table.setCellWidget(row, 1, QTextEdit())
                self.table.setRowHeight(row, 60)
            elif text == "dc:date":
                self.table.removeCellWidget(row, 1)
                self.table.setCellWidget(row, 1, QCalendarWidget())
                self.table.setRowHeight(row, 240)
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

        # Handle the dublincore metadata
        dublincore_dict = {}
        for row in range(self.table.rowCount()):
            combobox_text = self.table.cellWidget(row, 0).currentText()
            widget_type = self.table.cellWidget(row, 1).metaObject().className()
            if widget_type == "QLineEdit":
                widget_text_value = self.table.cellWidget(row, 1).displayText()
            elif widget_type == "QTextEdit":
                widget_text_value = self.table.cellWidget(row, 1).toPlainText()
            elif widget_type == "QCalendarWidget":
                widget_text_value = self.table.cellWidget(row, 1).selectedDate().toPyDate().strftime("%d %b %Y")

            if widget_text_value is not "":
                try:
                    dublincore_dict[combobox_text].append(widget_text_value)
                except KeyError:
                    dublincore_dict[combobox_text] = [widget_text_value]

        # Handle the other infos
        digitise_infos = {}
        if self.decklink_radio_1.isChecked():
            digitise_infos["decklink_card"] = "1"
        else:
            digitise_infos["decklink_card"] = "2"
        digitise_infos["H264"] = self.compressed_file_h264.isChecked()
        digitise_infos["H265"] = self.compressed_file_h265.isChecked()
        digitise_infos["package_mediatheque"] = self.package_mediatheque.isChecked()

        self.result_digitise.setText("Eyy digitapon")

        to_be_send = [digitise_infos, dublincore_dict]
        print(to_be_send)

        self.tab1_worker(action="digitise", parameter=to_be_send)

    def tab_init(self):
        grid = QGridLayout()

        # Decklink card choice
        grid.addWidget(self.decklink_label, 0, 0)
        grid.addWidget(self.decklink_radio_1, 0, 1)
        grid.addWidget(self.decklink_radio_2, 0, 2)

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

        grid.addWidget(self.result_digitise, 6, 3)

        self.new_table_row.clicked.connect(self.add_row)

        ###############

        self.launch_digitise.clicked.connect(self.digitise)

        # set the layout on the QWidget instantiated class
        self.setLayout(grid)


class Tab2Worker(QtCore.QObject):

    client = xmlrpc.client.ServerProxy('http://localhost:8000')

    search_done = QtCore.pyqtSignal([str])
    finished = QtCore.pyqtSignal()
    print("Tab2 worker init")

    def __init__(self):
        super().__init__()

    def search(self, command):
        print("bridge search()")
        return_payload = self.client.search(command)
        print(return_payload)
        self.search_done.emit(return_payload)
        self.finished.emit()


class Tab2(QWidget):
    def __init__(self):
        # Initialize the parent class QWidget
        super().__init__()

        #########

        self.table = QTableWidget()
        self.table_font = QFont(QFont().defaultFamily(), 12)
        self.add_row_button = QPushButton("ajouter")
        self.search_button = QPushButton("rechercher")

        #########

        self.workerThread_search = None
        self.workerObject_search = None

        self.tab_init()

    def delete_table_row(self):
        sender = self.sender()
        index = self.table.indexAt(sender.pos())
        if index.isValid():
            self.table.removeRow(index.row())

    def dc_combobox_changed(self, text):
        sender = self.sender()
        index = self.table.indexAt(sender.pos())
        logic_year_list = ["equal", "greater", "inferior"]
        logic_text_list = ["equal", "contain"]
        if index.isValid():
            row = index.row()
            if text == "dc:description":
                # print(self.table.rowHeight(row))
                self.table.removeCellWidget(row, 2)
                self.table.setCellWidget(row, 2, QTextEdit())
                self.table.setRowHeight(row, 60)
            else:
                self.table.removeCellWidget(row, 2)
                self.table.setCellWidget(row, 2, QLineEdit())
                self.table.setRowHeight(row, 30)

            if text == "dc:date":
                self.table.removeCellWidget(row, 1)
                self.table.setCellWidget(row, 1, QComboBox())
                self.table.cellWidget(row, 1).addItems(logic_year_list)
                self.table.removeCellWidget(row, 2)
                self.table.setCellWidget(row, 2, QCalendarWidget())
                self.table.setRowHeight(row, 240)
            else:
                self.table.removeCellWidget(row, 1)
                self.table.setCellWidget(row, 1, QComboBox())
                self.table.cellWidget(row, 1).addItems(logic_text_list)

    def add_row(self):
        dc_list = [
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
        logic_text_list = ["equal", "contain"]

        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        self.table.setCellWidget(row_count, 0, QComboBox())
        self.table.cellWidget(row_count, 0).addItems(dc_list)
        self.table.cellWidget(row_count, 0).activated[str].connect(self.dc_combobox_changed)

        self.table.setCellWidget(row_count, 1, QComboBox())
        self.table.cellWidget(row_count, 1).addItems(logic_text_list)

        self.table.setCellWidget(row_count, 2, QLineEdit())
        self.table.setCellWidget(row_count, 3, QPushButton("Delete"))
        self.table.cellWidget(row_count, 3).clicked.connect(self.delete_table_row)

    def tab2_worker(self, action, parameter):

        if action == "search":
            self.workerThread_search = QtCore.QThread()
            self.workerObject_search = Tab2Worker()
            self.workerObject_search.moveToThread(self.workerThread_search)

            self.search_button.setEnabled(False)

            self.workerThread_search.started.connect(partial(self.workerObject_search.search, command=parameter))
            self.workerObject_search.finished.connect(self.workerThread_search.quit)
            self.workerObject_search.finished.connect(partial(self.search_button.setEnabled, True))
            # self.workerObject_search.launch_digitise_done.connect(self.result_digitise.setText)

            self.workerThread_search.start()

    def search(self):
        # Handle the dublincore metadata
        search_dict = {}
        for row in range(self.table.rowCount()):
            dc_combobox_text = self.table.cellWidget(row, 0).currentText()
            data_widget_type = self.table.cellWidget(row, 2).metaObject().className()
            if data_widget_type == "QLineEdit":
                data_widget_text_value = self.table.cellWidget(row, 2).displayText()
            elif data_widget_type == "QTextEdit":
                data_widget_text_value = self.table.cellWidget(row, 2).toPlainText()
            elif data_widget_type == "QCalendarWidget":
                data_widget_text_value = self.table.cellWidget(row, 2).selectedDate().toPyDate().strftime("%d %b %Y")
            query_type = self.table.cellWidget(row, 1).currentText()

            if data_widget_text_value is not "":
                try:
                    search_dict[dc_combobox_text][query_type].append(data_widget_text_value)
                except KeyError:
                    try:
                        search_dict[dc_combobox_text][query_type] = [data_widget_text_value]
                    except KeyError:
                        search_dict[dc_combobox_text] = {query_type: [data_widget_text_value]}

        print(search_dict)
        self.tab2_worker(action="search", parameter=search_dict)

    def tab_init(self):
        grid = QGridLayout()

        # Table
        self.table.setRowCount(0)
        self.table.setColumnCount(4)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 170)
        self.table.setFont(self.table_font)
        self.add_row_button.clicked.connect(self.add_row)
        self.search_button.clicked.connect(self.search)

        grid.addWidget(self.table, 0, 0, 3, 3)
        grid.addWidget(self.add_row_button, 0, 4)
        grid.addWidget(self.search_button, 4, 4)

        self.setLayout(grid)





if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
__author__ = 'adrien'

from PyQt5 import QtCore
from PyQt5.QtCore import QDateTime
import xmlrpc.client
from PyQt5.QtWidgets import (QMainWindow, QAction, QApplication, QTabWidget, QWidget,
                             QHeaderView, QGridLayout,
                             QRadioButton, QTextEdit, QLabel, QLineEdit, QCheckBox, QTableWidget, QComboBox, QPushButton, QCalendarWidget)
from PyQt5.QtGui import QIcon, QFont
from collections import OrderedDict

from functools import partial


class DigitiseTabWorker(QtCore.QObject):

    client = xmlrpc.client.ServerProxy('http://localhost:8000')

    launch_digitise_done = QtCore.pyqtSignal([str])
    finished = QtCore.pyqtSignal()
    print("DigitiseTab Worker init")

    def __init__(self):
        super().__init__()

    def digitise(self, command=None):
        print("bridge digitize()")
        return_status = self.client.launch_digitise(command)
        self.launch_digitise_done.emit(return_status)
        self.finished.emit()


class DigitiseTab(QWidget):
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

        self.digitise_table = QTableWidget()
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
            self.workerObject_digitise = DigitiseTabWorker()
            self.workerObject_digitise.moveToThread(self.workerThread_digitise)

            self.launch_digitise.setEnabled(False)

            self.workerThread_digitise.started.connect(partial(self.workerObject_digitise.digitise, command=parameter))
            self.workerObject_digitise.finished.connect(self.workerThread_digitise.quit)
            self.workerObject_digitise.finished.connect(partial(self.launch_digitise.setEnabled, True))
            self.workerObject_digitise.launch_digitise_done.connect(self.result_digitise.setText)

            self.workerThread_digitise.start()

    def delete_table_row(self):
        sender = self.sender()
        index = self.digitise_table.indexAt(sender.pos())
        if index.isValid():
            self.digitise_table.removeRow(index.row())

    def combobox_changed(self, text):
        sender = self.sender()
        index = self.digitise_table.indexAt(sender.pos())
        if index.isValid():
            row = index.row()
            if text == "dc:description":
                self.digitise_table.removeCellWidget(row, 1)
                self.digitise_table.setCellWidget(row, 1, QTextEdit())
                self.digitise_table.setRowHeight(row, 60)
            elif text == "dcterms:created":
                self.digitise_table.removeCellWidget(row, 1)
                self.digitise_table.setCellWidget(row, 1, QLineEdit())
                self.digitise_table.cellWidget(row, 1).setInputMask("0000")
                self.digitise_table.setRowHeight(row, 30)
            elif text == "durée":
                self.digitise_table.removeCellWidget(row, 1)
                self.digitise_table.setCellWidget(row, 1, QLineEdit())
                self.digitise_table.setRowHeight(row, 30)
                self.digitise_table.cellWidget(row, 1).setInputMask("000")
            else:
                self.digitise_table.removeCellWidget(row, 1)
                self.digitise_table.setCellWidget(row, 1, QLineEdit())
                self.digitise_table.setRowHeight(row, 30)

    def add_row(self):

        dc_data = OrderedDict()
        dc_data['dc:contributor'] = "entrer le nom des personnes ayant contribués au film"
        dc_data['dc:creator'] = "maison d'édition, scénariste ou maitre de tournage"
        dc_data['dc:description'] = "Description générale de la ressource"
        dc_data['dc:language'] = "langue de la vidéo"
        dc_data['dc:publisher'] = "entreprise qui publié le film, par exemple sony pictures"
        dc_data['dc:subject'] = "thème du film: horreur, action, histoire d'amour..."
        dc_data['dc:title'] = "titre du film"
        dc_data['dcterms:abstract'] = "résumé conci du film"
        dc_data['dcterms:isPartOf'] = "remplir si le film fait parti d'un ensemble, comme star wars"
        dc_data['dcterms:tableOfContents'] = "remplir si le film se divise en parties"
        dc_data['dcterms:created'] = "année de sortie du film"
        dc_data['durée'] = "durée du film en minutes"

        row_count = self.digitise_table.rowCount()
        self.digitise_table.insertRow(row_count)
        self.digitise_table.setCellWidget(row_count, 0, QComboBox())

        count = 0
        for dc_key, dc_tooltip in dc_data.items():
            self.digitise_table.cellWidget(row_count, 0).addItem(dc_key)
            self.digitise_table.cellWidget(row_count, 0).setItemData(count, dc_tooltip, QtCore.Qt.ToolTipRole)
            count += 1

        self.digitise_table.cellWidget(row_count, 0).activated[str].connect(self.combobox_changed)
        self.digitise_table.setCellWidget(row_count, 1, QLineEdit())
        self.digitise_table.setCellWidget(row_count, 2, QPushButton("Delete"))
        self.digitise_table.cellWidget(row_count, 2).clicked.connect(self.delete_table_row)

    def digitise(self):

        # Handle the dublincore metadata
        # dc:rights = usage libre pour l'éducation
        # dc:source = VHS
        # dc:type = "image"
        # dcterms:modified = date de la numérisation
        # dc:identifier = id incremental pour chaque VHS
        # dc:format = {"size_ratio": "4/3", "duration": temps}

        dublincore_dict = {}
        for row in range(self.digitise_table.rowCount()):
            combobox_text = self.digitise_table.cellWidget(row, 0).currentText()
            widget_type = self.digitise_table.cellWidget(row, 1).metaObject().className()
            if widget_type == "QLineEdit":
                widget_text_value = self.digitise_table.cellWidget(row, 1).displayText()
            elif widget_type == "QTextEdit":
                widget_text_value = self.digitise_table.cellWidget(row, 1).toPlainText()
            elif widget_type == "QCalendarWidget":
                widget_text_value = self.digitise_table.cellWidget(row, 1).selectedDate().toPyDate().strftime("%d %b %Y")

            if widget_text_value is not "":
                if combobox_text == "durée":
                    dublincore_dict["format"] = {"size_ratio": "4/3", "duration": int(widget_text_value)}
                elif combobox_text == "dcterms:created":
                    dublincore_dict["dcterms:created"] = int(widget_text_value)
                else:
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
        self.digitise_table.setRowCount(0)
        self.digitise_table.setColumnCount(3)
        self.digitise_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.digitise_table.setColumnWidth(0, 170)
        self.digitise_table.setFont(self.table_font)
        grid.addWidget(self.digitise_table, 3, 0, 5, 2)

        grid.addWidget(self.new_table_row, 3, 3)

        grid.addWidget(self.launch_digitise, 5, 3)

        grid.addWidget(self.result_digitise, 6, 3)

        self.new_table_row.clicked.connect(self.add_row)

        ###############

        self.launch_digitise.clicked.connect(self.digitise)

        # set the layout on the QWidget instantiated class
        self.setLayout(grid)
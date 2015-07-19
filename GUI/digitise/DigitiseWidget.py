__author__ = 'adrien'

from PyQt5 import QtCore
from PyQt5.QtWidgets import (QWidget,
                             QHeaderView, QGridLayout,
                             QRadioButton, QTextEdit, QLabel, QLineEdit, QCheckBox, QTableWidget, QComboBox, QPushButton)
from PyQt5.QtGui import QFont
from collections import OrderedDict
from datetime import datetime
from functools import partial
from GUI.digitise.DigitiseWidgetWorker import DigitiseWidgetWorker


class DigitiseWidget(QWidget):
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

    def delete_table_row(self):
        """
        This function is linked to the delete button when a row is added.
        When the delete button is pressed, the function look up its row and delete it
        :return: nothing
        """
        sender = self.sender()
        index = self.digitise_table.indexAt(sender.pos())
        if index.isValid():
            self.digitise_table.removeRow(index.row())

    def combobox_changed(self, text):
        """
        This function is linked to the combobox when a row is added
        When the combobox selected item changes (example: from dc:contributor to dc:description),
        this function is called to make the row fit its new usage. (example: enter text or a date)
        :param text: it's the selected combobox item name
        :return: nothing
        """
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
            elif text == "ratio":
                self.digitise_table.removeCellWidget(row, 1)
                self.digitise_table.setCellWidget(row, 1, QComboBox())
                self.digitise_table.setRowHeight(row, 30)
                self.digitise_table.cellWidget(row, 1).addItems(["4/3", "16/9"])
            else:
                self.digitise_table.removeCellWidget(row, 1)
                self.digitise_table.setCellWidget(row, 1, QLineEdit())
                self.digitise_table.setRowHeight(row, 30)

    def add_row(self):
        # todo add the size ratio with default 4/3
        """
        This function add a new row (Hoho !) when the new_table_row button is pressed
        this function will fill the combobox with their name and a tooltip,
        link the combobox to the combobox_changed function,
        link the delete button with the delete_table_row function
        :return: nothing
        """

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
        dc_data['ratio'] = "format visuel du film"

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

    def digitise_worker(self, action, data):
        """
        :param action: tell which action the digitise_worker function should launch
        :param data: the data can be a dictionary, a list, a sting, an integer
        if the chosen action is "digitise" the parameter will be : [digitise_infos, dublincore_dict]
        digitise_infos and dublincore_dict are dictionarys

        :return: nothing, the function instantiate the DigitiseTabWorker class and then exit
        """

        if action == "digitise" and "duration" in data[1].get('format', {}):
            # this check if at least a duration is set before sending the data to the back end
            self.workerThread_digitise = QtCore.QThread()
            self.workerObject_digitise = DigitiseWidgetWorker()
            self.workerObject_digitise.moveToThread(self.workerThread_digitise)

            self.launch_digitise.setEnabled(False)

            self.workerThread_digitise.started.connect(partial(self.workerObject_digitise.digitise, command=data))
            self.workerObject_digitise.finished.connect(self.workerThread_digitise.quit)
            self.workerObject_digitise.finished.connect(partial(self.launch_digitise.setEnabled, True))
            self.workerObject_digitise.launch_digitise_done.connect(self.result_digitise.setText)

            self.workerThread_digitise.start()

    def digitise(self):
        # todo: find a way to use an increment only for the dc:identifier field, like an UID
        """
        This function wil gather all the metadata, add the constants listed below.

        # Handle the dublincore metadata
        # dc:rights = usage libre pour l'éducation
        # dc:source = VHS
        # dc:type = "image"
        # dcterms:modified = date de la numérisation
        # dc:identifier = id incremental pour chaque VHS
        # dc:format = {"size_ratio": "4/3", "duration": temps}

        :return: nothing but call the digitise_worker function with the parameter [digitise_infos, dublincore_dict]

        [{'H265': False, 'decklink_card': '2', 'H264': False, 'package_mediatheque': False},
        {'dc:description': ['this is a general summary of the resource'], 'dc:contributor': ['great contributor'],
        'format': {'size_ratio': '4/3', 'duration': 165}}]
        """

        dublincore_dict = {}
        dublincore_dict["format"] = {"size_ratio": "4/3"}

        for row in range(self.digitise_table.rowCount()):
            combobox_text = self.digitise_table.cellWidget(row, 0).currentText()
            widget_type = self.digitise_table.cellWidget(row, 1).metaObject().className()
            if widget_type == "QLineEdit":
                widget_text_value = self.digitise_table.cellWidget(row, 1).displayText()
            elif widget_type == "QTextEdit":
                widget_text_value = self.digitise_table.cellWidget(row, 1).toPlainText()
            elif widget_type == "QComboBox":
                widget_text_value = self.digitise_table.cellWidget(row, 1).currentText()

            if widget_text_value is not "":
                if combobox_text == "durée":
                    dublincore_dict["format"]["duration"] = int(widget_text_value)
                elif combobox_text == "ratio":
                    dublincore_dict["format"]["size_ratio"] = widget_text_value
                elif combobox_text == "dcterms:created":
                    dublincore_dict[combobox_text] = int(widget_text_value)
                elif combobox_text == "dc:description":
                    # this will only keep one description
                    # todo: merge the descriptions ?
                    dublincore_dict[combobox_text] = widget_text_value
                else:
                    try:
                        dublincore_dict[combobox_text].append(widget_text_value)
                    except KeyError:
                        dublincore_dict[combobox_text] = [widget_text_value]
        dublincore_dict["dc:rights"] = "usage libre pour l'éducation"
        dublincore_dict["dc:source"] = "VHS"
        dublincore_dict["dc:type"] = "video"
        dublincore_dict["dcterms:modified"] = datetime.now().replace(microsecond=0).isoformat()

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

        self.digitise_worker(action="digitise", data=to_be_send)

    def tab_init(self):
        """
        This function is called when the DigitiseWidget class init
        Its job is to put the widgets instantiated in the init function to their place and
        set some link between functions and buttons
        :return: nothing
        """
        grid = QGridLayout()
        self.setLayout(grid)

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
        self.digitise_table.setHorizontalHeaderLabels(["", "", ""])

        grid.addWidget(self.digitise_table, 3, 0, 5, 2)
        grid.addWidget(self.new_table_row, 3, 3)
        grid.addWidget(self.launch_digitise, 5, 3)
        grid.addWidget(self.result_digitise, 6, 3)

        self.new_table_row.clicked.connect(self.add_row)
        self.launch_digitise.clicked.connect(self.digitise)

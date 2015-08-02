__author__ = 'adrien'

from PyQt5 import QtCore
from PyQt5.QtWidgets import (QWidget,
                             QHeaderView, QGridLayout,
                             QTextEdit, QLineEdit, QTableWidget, QComboBox, QPushButton)
from PyQt5.QtGui import QFont
from functools import partial
from collections import OrderedDict
from GUI.search.SearchWidgetWorker import SearchWidgetWorker

# todo permettre de trouver les videos numérisées un certain jour, retour de Qcalendar


class SearchWidget(QWidget):
    show_result_widget_signal = QtCore.pyqtSignal()
    search_transmit = QtCore.pyqtSignal([list])

    def __init__(self):
        # Initialize the parent class QWidget
        super().__init__()

        # query table
        #########
        self.query_table = QTableWidget()
        self.table_font = QFont(QFont().defaultFamily(), 12)
        self.add_row_button = QPushButton("ajouter")
        self.search_button = QPushButton("rechercher")

        #########

        # answer table
        #########
        self.grid2 = None

        #########

        # Stacked layout
        #########
        # self.layout_stack = QStackedLayout()

        #########

        self.workerThread_search = None
        self.workerObject_search = None

        # this variable will store the search results when they come
        self.search_results = None

        self.tab_init()

    def delete_table_row(self):
        """
        This function is linked to the delete button when a row is added.
        When the delete button is pressed, the function look up its row and delete it
        :return: nothing
        """
        sender = self.sender()
        index = self.query_table.indexAt(sender.pos())
        if index.isValid():
            self.query_table.removeRow(index.row())

    def dc_combobox_changed(self, text):
        """
        This function is linked to the dublin core combobox when a row is added
        When the combobox selected item changes (example: from dc:contributor to dc:description),
        this function is called to make the row fit its new usage. (example: enter text or a date)
        :param text: it's the selected combobox item name
        :return: nothing
        """
        sender = self.sender()
        index = self.query_table.indexAt(sender.pos())
        logic_time_list = ["equal", "greater", "inferior"]
        logic_text_list = ["equal", "contain"]
        if index.isValid():
            row = index.row()
            if text == "dc:description":
                self.query_table.removeCellWidget(row, 1)
                self.query_table.setCellWidget(row, 1, QComboBox())
                self.query_table.cellWidget(row, 1).addItems(logic_text_list)

                self.query_table.removeCellWidget(row, 2)
                self.query_table.setCellWidget(row, 2, QTextEdit())
                self.query_table.setRowHeight(row, 60)

            elif text == "dcterms:created":
                self.query_table.removeCellWidget(row, 1)
                self.query_table.setCellWidget(row, 1, QComboBox())
                self.query_table.cellWidget(row, 1).addItems(logic_time_list)

                self.query_table.removeCellWidget(row, 2)
                self.query_table.setCellWidget(row, 2, QLineEdit())
                self.query_table.cellWidget(row, 2).setInputMask("0000")
                self.query_table.setRowHeight(row, 30)
            elif text == "durée":
                self.query_table.removeCellWidget(row, 1)
                self.query_table.setCellWidget(row, 1, QComboBox())
                self.query_table.cellWidget(row, 1).addItems(logic_time_list)

                self.query_table.removeCellWidget(row, 2)
                self.query_table.setCellWidget(row, 2, QLineEdit())
                self.query_table.setRowHeight(row, 30)
                self.query_table.cellWidget(row, 2).setInputMask("000")
            else:
                self.query_table.removeCellWidget(row, 1)
                self.query_table.setCellWidget(row, 1, QComboBox())
                self.query_table.cellWidget(row, 1).addItems(logic_text_list)

                self.query_table.removeCellWidget(row, 2)
                self.query_table.setCellWidget(row, 2, QLineEdit())
                self.query_table.setRowHeight(row, 30)

    def add_row(self):
        """
        This function add a new row (Hoho !) when the new_table_row button is pressed
        this function will fill the combobox with their name and a tooltip,
        link the dublin core combobox to the dc_combobox_changed function,
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

        logic_text_list = ["equal", "contain"]

        row_count = self.query_table.rowCount()
        self.query_table.insertRow(row_count)
        self.query_table.setCellWidget(row_count, 0, QComboBox())

        count = 0
        for dc_key, dc_tooltip in dc_data.items():
            self.query_table.cellWidget(row_count, 0).addItem(dc_key)
            self.query_table.cellWidget(row_count, 0).setItemData(count, dc_tooltip, QtCore.Qt.ToolTipRole)
            count += 1

        self.query_table.cellWidget(row_count, 0).activated[str].connect(self.dc_combobox_changed)

        self.query_table.setCellWidget(row_count, 1, QComboBox())
        self.query_table.cellWidget(row_count, 1).addItems(logic_text_list)

        self.query_table.setCellWidget(row_count, 2, QLineEdit())
        self.query_table.setCellWidget(row_count, 3, QPushButton("Delete"))
        self.query_table.cellWidget(row_count, 3).clicked.connect(self.delete_table_row)

    def search_worker(self, action, data):
        """
        :param action: tell which action the search_worker function should launch
        :param data: the parameter can be a dictionary, a list, a sting, an integer
        if the chosen action is "search" the parameter will be a dictionary.

        :return: nothing, the function instantiate the DigitiseWidgetWorker class and then exit
        """

        # toute la base de donnée est retournée si on fait une recherche sans arguments
        if data and action == "search":
            self.workerThread_search = QtCore.QThread()
            self.workerObject_search = SearchWidgetWorker()
            self.workerObject_search.moveToThread(self.workerThread_search)

            self.search_button.setEnabled(False)

            self.workerThread_search.started.connect(partial(self.workerObject_search.search, command=data))
            self.workerObject_search.finished.connect(self.workerThread_search.quit)
            self.workerObject_search.finished.connect(partial(self.search_button.setEnabled, True))
            self.workerObject_search.search_done.connect(self.search_transmit.emit)

            self.workerThread_search.start()

    def search(self):
        """
        This function gather the search keys and put them in a dictionary similar to the one shown below:
        {'dc:description': {'contain': ['some part of the description', 'an other part of the description']},
        'dc:format.duration': {'inferior': [120]}, 'dc:contributor': {'equal': ['great contributor']}}

        :return: nothing but call the search worker with the dictionary as parameter
        """

        # Handle the dublincore metadata
        query_dict = {}
        for row in range(self.query_table.rowCount()):
            dc_combobox_text = self.query_table.cellWidget(row, 0).currentText()
            data_widget_type = self.query_table.cellWidget(row, 2).metaObject().className()
            if data_widget_type == "QLineEdit":
                data_widget_text_value = self.query_table.cellWidget(row, 2).displayText()
            elif data_widget_type == "QTextEdit":
                data_widget_text_value = self.query_table.cellWidget(row, 2).toPlainText()
            query_type = self.query_table.cellWidget(row, 1).currentText()

            if data_widget_text_value is not "":
                if dc_combobox_text == "durée":
                    dc_combobox_text = "dc:format.duration"
                try:
                    if dc_combobox_text == "dcterms:created" or dc_combobox_text == "dc:format.duration":
                        query_dict[dc_combobox_text][query_type].append(int(data_widget_text_value))
                    else:
                        query_dict[dc_combobox_text][query_type].append(data_widget_text_value)
                except KeyError:
                    try:
                        if dc_combobox_text == "dcterms:created" or dc_combobox_text == "dc:format.duration":
                            query_dict[dc_combobox_text][query_type] = [int(data_widget_text_value)]
                        else:
                            query_dict[dc_combobox_text][query_type] = [data_widget_text_value]
                    except KeyError:
                        if dc_combobox_text == "dcterms:created" or dc_combobox_text == "dc:format.duration":
                            query_dict[dc_combobox_text] = {query_type: [int(data_widget_text_value)]}
                        else:
                            query_dict[dc_combobox_text] = {query_type: [data_widget_text_value]}

        print(query_dict)
        self.search_worker(action="search", data=query_dict)

    def tab_init(self):
        """
        This function is called when the SearchWidget class init
        Its job is to put the widgets instantiated in the init function to their place and
        set some link between functions and buttons
        :return: nothing
        """

        query_widget_layout = QGridLayout()
        self.setLayout(query_widget_layout)

        # query Table
        self.query_table.setRowCount(0)
        self.query_table.setColumnCount(4)
        self.query_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.query_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.query_table.setColumnWidth(0, 170)
        self.query_table.setFont(self.table_font)
        self.query_table.setHorizontalHeaderLabels(["", "", "", ""])

        self.add_row_button.clicked.connect(self.add_row)
        self.search_button.clicked.connect(self.search)
        self.search_button.clicked.connect(self.show_result_widget_signal.emit)

        query_widget_layout.addWidget(self.query_table, 0, 0, 3, 3)
        query_widget_layout.addWidget(self.add_row_button, 0, 4)
        query_widget_layout.addWidget(self.search_button, 4, 4)

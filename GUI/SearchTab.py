__author__ = 'adrien'

from PyQt5 import QtCore
from PyQt5.QtCore import QDateTime
import xmlrpc.client
from PyQt5.QtWidgets import (QWidget,
                             QHeaderView, QGridLayout, QStackedLayout,
                             QTextEdit, QLineEdit, QTableWidget, QComboBox, QPushButton, QCalendarWidget)
from PyQt5.QtGui import QFont
from functools import partial
from collections import OrderedDict


class SearchTabWorker(QtCore.QObject):

    client = xmlrpc.client.ServerProxy('http://localhost:8000')

    search_done = QtCore.pyqtSignal([list])
    finished = QtCore.pyqtSignal()
    print("SearchTab worker init")

    def __init__(self):
        super().__init__()

    def search(self, command):
        print("bridge search()")
        return_payload = self.client.search(command)
        #print(return_payload)
        self.search_done.emit(return_payload)
        self.finished.emit()


class SearchTab(QWidget):
    def __init__(self):
        # Initialize the parent class QWidget
        super().__init__()

        # query table
        #########
        self.grid1 = None
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
        sender = self.sender()
        index = self.query_table.indexAt(sender.pos())
        if index.isValid():
            self.query_table.removeRow(index.row())

    def dc_combobox_changed(self, text):
        sender = self.sender()
        index = self.query_table.indexAt(sender.pos())
        logic_time_list = ["equal", "greater", "inferior"]
        logic_text_list = ["equal", "contain"]
        if index.isValid():
            row = index.row()
            if text == "dc:description":
                # print(self.table.rowHeight(row))
                self.query_table.removeCellWidget(row, 2)
                self.query_table.setCellWidget(row, 2, QTextEdit())
                self.query_table.setRowHeight(row, 60)
            else:
                self.query_table.removeCellWidget(row, 2)
                self.query_table.setCellWidget(row, 2, QLineEdit())
                self.query_table.setRowHeight(row, 30)

            if text == "dcterms:created":
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

    def tab2_worker(self, action, parameter):

        if action == "search":
            self.workerThread_search = QtCore.QThread()
            self.workerObject_search = SearchTabWorker()
            self.workerObject_search.moveToThread(self.workerThread_search)

            self.search_button.setEnabled(False)

            self.workerThread_search.started.connect(partial(self.workerObject_search.search, command=parameter))
            self.workerObject_search.finished.connect(self.workerThread_search.quit)
            self.workerObject_search.finished.connect(partial(self.search_button.setEnabled, True))
            self.workerObject_search.search_done.connect(self.search_done)

            self.workerThread_search.start()

    def search_done(self, argu):
        self.search_results = argu
        print("aleluyaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        print(argu)

    def search(self):

        # Handle the dublincore metadata
        search_dict = {}
        for row in range(self.query_table.rowCount()):
            dc_combobox_text = self.query_table.cellWidget(row, 0).currentText()
            data_widget_type = self.query_table.cellWidget(row, 2).metaObject().className()
            if data_widget_type == "QLineEdit":
                data_widget_text_value = self.query_table.cellWidget(row, 2).displayText()
            elif data_widget_type == "QTextEdit":
                data_widget_text_value = self.query_table.cellWidget(row, 2).toPlainText()
            elif data_widget_type == "QCalendarWidget":
                data_widget_text_value = self.query_table.cellWidget(row, 2).selectedDate().toPyDate().strftime("%d %b %Y")
            query_type = self.query_table.cellWidget(row, 1).currentText()

            if data_widget_text_value is not "":
                if dc_combobox_text == "durée":
                    search_dict["dc:format.duration"] = {query_type: [int(data_widget_text_value)]}
                elif dc_combobox_text == 'dcterms:created':
                    try:
                        search_dict[dc_combobox_text][query_type] = [int(data_widget_text_value)]
                    except KeyError:
                        search_dict[dc_combobox_text] = {query_type: [int(data_widget_text_value)]}
                else:
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

        # todo: Pour afficher le resultat de la recherche, rendre le widget grid1 invisible et le remplacer par grid2
        # grid2 contiendra une table remplie avec les résultats de la recherche + un bouton pour re-afficher grid1.

        self.grid1 = QGridLayout()

        # query Table
        self.query_table.setRowCount(0)
        self.query_table.setColumnCount(4)
        self.query_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.query_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.query_table.setColumnWidth(0, 170)
        self.query_table.setFont(self.table_font)
        self.add_row_button.clicked.connect(self.add_row)
        self.search_button.clicked.connect(self.search)

        self.grid1.addWidget(self.query_table, 0, 0, 3, 3)
        self.grid1.addWidget(self.add_row_button, 0, 4)
        self.grid1.addWidget(self.search_button, 4, 4)

        self.setLayout(self.grid1)

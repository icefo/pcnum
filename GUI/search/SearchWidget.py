__author__ = 'adrien'

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (QWidget,
                             QHeaderView, QGridLayout,
                             QTextEdit, QLineEdit, QTableWidget, QComboBox, QPushButton, QMessageBox)
from PyQt5.QtGui import QFont
from collections import OrderedDict
from pymongo import MongoClient, ASCENDING
import atexit

# todo add search by source (DVD, file_import, decklink)
class SearchWidget(QWidget):
    show_result_widget_signal = pyqtSignal()
    search_transmit = pyqtSignal([list])

    def __init__(self):
        # Initialize the parent class QWidget
        super().__init__()

        #########
        self.query_table = QTableWidget()
        self.table_font = QFont(QFont().defaultFamily(), 12)

        #########
        self.add_row_button = QPushButton("ajouter")
        self.search_button = QPushButton("rechercher")

        #########
        self.db_client = MongoClient("mongodb://localhost:27017/")
        digitize_app = self.db_client['digitize_app']
        self.videos_metadata_collection = digitize_app['videos_metadata']
        # This function is called when the SearchWidget class is about to be destroyed
        atexit.register(self.cleanup)

        self.tab_init()

    def cleanup(self):
        self.db_client.close()
        print("SearchWidget's db connection closed")

    def delete_table_row(self):
        """
        This function is linked to the delete button when a row is added.
        When the delete button is pressed, the function look up its row and delete it

        :return:
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

        :return:
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

        :return:
        """

        dc_data = OrderedDict()
        dc_data['dc:contributor'] = "nom de acteurs"
        dc_data['dc:creator'] = "maison d'édition, scénariste ou réalisateur"
        dc_data['dc:description'] = "résumé de la vidéo"
        dc_data['dc:language'] = "langue de la vidéo"
        dc_data['dc:publisher'] = "entreprise qui a publié le film, par exemple Sony Pictures"
        dc_data['dc:subject'] = "thème du film: horreur, action, histoire d'amour..."
        dc_data['dc:title'] = "titre du film"
        dc_data['dcterms:isPartOf'] = "remplir si le film fait partit d'un ensemble de films comme Star Wars"
        dc_data['dcterms:created'] = "année de sortie du film"
        dc_data['durée'] = "durée du film en minutes"

        logic_text_list = ["equal", "contain"]

        row_count = self.query_table.rowCount()
        self.query_table.insertRow(row_count)
        self.query_table.setCellWidget(row_count, 0, QComboBox())

        count = 0
        for dc_key, dc_tooltip in dc_data.items():
            self.query_table.cellWidget(row_count, 0).addItem(dc_key)
            self.query_table.cellWidget(row_count, 0).setItemData(count, dc_tooltip, Qt.ToolTipRole)
            count += 1

        self.query_table.cellWidget(row_count, 0).activated[str].connect(self.dc_combobox_changed)

        self.query_table.setCellWidget(row_count, 1, QComboBox())
        self.query_table.cellWidget(row_count, 1).addItems(logic_text_list)

        self.query_table.setCellWidget(row_count, 2, QLineEdit())
        self.query_table.setCellWidget(row_count, 3, QPushButton("Delete"))
        self.query_table.cellWidget(row_count, 3).clicked.connect(self.delete_table_row)

    def run_search_query(self, command):
        """
        take the command parameter from the search function and transform it in the MongoDB syntax:
        {'$and': [{'dc:creator': {'$options': 'i', '$regex': '^claire sougner$'}},
        {'dc:description': {'$options': 'i', '$regex': ".*C'est l'histoire de.*"}},
        {'dc:format.duration': {'$gt': 35}},
        {'dc:format.duration': {'$lt': 75}},
        {'dc:title': {'$options': 'i', '$regex': '.*La tour.*'}}]}

        :param command: dictionary

        :return:
        """
        print("run_search_query()")

        mongo_query = {"$and": []}
        for dc_item, dict_query in command.items():
            print(dc_item, dict_query)
            for query_type, query in dict_query.items():
                if query_type == "equal":
                    for query_item in query:
                        if isinstance(query_item, str):
                            mongo_query["$and"].append({dc_item: {"$regex": "^" + query_item + "$", "$options": "i"}})
                        else:
                            mongo_query["$and"].append({dc_item: query_item})
                elif query_type == "contain":
                    for query_item in query:
                        mongo_query["$and"].append({dc_item: {"$regex": ".*" + query_item + ".*", "$options": "i"}})
                elif query_type == "greater":
                    mongo_query["$and"].append({dc_item: {"$gt": query[0]}})
                elif query_type == "inferior":
                    mongo_query["$and"].append({dc_item: {"$lt": query[0]}})

        print(mongo_query)
        result_list = []
        for post in self.videos_metadata_collection.find(mongo_query, {'_id': False}).sort([("dc:format.duration",
                                                                                             ASCENDING)]):
            result_list.append(post)
            print(post)
        self.search_transmit.emit(result_list)

        # re-enable button hammering
        self.search_button.setEnabled(True)

    def search(self):
        """
        This function gather the search keys and put them in a dictionary similar to the one shown below:
        {'dc:creator': {'equal': ['claire sougner']}, 'dc:description': {'contain': ["C'est l'histoire de"]},
        'dc:format.duration': {'greater': [35], 'inferior': [75]}, 'dc:title': {'contain': ['La tour']}}

        :return: nothing but call the run_search_query function with the dictionary as parameter
        """
        # Prevent button hammering
        self.search_button.setEnabled(False)
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

            if data_widget_text_value != "":
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

        if query_dict:
            print(query_dict)
            self.run_search_query(command=query_dict)
        else:
            warning_box = QMessageBox()
            warning_message = "Il faut entrer des informations à rechercher"

            warning_box.warning(warning_box, "Attention", warning_message)
            self.search_button.setEnabled(True)

    def tab_init(self):
        """
        This function is called when the SearchWidget class init
        Its job is to put the widgets instantiated in the init function to their place and
        set some link between functions and buttons

        :return:
        """
        grid = QGridLayout()
        self.setLayout(grid)

        #########
        self.query_table.setRowCount(0)
        self.query_table.setColumnCount(4)
        self.query_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.query_table.setColumnWidth(0, 170)
        self.query_table.setFont(self.table_font)
        self.query_table.setHorizontalHeaderLabels(["", "", "", ""])

        #########
        grid.addWidget(self.query_table, 0, 0, 4, 5)
        grid.addWidget(self.add_row_button, 0, 6)
        grid.addWidget(self.search_button, 3, 6)

        #########
        self.add_row_button.clicked.connect(self.add_row)
        self.search_button.clicked.connect(self.search)
        self.search_button.clicked.connect(self.show_result_widget_signal.emit)

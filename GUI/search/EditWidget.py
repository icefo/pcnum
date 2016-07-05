from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtWidgets import (QWidget, QApplication, QMainWindow,
                             QHeaderView, QGridLayout,
                             QRadioButton, QCheckBox, QTextEdit, QLabel, QLineEdit, QTableWidget, QComboBox,
                             QPushButton, QFileDialog, QMessageBox)
from PyQt5.QtGui import QFont
from collections import OrderedDict
from datetime import datetime
import os
import shutil
from functools import partial
from backend.shared import FILES_PATHS, wrap_in_future
import asyncio
from pymongo import MongoClient
import sys


class EditWidget(QWidget):
    """
    This QWidget gather and check the user provided metadata and commit it to the database
    This QWidget is largely inspired from the CaptureWidget

    Attributes:
    self.show_result_widget_signal (pyqtSignal()): Is used to ask the MainSearchWidget to display the ResultWidget
    self.request_refresh_signal (pyqtSignal()): Is used to ask the SearchWidget to rerun the search after an edit
    """

    show_result_widget_signal = pyqtSignal()
    request_refresh_signal = pyqtSignal()

    def __init__(self):
        # Initialize the parent class QWidget
        # this allow the use of the parent's methods when needed
        super(EditWidget, self).__init__()

        #########
        self.edit_label = QLabel("Choisissez les éléments à modifier")

        #########
        self.edit_table = QTableWidget()
        self.table_font = QFont(QFont().defaultFamily(), 12)

        #########
        self.new_table_row_button = QPushButton("Ajouter")
        self.save_modifications_button = QPushButton("Sauvegarder")
        self.return_to_result_button = QPushButton('Retour')

        #########
        dc_data = OrderedDict()
        dc_data['dc:contributor'] = "nom des acteurs"
        dc_data['dc:creator'] = "maison d'édition, scénariste ou réalisateur"
        dc_data['dc:description'] = "résumé de la vidéo"
        dc_data['dc:language'] = "langue de la vidéo: FRA, ENG"
        dc_data['dc:publisher'] = "entreprise qui a publié le film, par exemple Sony Pictures"
        dc_data['dc:subject'] = "thème du film: horreur, action, histoire d'amour..."
        dc_data['dc:title'] = "titre du film"
        dc_data['dcterms:isPartOf'] = "remplir si le film fait partie d'un ensemble de films comme Star Wars"
        dc_data['dcterms:created'] = "année de sortie du film"
        dc_data['ratio'] = "format visuel du film"
        dc_data['format_video'] = "format video de la cassette"
        self.digitise_table_row_tooltip = dc_data

        #########
        self.raw_videos_path = FILES_PATHS["raw"]
        self.compressed_videos_path = FILES_PATHS["compressed"]
        self.imported_files_path = FILES_PATHS["imported"]

        #########
        self.db_client = MongoClient("mongodb://localhost:27017/")
        digitize_app = self.db_client['digitize_app']
        self.videos_metadata_collection = digitize_app['videos_metadata']

        #########
        self.capture_data = None

        #########
        self.tab_init()

    @wrap_in_future
    @asyncio.coroutine
    def receive_data(self, dc_identifier):
        """
        Receive data from the ResultWidget, parse it and call self.add_table_row for each row to add
        Args:
            dc_identifier (str):

        """
        self.capture_data = self.videos_metadata_collection.find_one({"dc:identifier": dc_identifier}, {'_id': False})
        print("hey")
        print(self.capture_data)
        for key, values in self.capture_data.items():
            if key in ('dc:identifier', 'duration', 'dc:type', 'files_path', 'dcterms:modified'):
                pass
            elif key in ('dc:subject', 'dc:publisher', 'dc:creator', 'dc:title', 'dc:language', 'dc:contributor',
                         'dcterms:isPartOf'):
                for value in values:
                    row_count = self.edit_table.rowCount()
                    self.add_table_row()

                    self.edit_table.cellWidget(row_count, 0).setCurrentText(key)
                    self.edit_table.cellWidget(row_count, 1).setText(value)
            elif key == 'dc:description':
                row_count = self.edit_table.rowCount()
                self.add_table_row()
                print(row_count)
                print(values)
                self.edit_table.cellWidget(row_count, 0).setCurrentText(key)
                # Ugly hack to let the combobox_changed function some time to react
                # the function is linked with a signal and the reaction is not instantaneous
                yield from asyncio.sleep(0.5)
                self.edit_table.cellWidget(row_count, 1).setText(values)
            elif key == 'dc:format':
                row_count = self.edit_table.rowCount()
                self.add_table_row()
                self.edit_table.cellWidget(row_count, 0).setCurrentText('format_video')
                yield from asyncio.sleep(0.5)
                self.edit_table.cellWidget(row_count, 1).setCurrentText(values['format'])

                self.add_table_row()
                self.edit_table.cellWidget(row_count + 1, 0).setCurrentText('ratio')
                yield from asyncio.sleep(0.5)
                self.edit_table.cellWidget(row_count + 1, 1).setCurrentText(values['aspect_ratio'])
            elif key == 'dcterms:created':
                row_count = self.edit_table.rowCount()
                self.add_table_row()

                self.edit_table.cellWidget(row_count, 0).setCurrentText(key)
                self.edit_table.cellWidget(row_count, 1).setText(str(values))

    def add_table_row(self):
        """
        Is called when the "self.new_table_row_button" button is pressed or by the receive_row function

        This function will fill the combobox with their name and a tooltip, link the combobox
         to the "self.combobox_changed function" and link the delete button with the self.delete_table_row" function

        """

        row_count = self.edit_table.rowCount()
        self.edit_table.insertRow(row_count)
        self.edit_table.setCellWidget(row_count, 0, QComboBox())

        count = 0
        for dc_key, dc_tooltip in self.digitise_table_row_tooltip.items():
            self.edit_table.cellWidget(row_count, 0).addItem(dc_key)
            self.edit_table.cellWidget(row_count, 0).setItemData(count, dc_tooltip, Qt.ToolTipRole)
            count += 1

        self.edit_table.cellWidget(row_count, 0).currentTextChanged[str].connect(self.combobox_changed)
        self.edit_table.setCellWidget(row_count, 1, QLineEdit())
        self.edit_table.setCellWidget(row_count, 2, QPushButton("Delete"))
        self.edit_table.cellWidget(row_count, 2).clicked.connect(self.delete_table_row)

    def delete_table_row(self):
        """
        Is linked to the delete button when a row is added.

        When the delete button is pressed, the function look up its row and delete it
        """

        sender = self.sender()
        index = self.edit_table.indexAt(sender.pos())
        if index.isValid():
            self.edit_table.removeRow(index.row())

    def combobox_changed(self, text):
        """
        Is linked to the combobox when a row is added

        When the combobox selected item changes (example: from dc:contributor to dc:description),
        this function is called to make the row fit its new usage. (example: enter text or a date)

        Args:
            text (str): its the active combobox selection
        """
        sender = self.sender()
        index = self.edit_table.indexAt(sender.pos())
        if index.isValid():
            row = index.row()
            if text == "dc:description":
                self.edit_table.removeCellWidget(row, 1)
                self.edit_table.setCellWidget(row, 1, QTextEdit())
                self.edit_table.setRowHeight(row, 60)
            elif text == "dcterms:created":
                self.edit_table.removeCellWidget(row, 1)
                self.edit_table.setCellWidget(row, 1, QLineEdit())
                self.edit_table.cellWidget(row, 1).setInputMask("0000")
                self.edit_table.setRowHeight(row, 30)
            elif text == "ratio":
                self.edit_table.removeCellWidget(row, 1)
                self.edit_table.setCellWidget(row, 1, QComboBox())
                self.edit_table.setRowHeight(row, 30)
                self.edit_table.cellWidget(row, 1).addItems(["4:3", "16:9"])
            elif text == "format_video":
                self.edit_table.removeCellWidget(row, 1)
                self.edit_table.setCellWidget(row, 1, QComboBox())
                self.edit_table.setRowHeight(row, 30)
                self.edit_table.cellWidget(row, 1).addItems(["PAL", "SECAM", "NTSC"])
            elif text == "dc:language":
                self.edit_table.removeCellWidget(row, 1)
                self.edit_table.setCellWidget(row, 1, QLineEdit())
                self.edit_table.setRowHeight(row, 30)
                self.edit_table.cellWidget(row, 1).setInputMask("AAA")
            else:
                self.edit_table.removeCellWidget(row, 1)
                self.edit_table.setCellWidget(row, 1, QLineEdit())
                self.edit_table.setRowHeight(row, 30)

    def metadata_checker(self, capture_action, data):
        """
        Check if the required metadata is present. If yes it launches the launch_capture function

        Args:
            capture_action (str): tell which capture_action the metadata_checker function should launch
                Possible values: decklink, file, DVD
            data: [digitise_infos, dublincore_dict]
        """

        # this check if at least a duration, title, and creation date is set before sending the data to the back end
        if capture_action == "decklink" and "duration" in data[1].get('dc:format', {}) and "dc:title" in data[1] \
                and "dcterms:created" in data[1] and self.check_remaining_space(
            VHS_duration=data[1]["dc:format"]["duration"]):

            self.launch_digitise_button.setEnabled(False)

            self.launch_capture(data)
            self.launch_digitise_button.setEnabled(True)
            # set status bar temp text
            self.set_statusbar_text_signal.emit("Numérisation Decklink lancée")

        elif capture_action == "file" and "file_path" in data[0] and "dc:title" in data[1] and "dcterms:created" in data[1] \
                and self.check_remaining_space(import_file_path=data[0]["file_path"]):

            self.launch_digitise_button.setEnabled(False)

            self.launch_capture(data)
            self.launch_digitise_button.setEnabled(True)

            self.set_statusbar_text_signal.emit("Enregistrement du fichier lancé !")

        elif capture_action == "DVD" and "dc:title" in data[1] and "dcterms:created" in data[1] \
                and self.check_remaining_space(for_DVD=True):

            self.launch_digitise_button.setEnabled(False)

            self.launch_capture(data)
            self.launch_digitise_button.setEnabled(True)

            self.set_statusbar_text_signal.emit("Enregistrement du DVD lancé !")
        else:
            warning_box = QMessageBox()
            warning_message = (
                "Les informations suivantes sont necessaires:\n"
                "   Pour enregistrer un dvd:\n"
                "       un titre et la date de creation de l'oeuvre\n"
                "   Pour enregistrer une cassette:\n"
                "       la durée, un titre et la date de creation de l'oeuvre\n"
                "\n"
                "   Il faut aussi avoir sélectionné une méthode d'enregistrement (decklink, dvd...)")

            warning_box.warning(warning_box, "Attention", warning_message)
            self.launch_digitise_button.setEnabled(True)

    def save_modifications(self):
        """
        Gather the user provided metadata and add the constants listed below.
            dublincore_dict["dcterms:modified"] = datetime.now().replace(microsecond=0).isoformat()
        """

        dublincore_dict = dict()
        dublincore_dict["dc:format"] = dict()

        for row in range(self.edit_table.rowCount()):
            combobox_text = self.edit_table.cellWidget(row, 0).currentText()
            widget_type = self.edit_table.cellWidget(row, 1).metaObject().className()
            if widget_type == "QLineEdit":
                widget_text_value = self.edit_table.cellWidget(row, 1).displayText()
            elif widget_type == "QTextEdit":
                widget_text_value = self.edit_table.cellWidget(row, 1).toPlainText()
            elif widget_type == "QComboBox":
                widget_text_value = self.edit_table.cellWidget(row, 1).currentText()

            if widget_text_value != "":
                if combobox_text == "ratio":
                    dublincore_dict["dc:format"]["aspect_ratio"] = widget_text_value
                elif combobox_text == "format_video":
                    dublincore_dict["dc:format"]["format"] = widget_text_value
                elif combobox_text == "dcterms:created":
                    dublincore_dict[combobox_text] = int(widget_text_value)
                elif combobox_text == "dc:description":
                    dublincore_dict[combobox_text] = widget_text_value
                else:
                    try:
                        dublincore_dict[combobox_text].append(widget_text_value)
                    except KeyError:
                        dublincore_dict[combobox_text] = [widget_text_value]
        dublincore_dict["dcterms:modified"] = datetime.now().replace(microsecond=0).isoformat()

        if 'dc:title' in dublincore_dict:
            dc_identifier = self.capture_data['dc:identifier']
            self.videos_metadata_collection.update_one(
                filter={"dc:identifier": dc_identifier},
                update={"$set": dublincore_dict})
        else:
            warning_box = QMessageBox()
            warning_message = "Il ne faut pas supprimer le titre de la vidéo !"

            warning_box.warning(warning_box, "Attention", warning_message)
        self.request_refresh_signal.emit()

    def reset_edit_table(self):
        self.edit_table.setRowCount(0)

    def tab_init(self):
        """
        Is called when the CaptureWidget class init

        Its job is to put the widgets instantiated in the init function to their place and set some signals between
         functions and buttons
        """

        grid = QGridLayout()
        self.setLayout(grid)

        #########
        self.edit_table.setRowCount(0)
        self.edit_table.setColumnCount(3)
        self.edit_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.edit_table.setColumnWidth(0, 170)
        self.edit_table.setFont(self.table_font)
        self.edit_table.setHorizontalHeaderLabels(["", "", ""])

        #########
        grid.addWidget(self.edit_label, 0, 0)

        grid.addWidget(self.edit_table, 1, 0, 7, 4)
        grid.addWidget(self.new_table_row_button, 1, 5)
        grid.addWidget(self.return_to_result_button, 8, 0)
        grid.addWidget(self.save_modifications_button, 8, 5)

        #########
        self.return_to_result_button.clicked.connect(self.show_result_widget_signal.emit)

        #########
        self.new_table_row_button.clicked.connect(self.add_table_row)
        self.save_modifications_button.clicked.connect(self.save_modifications)


class MainWindow(QMainWindow):
    """
    This class is a wamp client and adds the CaptureWidget, MainSearchWidget and StatusWidget in a QTabWidget.
    This class acts as a proxy for the widgets that want to communicate with the backend because they can't have a valid
     ApplicationSession that would allow them to be a wamp client and a QWidget.
    """

    def __init__(self, config=None):
        QMainWindow.__init__(self)

        self.my_timer = QTimer()
        self.my_timer1 = QTimer()

        self.main_window_init()

    def main_window_init(self):
        """
        This function init the main window
        It sets the status bar, menu bar and set the tabs class as central widget
        """
        self.setFont(QFont(QFont().defaultFamily(), 12))

        edit_widget = EditWidget()

        self.setCentralWidget(edit_widget)

        #########
        self.setGeometry(300, 300, 500, 400)
        self.setWindowTitle('Logiciel Numérisation')
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())
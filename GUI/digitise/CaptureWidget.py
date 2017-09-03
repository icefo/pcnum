from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtWidgets import (QWidget,
                             QHeaderView, QGridLayout,
                             QRadioButton, QCheckBox, QTextEdit, QLabel, QLineEdit, QTableWidget, QComboBox,
                             QPushButton, QFileDialog, QMessageBox)
from PyQt5.QtGui import QFont
from collections import OrderedDict, Counter
from datetime import datetime
import os
import shutil
from functools import partial
from backend.shared import FILES_PATHS

from backend.shared import wrap_in_future
import asyncio

import subprocess


# todo allow for more than one dc:description
# todo check if possible to add multiples dc:language

class CaptureWidget(QWidget):
    """
    This QWidget gather and check the user provided metadata and ask the MainWindow to launch the capture

    Attributes:
        self.receive_enable_decklink_radio_1 (pyqtSignal([bool])): signal sent by the StatusWidget
        self.receive_enable_decklink_radio_2 (pyqtSignal([bool])): signal sent by the StatusWidget
        self.set_statusbar_text_signal (pyqtSignal([str])): Is used to display text on the MainWindow's statusbar
    """

    receive_enable_decklink_radio_1 = pyqtSignal([bool])
    receive_enable_decklink_radio_2 = pyqtSignal([bool])
    set_statusbar_text_signal = pyqtSignal([str])

    def __init__(self, parent):
        # Initialize the parent class QWidget
        # this allow the use of the parent's methods when needed
        super(CaptureWidget, self).__init__(parent=parent)
        self.main_window = None

        #########
        self.decklink_label = QLabel("Choisissez la source vidéo")
        self.decklink_radio_1 = QRadioButton("Decklink 1 (NTSC/PAL)")
        self.decklink_radio_2 = QRadioButton("Decklink 2 (NTSC/PAL/SECAM)")
        self.file_import_radio = QRadioButton("importer fichier vidéo")
        self.dvd_import_radio = QRadioButton("importer dvd")
        self.lossless_import_checkbox = QCheckBox("Importer sans perte de qualité")

        #########
        self.digitise_table = QTableWidget()
        self.table_font = QFont(QFont().defaultFamily(), 12)
        self.new_table_row_button = QPushButton("Ajouter")
        self.launch_ffplay_button = QPushButton("Lancer aperçu")
        self.launch_digitise_button = QPushButton("Numériser")

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
        dc_data['durée'] = "durée du film en minutes"
        dc_data['ratio'] = "format visuel du film"
        dc_data['format_video'] = "format video de la cassette"
        self.digitise_table_row_tooltip = dc_data

        #########
        self.raw_videos_path = FILES_PATHS["raw"]
        self.compressed_videos_path = FILES_PATHS["compressed"]
        self.imported_files_path = FILES_PATHS["imported"]

        #########
        self.backend_is_alive_timer = QTimer()

        #########
        self.tab_init()

    def delayed_init(self):
        """
        Is called if the wamp router is successfully joined, if you don't wait, you get this:

        'NoneType' object has no attribute 'parent'
        Traceback (most recent call last):
            File "/usr/local/lib/python3.4/dist-packages/autobahn/wamp/websocket.py", line 62, in onOpen
                self._session.onOpen(self)
        AttributeError: 'NoneType' object has no attribute 'onOpen'
        """
        self.main_window = self.parent().parent().parent()  # MainWindow -> QTabWidget -> QStackedWidget

    @wrap_in_future
    @asyncio.coroutine
    def launch_capture(self, metadata):
        """
        Call the 'launch_capture' function in the backend

        Args:
            metadata (list): [digitise_infos, dublincore_dict]
        """
        print("metadata")
        print(metadata)
        yield from self.main_window.call('com.digitize_app.launch_capture', metadata)

    def launch_ffplay(self):
        decklink_id = None
        video_format = None

        if self.decklink_radio_1.isChecked() and self.decklink_radio_1.isEnabled():
            decklink_id = '1'
        elif self.decklink_radio_2.isChecked() and self.decklink_radio_2.isEnabled():
            decklink_id = '2'
        else:
            error_box = QMessageBox()
            error_box.setText("Veuillez sélectionner une carte d'aquisition non utilisée")
            error_box.setWindowTitle("Erreur")
            error_box.exec_()

        for row in range(self.digitise_table.rowCount()):
            combobox_text = self.digitise_table.cellWidget(row, 0).currentText()
            if combobox_text == 'format_video':
                video_format = self.digitise_table.cellWidget(row, 1).currentText()
                break
        if video_format is None and decklink_id == '1':
            error_box = QMessageBox()
            error_box.setText("Veuillez préciser le format de la vidéo")
            error_box.setWindowTitle("Erreur")
            error_box.exec_()

        if decklink_id == '1' and video_format:
            decklink_input = "Intensity Pro (1)"

            if video_format == 'SECAM':
                error_box = QMessageBox()
                error_box.setText("Il est impossible de numériser une cassette SECAM avec la carte numéro 1")
                error_box.setWindowTitle("Erreur")
                error_box.exec_()
            elif video_format == 'PAL':
                subprocess.Popen(['ffplay', '-f', 'decklink', '-format_code', 'pal', '-video_input', 'composite', '-i',
                                  decklink_input])
            elif video_format == 'NTSC':
                subprocess.Popen(['ffplay', '-f', 'decklink', '-format_code', 'ntsc', '-video_input', 'composite', '-i',
                                  decklink_input])
        elif decklink_id == '2':
            decklink_input = "Intensity Pro (2)"
            subprocess.Popen(['ffplay', '-f', 'decklink', '-format_code', 'hp60', '-video_input', 'hdmi',
                              '-aspect', '4:3', '-i', decklink_input])

    def backend_is_alive_beacon(self):
        """
        Is called when the backend send a beacon
        Effect: make a timer decrement from 15000 ms. If the timer reach zero, the widget can't start a new capture.
        """
        self.backend_is_alive_timer.setInterval(39000)

    def add_table_row(self):
        """
        Is called when the "self.new_table_row_button" button is pressed

        This function will fill the combobox with their name and a tooltip, link the combobox
         to the "self.combobox_changed function" and link the delete button with the self.delete_table_row" function
        """

        row_count = self.digitise_table.rowCount()
        self.digitise_table.insertRow(row_count)
        self.digitise_table.setCellWidget(row_count, 0, QComboBox())

        count = 0
        for dc_key, dc_tooltip in self.digitise_table_row_tooltip.items():
            self.digitise_table.cellWidget(row_count, 0).addItem(dc_key)
            self.digitise_table.cellWidget(row_count, 0).setItemData(count, dc_tooltip, Qt.ToolTipRole)
            count += 1

        self.digitise_table.cellWidget(row_count, 0).activated[str].connect(self.combobox_changed)
        self.digitise_table.setCellWidget(row_count, 1, QLineEdit())
        self.digitise_table.setCellWidget(row_count, 2, QPushButton("Delete"))
        self.digitise_table.cellWidget(row_count, 2).clicked.connect(self.delete_table_row)

    def delete_table_row(self):
        """
        Is linked to the delete button when a row is added.

        When the delete button is pressed, the function look up its row and delete it
        """

        sender = self.sender()
        index = self.digitise_table.indexAt(sender.pos())
        if index.isValid():
            self.digitise_table.removeRow(index.row())

    def combobox_changed(self, text):
        """
        Is linked to the combobox when a row is added

        When the combobox selected item changes (example: from dc:contributor to dc:description),
        this function is called to make the row fit its new usage. (example: enter text or a date)

        Args:
            text (str): its the active combobox selection
        """
        index = self.digitise_table.indexAt(self.sender().pos())

        comboboxes_names_counter = []
        for row in range(self.digitise_table.rowCount()):
            comboboxes_names_counter.append(self.digitise_table.cellWidget(row, 0).currentText())
        comboboxes_names_counter = Counter(comboboxes_names_counter)

        forbidden_duplicates = ["dc:description", "dcterms:created", "durée", "ratio", "format_video"]

        if text in forbidden_duplicates and comboboxes_names_counter[text] > 1:
            self.digitise_table.cellWidget(index.row(), 0).setCurrentText('dc:contributor')
            text = 'dc:contributor'
            error_box = QMessageBox()
            error_box.setText("Il est impossible d'avoir plus d'une entrée de ce type")
            error_box.setWindowTitle("Erreur")
            error_box.exec_()

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
                self.digitise_table.cellWidget(row, 1).addItems(["4:3", "16:9"])
            elif text == "format_video":
                self.digitise_table.removeCellWidget(row, 1)
                self.digitise_table.setCellWidget(row, 1, QComboBox())
                self.digitise_table.setRowHeight(row, 30)
                self.digitise_table.cellWidget(row, 1).addItems(["PAL", "SECAM", "NTSC"])
            elif text == "dc:language":
                self.digitise_table.removeCellWidget(row, 1)
                self.digitise_table.setCellWidget(row, 1, QLineEdit())
                self.digitise_table.setRowHeight(row, 30)
                self.digitise_table.cellWidget(row, 1).setInputMask("AAA")
            else:
                self.digitise_table.removeCellWidget(row, 1)
                self.digitise_table.setCellWidget(row, 1, QLineEdit())
                self.digitise_table.setRowHeight(row, 30)

    def metadata_checker(self, capture_action, data):
        """
        Check if the required metadata is present. If yes it launches the launch_capture function

        Args:
            capture_action (str): tell which capture_action the metadata_checker function should launch
                Possible values: decklink, file, DVD
            data: [digitise_infos, dublincore_dict]
        """

        # this check if at least a duration, title, and creation date is set before sending the data to the back end
        if capture_action == "decklink" and "duration" in data[1].get('dc:format', {}) \
                and "format" in data[1].get('dc:format', {}) and "dc:title" in data[1] and "dcterms:created" in data[1] \
                and self.check_remaining_space(VHS_duration=data[1]["dc:format"]["duration"]):

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
                "       la durée, un titre, le format et l'année de creation de l'oeuvre\n"
                "   Pour copier un fichier:\n"
                "       un titre et la date de création de l'oeuvre\n"
                "\n"
                "   Il faut aussi avoir sélectionné une méthode d'enregistrement (decklink, dvd...)")

            warning_box.warning(warning_box, "Attention", warning_message)
            self.launch_digitise_button.setEnabled(True)

    def check_remaining_space(self, for_DVD=None, import_file_path=None, VHS_duration=None):
        """
        Check the remaining space in the folder where the video will be saved

        Args:
            for_DVD (bool):
            import_file_path (str):
            VHS_duration (str):

        Returns:
            bool: True if successful, False otherwise.
        """

        error_text = "L'espace disque est insuffisant pour enregistrer la vidéo, " + \
                     "veuillez contacter le responsable informatique."

        if for_DVD:
            free_space = shutil.disk_usage(self.compressed_videos_path)[2]
            file_size = 15000000000  # 15GB
            if free_space - file_size < 10000000000:  # 10GB
                error_box = QMessageBox()
                error_box.setText(error_text)
                error_box.setWindowTitle("Erreur")
                error_box.exec_()
                return False
            else:
                return True
        elif import_file_path:
            free_space = shutil.disk_usage(self.imported_files_path)[2]
            file_size = os.path.getsize(import_file_path)
            if free_space - file_size < 10000000000:  # 10GB
                error_box = QMessageBox()
                error_box.setText(error_text)
                error_box.setWindowTitle("Erreur")
                error_box.exec_()
                return False
            else:
                return True
        elif VHS_duration:
            free_space = shutil.disk_usage(self.compressed_videos_path)[2]
            file_size = VHS_duration * 6.6 * 1000000000
            if free_space - file_size < 100000000000: # 100GB
                error_box = QMessageBox()
                error_box.setText(error_text)
                error_box.setWindowTitle("Erreur")
                error_box.exec_()
                return False
            else:
                return True

    def gather_metadata(self):
        """
        Gather the user provided metadata and add the constants listed below.
            dublincore_dict["dc:rights"] = "usage libre pour l'éducation"
            dublincore_dict["dc:type"] = "video"
            dublincore_dict["dcterms:modified"] = datetime.now().replace(microsecond=0).isoformat()

        Notes:
            This function also set default values for this key but it can be overridden by the user
            dublincore_dict['dc:format'] = {'aspect_ratio': '4:3', 'format': 'Non spécifié'}

        Call the 'self.metadata_checker' function with the parameter [digitise_infos, dublincore_dict]
        """

        # prevent button hammering
        self.launch_digitise_button.setEnabled(False)

        file_path = None
        if self.file_import_radio.isChecked():
            file_dialog = QFileDialog(self)
            file_path = file_dialog.getOpenFileName(directory=FILES_PATHS["home_dir"])
            file_path = file_path[0]
            print(file_path)

        dublincore_dict = dict()
        dublincore_dict["dc:format"] = {"aspect_ratio": "4:3"}

        for row in range(self.digitise_table.rowCount()):
            combobox_text = self.digitise_table.cellWidget(row, 0).currentText()
            widget_type = self.digitise_table.cellWidget(row, 1).metaObject().className()
            if widget_type == "QLineEdit":
                widget_text_value = self.digitise_table.cellWidget(row, 1).displayText()
            elif widget_type == "QTextEdit":
                widget_text_value = self.digitise_table.cellWidget(row, 1).toPlainText()
            elif widget_type == "QComboBox":
                widget_text_value = self.digitise_table.cellWidget(row, 1).currentText()

            if widget_text_value != "":
                if combobox_text == "durée":
                    dublincore_dict["dc:format"]["duration"] = int(widget_text_value) * 60  # convert minutes to seconds
                elif combobox_text == "ratio":
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
        dublincore_dict["dc:rights"] = "usage libre pour l'éducation"
        dublincore_dict["dc:type"] = "video"
        dublincore_dict["dcterms:modified"] = datetime.now().replace(microsecond=0).isoformat()

        # Handle the other infos
        capture_action = None
        digitise_infos = {}
        if self.decklink_radio_1.isChecked() and self.decklink_radio_1.isEnabled():
            digitise_infos["source"] = "decklink_1"
            digitise_infos["lossless_import"] = self.lossless_import_checkbox.isChecked()
            capture_action = "decklink"
        elif self.decklink_radio_2.isChecked() and self.decklink_radio_2.isEnabled():
            digitise_infos["source"] = "decklink_2"
            digitise_infos["lossless_import"] = self.lossless_import_checkbox.isChecked()
            capture_action = "decklink"
        elif self.file_import_radio.isChecked():
            digitise_infos["source"] = "file"
            capture_action = "file"
        elif self.dvd_import_radio.isChecked():
            digitise_infos["source"] = "DVD"
            capture_action = "DVD"

        digitise_infos["file_path"] = file_path

        to_be_send = [digitise_infos, dublincore_dict]
        print(to_be_send)

        self.metadata_checker(capture_action=capture_action, data=to_be_send)

    def tab_init(self):
        """
        Is called when the CaptureWidget class init

        Its job is to put the widgets instantiated in the init function to their place and set some signals between
         functions and buttons
        """

        grid = QGridLayout()
        self.setLayout(grid)

        #########
        self.digitise_table.setRowCount(0)
        self.digitise_table.setColumnCount(3)
        self.digitise_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.digitise_table.setColumnWidth(0, 170)
        self.digitise_table.setFont(self.table_font)
        self.digitise_table.setHorizontalHeaderLabels(["", "", ""])

        #########
        grid.addWidget(self.decklink_label, 0, 0)
        grid.addWidget(self.decklink_radio_1, 0, 1)
        grid.addWidget(self.file_import_radio, 0, 3)
        grid.addWidget(self.lossless_import_checkbox, 1, 0)
        grid.addWidget(self.decklink_radio_2, 1, 1)
        grid.addWidget(self.dvd_import_radio, 1, 3)

        grid.addWidget(self.digitise_table, 2, 0, 7, 4)
        grid.addWidget(self.new_table_row_button, 2, 5)
        grid.addWidget(self.launch_ffplay_button, 5, 5)
        grid.addWidget(self.launch_digitise_button, 8, 5)

        #########
        self.dvd_import_radio.toggled.connect(self.lossless_import_checkbox.setDisabled)
        self.dvd_import_radio.toggled.connect(self.launch_ffplay_button.setDisabled)
        self.file_import_radio.toggled.connect(self.lossless_import_checkbox.setDisabled)
        self.file_import_radio.toggled.connect(self.launch_ffplay_button.setDisabled)

        #########
        self.backend_is_alive_timer.start(15000)
        self.backend_is_alive_timer.timeout.connect(partial(self.launch_digitise_button.setDisabled, True))
        self.receive_enable_decklink_radio_1.connect(self.decklink_radio_1.setEnabled)
        self.receive_enable_decklink_radio_2.connect(self.decklink_radio_2.setEnabled)

        #########
        self.new_table_row_button.clicked.connect(self.add_table_row)
        self.launch_ffplay_button.clicked.connect(self.launch_ffplay)
        self.launch_digitise_button.clicked.connect(self.gather_metadata)

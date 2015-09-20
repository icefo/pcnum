__author__ = 'adrien'

from PyQt5.QtCore import pyqtSignal, Qt, QThread
from PyQt5.QtWidgets import (QWidget,
                             QHeaderView, QGridLayout,
                             QRadioButton, QTextEdit, QLabel, QLineEdit, QTableWidget, QComboBox,
                             QPushButton, QFileDialog, QMessageBox)
from PyQt5.QtGui import QFont
from collections import OrderedDict
from datetime import datetime
import os
import shutil
from GUI.digitise.DigitiseWidgetWorker import DigitiseWidgetWorker
from pprint import pprint
from pymongo import MongoClient
import atexit


class DigitiseWidget(QWidget):

    set_statusbar_text_1 = pyqtSignal([str])

    def __init__(self):
        # Initialize the parent class QWidget
        super().__init__()

        #########
        self.decklink_label = QLabel("Choisissez la source vidéo")
        self.decklink_radio_1 = QRadioButton("Decklink 1")
        self.decklink_radio_2 = QRadioButton("Decklink 2")
        self.file_import_radio = QRadioButton("importer fichier vidéo")
        self.dvd_import_radio = QRadioButton("importer dvd")

        #########
        self.digitise_table = QTableWidget()
        self.table_font = QFont(QFont().defaultFamily(), 12)
        self.new_table_row_button = QPushButton("Nouveau")
        self.launch_digitise_button = QPushButton("Numériser")

        #########
        # they have to be attached to the object, if not they are destroyed when the function exit
        self.worker_thread_backend_status = None
        self.worker_object_backend_status = None

        #########
        self.db_client = MongoClient("mongodb://localhost:27017/")
        metadata_db = self.db_client["metadata"]
        self.videos_metadata = metadata_db["videos_metadata"]
        ffmpeg_db = self.db_client["ffmpeg_conversions"]
        self.waiting_conversions_collection = ffmpeg_db["waiting_conversions"]

        #########
        self.raw_videos_path = "/media/storage/raw/"
        self.compressed_videos_path = "/media/storage/compressed/"
        self.imported_files_path = "/media/storage/imported/"

        #########
        self.backend_status_check()
        self.tab_init()

        atexit.register(self.cleanup)

    def cleanup(self):
        """This function is called when the DigitiseWidget class is about to be destroyed"""
        self.db_client.close()
        print("DigitiseWidget's db connection closed")

    def backend_status_check(self):

        print("backend_status_check")
        self.worker_thread_backend_status = QThread()
        self.worker_object_backend_status = DigitiseWidgetWorker()
        self.worker_object_backend_status.moveToThread(self.worker_thread_backend_status)

        self.worker_thread_backend_status.started.connect(self.worker_object_backend_status.backend_status_check)

        self.worker_object_backend_status.enable_decklink_1_radio.connect(self.decklink_radio_1.setCheckable)
        self.worker_object_backend_status.enable_decklink_1_radio.connect(self.decklink_radio_1.setEnabled)

        self.worker_object_backend_status.enable_decklink_2_radio.connect(self.decklink_radio_2.setCheckable)
        self.worker_object_backend_status.enable_decklink_2_radio.connect(self.decklink_radio_2.setEnabled)

        self.worker_object_backend_status.enable_digitize_button.connect(self.launch_digitise_button.setEnabled)
        self.worker_thread_backend_status.start()

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
                self.digitise_table.cellWidget(row, 1).setInputMask("AA")
            else:
                self.digitise_table.removeCellWidget(row, 1)
                self.digitise_table.setCellWidget(row, 1, QLineEdit())
                self.digitise_table.setRowHeight(row, 30)

    def add_row(self):
        """
        This function add a new row (Hoho !) when the new_table_row_button button is pressed
        this function will fill the combobox with their name and a tooltip,
        link the combobox to the combobox_changed function,
        link the delete button with the delete_table_row function
        :return: nothing
        """

        dc_data = OrderedDict()
        dc_data['dc:contributor'] = "nom des acteurs"
        dc_data['dc:creator'] = "maison d'édition, scénariste ou réalisateur"
        dc_data['dc:description'] = "résumé de la vidéo"
        dc_data['dc:language'] = "langue de la vidéo"
        dc_data['dc:publisher'] = "entreprise qui a publié le film, par exemple Sony Pictures"
        dc_data['dc:subject'] = "thème du film: horreur, action, histoire d'amour..."
        dc_data['dc:title'] = "titre du film"
        dc_data['dcterms:isPartOf'] = "remplir si le film fait partit d'un ensemble de films comme Star Wars"
        dc_data['dcterms:created'] = "année de sortie du film"
        dc_data['durée'] = "durée du film en minutes"
        dc_data['ratio'] = "format visuel du film"
        dc_data['format_video'] = "format video de la cassette"

        row_count = self.digitise_table.rowCount()
        self.digitise_table.insertRow(row_count)
        self.digitise_table.setCellWidget(row_count, 0, QComboBox())

        count = 0
        for dc_key, dc_tooltip in dc_data.items():
            self.digitise_table.cellWidget(row_count, 0).addItem(dc_key)
            self.digitise_table.cellWidget(row_count, 0).setItemData(count, dc_tooltip, Qt.ToolTipRole)
            count += 1

        self.digitise_table.cellWidget(row_count, 0).activated[str].connect(self.combobox_changed)
        self.digitise_table.setCellWidget(row_count, 1, QLineEdit())
        self.digitise_table.setCellWidget(row_count, 2, QPushButton("Delete"))
        self.digitise_table.cellWidget(row_count, 2).clicked.connect(self.delete_table_row)

    def launch_digitise(self, metadata):
        def get_and_lock_new_vuid():
            # set this so the first vuid will be 1
            list_of_vuids = [0]
            for post in self.videos_metadata.find({}, {"dc:identifier": True, "_id": False}):
                list_of_vuids.append(post["dc:identifier"])
            new_vuid = max(list_of_vuids) + 1
            # Use this vuid so that an other acquisition don't use it and mess up the database
            self.videos_metadata.insert({"dc:identifier": new_vuid}, fsync=True)
            return new_vuid

        print("launch digitize()")
        vuid = get_and_lock_new_vuid()
        metadata[1]["dc:identifier"] = vuid

        metadata = {"vuid": vuid, "metadata": metadata}
        pprint(metadata)
        print(self.waiting_conversions_collection.insert(metadata, fsync=True))
        self.launch_digitise_button.setEnabled(True)

    def digitise_checker(self, action, data):
        """
        :param action: tell which action the digitise_checker function should launch
        :param data: the data can be a dictionary, a list, a sting, an integer
        if the chosen action is "digitise" the parameter will be : [digitise_infos, dublincore_dict]
        digitise_infos and dublincore_dict are dictionarys

        :return: nothing, the function instantiate the DigitiseTabWorker class and then exit
        """
        # this check if at least a duration, title, and creation date is set before sending the data to the back end
        if action == "decklink" and "duration" in data[1].get('dc:format', {}) and "dc:title" in data[1] \
                and "dcterms:created" in data[1] and self.check_remaining_space(duration=data[1]["dc:format"]["duration"]):

            self.launch_digitise_button.setEnabled(False)

            if data[0]["source"] == "decklink_1":
                self.decklink_radio_1.setEnabled(False)
            elif data[0]["source"] == "decklink_2":
                self.decklink_radio_2.setEnabled(False)
            else:
                raise ValueError

            self.launch_digitise(metadata=data)
            # set status bar temp text
            self.set_statusbar_text_1.emit("Numérisation Decklink lancée")

            if data[0]["source"] == "decklink_1":
                self.decklink_radio_1.setEnabled(True)
            elif data[0]["source"] == "decklink_2":
                self.decklink_radio_2.setEnabled(True)
            else:
                raise ValueError

        elif action == "file" and "filename" in data[0] and "dc:title" in data[1] and "dcterms:created" in data[1] \
                and self.check_remaining_space(import_filename=data[0]["filename"]):

            self.launch_digitise_button.setEnabled(False)

            self.launch_digitise(metadata=data)

            self.set_statusbar_text_1.emit("Enregistrement du fichier lancé !")

        elif action == "DVD" and "filename" in data[0] and "dc:title" in data[1] and "dcterms:created" in data[1] \
                and self.check_remaining_space(DVD_filename=data[0]["filename"]):

            self.launch_digitise_button.setEnabled(False)

            self.launch_digitise(metadata=data)

            self.set_statusbar_text_1.emit("Enregistrement du DVD lancé !")
        else:
            warning_box = QMessageBox()
            warning_message = "Les informations suivantes sont necessaires:\n" + \
                            "Pour enregistrer un dvd:\n" + \
                                "    un titre et la date de creation de l'oeuvre\n" + \
                            "Pour enregistrer une cassette:\n" + \
                                "    la durée, un titre et la date de creation de l'oeuvre\n" + \
                            "\n" + \
                            "Il faut aussi:\n" \
                            "   Avoir sélectionné une méthode d'enregistrement (decklink, dvd..."

            warning_box.warning(warning_box, "Attention", warning_message)

    def check_remaining_space(self, DVD_filename=None, import_filename=None, duration=None):
        error_text = "L'espace disque est insuffisant pour enregistrer la vidéo, " + \
                     "veuillez contacter le responsable informatique."

        if DVD_filename:
            free_space = shutil.disk_usage(self.compressed_videos_path)[2]
            file_size = os.path.getsize(DVD_filename)
            if free_space - file_size < 10000000000: # 10GB
                error_box = QMessageBox()
                error_box.setText(error_text)
                error_box.setWindowTitle("Erreur")
                error_box.exec_()
            else:
                return True
        elif import_filename:
            free_space = shutil.disk_usage(self.imported_files_path)[2]
            file_size = os.path.getsize(import_filename)
            if free_space - file_size < 10000000000: # 10GB
                error_box = QMessageBox()
                error_box.setText(error_text)
                error_box.setWindowTitle("Erreur")
                error_box.exec_()
            else:
                return True
        elif duration:
            free_space = shutil.disk_usage(self.compressed_videos_path)[2]
            file_size = duration * 6.6 * 1000000000
            if free_space - file_size < 10000000000: # 10GB
                error_box = QMessageBox()
                error_box.setText(error_text)
                error_box.setWindowTitle("Erreur")
                error_box.exec_()
            else:
                return True

    def digitise(self):
        """
        This function wil gather all the metadata, add the constants listed below.

        # Handle the dublincore metadata
        # dc:rights = usage libre pour l'éducation
        # dc:type = "image"
        # dcterms:modified = date de la numérisation
        # dc:identifier = id incremental pour chaque VHS
        # dc:format = {"size_ratio": "4/3", "duration": temps}

        :return: nothing but call the digitise_checker function with the parameter [digitise_infos, dublincore_dict]
        """
        # prevent button hammering
        self.launch_digitise_button.setEnabled(False)

        filename = None
        if self.dvd_import_radio.isChecked():
            file_dialog = QFileDialog(self)
            filename = file_dialog.getOpenFileName(directory="/media/storage", filter="MKV files (*.mkv)")
            filename = filename[0]
            print(filename)
        elif self.file_import_radio.isChecked():
            file_dialog = QFileDialog(self)
            filename = file_dialog.getOpenFileName(directory="/media/storage")
            filename = filename[0]
            print(filename)

        dublincore_dict = {}
        dublincore_dict["dc:format"] = {"size_ratio": "4:3"}
        dublincore_dict["format_video"] = "PAL"

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
                    dublincore_dict["dc:format"]["duration"] = int(widget_text_value) * 60  # convert minutes to seconds
                elif combobox_text == "ratio":
                    dublincore_dict["dc:format"]["size_ratio"] = widget_text_value
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
        worker_action = None
        digitise_infos = {}
        if self.decklink_radio_1.isChecked():
            digitise_infos["source"] = "decklink_1"
            worker_action = "decklink"
        elif self.decklink_radio_2.isChecked():
            digitise_infos["source"] = "decklink_2"
            worker_action = "decklink"
        elif self.file_import_radio.isChecked():
            digitise_infos["source"] = "file"
            worker_action = "file"
        elif self.dvd_import_radio.isChecked():
            digitise_infos["source"] = "DVD"
            worker_action = "DVD"

        # digitise_infos["H264"] = self.compressed_file_h264.isChecked()
        # digitise_infos["H265"] = self.compressed_file_h265.isChecked()

        digitise_infos["filename"] = filename
        # digitise_infos["package_mediatheque"] = self.package_mediatheque.isChecked()

        to_be_send = [digitise_infos, dublincore_dict]
        print(to_be_send)

        self.digitise_checker(action=worker_action, data=to_be_send)

    def tab_init(self):
        """
        This function is called when the DigitiseWidget class init
        Its job is to put the widgets instantiated in the init function to their place and
        set some link between functions and buttons
        :return: nothing
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
        grid.addWidget(self.decklink_radio_2, 1, 1)
        grid.addWidget(self.file_import_radio, 0, 2)
        grid.addWidget(self.dvd_import_radio, 0, 3)

        grid.addWidget(self.digitise_table, 3, 0, 5, 2)
        grid.addWidget(self.new_table_row_button, 3, 3)
        grid.addWidget(self.launch_digitise_button, 5, 3)

        #########
        self.new_table_row_button.clicked.connect(self.add_row)
        self.launch_digitise_button.clicked.connect(self.digitise)

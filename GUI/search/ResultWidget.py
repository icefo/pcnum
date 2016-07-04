from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QPushButton, QGridLayout, QTreeWidget, QTreeWidgetItem, QTextBrowser, QMessageBox
from PyQt5.QtGui import QFont
import subprocess
from pymongo import MongoClient
import atexit
import os


class ResultWidget(QWidget):
    """
    This QWidget display the search results

    Attributes:
        self.show_search_widget_signal (pyqtSignal()): Is used to ask the MainSearchWidget to display the SearchWidget
        self.show_edit_widget_signal (pyqtSignal()): Is used to ask the MainSearchWidget to display the EditWidget

        self.request_refresh_signal (pyqtSignal()): Is used to ask the SearchWidget to rerun the search after a deletion

        self.receive_search_results (pyqtSignal([list])): List of dict sent after a search by the SearchWidget
        self.send_dc_identifier (pyqtSignal([str])): Is used to send the dc:identifier to the EditWidget
    """

    show_search_widget_signal = pyqtSignal()
    show_edit_widget_signal = pyqtSignal()

    request_refresh_signal = pyqtSignal()

    receive_search_results = pyqtSignal([list])
    send_dc_identifier = pyqtSignal([str])

    def __init__(self):
        super().__init__()

        #########
        self.search_results_tree = QTreeWidget()
        self.result_font = QFont(QFont().defaultFamily(), 12)

        #########
        self.return_to_search_button = QPushButton('Retour')
        self.delete_video_button = QPushButton('Supprimer')
        self.edit_record_button = QPushButton('Modifier')

        #########
        # litle hack to set the label of each result; sort of global variable
        self.movie_title = ""
        self.movie_creation_date = ""

        #########
        self.db_client = MongoClient("mongodb://localhost:27017/")
        digitize_app = self.db_client['digitize_app']
        self.videos_metadata_collection = digitize_app['videos_metadata']

        #########
        self.tab_init()
        atexit.register(self.cleanup)

    def cleanup(self):
        """
        Is called when the DigitiseWidgetWorker class is about to be destroyed
        """

        self.db_client.close()
        print("ResultWidget's db connection closed")

    def handle_doubleclick(self):
        """
        Launch vlc in a separate process when the user double click on a file path
        """

        selected_item = self.search_results_tree.currentItem()
        selected_item_parent = selected_item.parent().text(0)

        if selected_item_parent == "files_path":
            # unknown: /media/storage/imported/le beau fichier importé: -- 4.mkv
            file_or_dir_path = "".join(selected_item.text(0).split(": ")[1:])
            print(file_or_dir_path)
            command = ['vlc', '--quiet', file_or_dir_path]
            subprocess.Popen(command, stdout=None)

    def delete_video(self):
        """
        Delete a video after requesting user confirmation
        """

        selected_item_parent = None
        dc_identifier = None
        try:
            selected_item = self.search_results_tree.currentItem()
            selected_item_parent = selected_item.parent().text(0)
            dc_identifier = selected_item.text(0)
            print(dc_identifier)
            if not selected_item_parent == "dc:identifier":
                raise ValueError
        except (AttributeError, ValueError):
            error_box = QMessageBox()
            error_message = "Vous devez sélectionner l'identifiant sous dc:identifier"

            error_box.setText(error_message)
            error_box.setWindowTitle("Erreur")
            error_box.exec_()

        if selected_item_parent == "dc:identifier":
            warning_box = QMessageBox()
            warning_message = "Etes vous sûr de vouloir supprimer cette vidéo ?\n" + \
                              "Cette action est irreversible"

            reply = warning_box.warning(warning_box, 'Attention', warning_message, QMessageBox.Yes | QMessageBox.No,
                                        QMessageBox.No)

            if reply == QMessageBox.Yes and dc_identifier:
                video_metadata = self.videos_metadata_collection.find_one({"dc:identifier": dc_identifier})
                delete_folder = False
                for folder_or_file, path in video_metadata["files_path"].items():
                    print(path)
                    if folder_or_file == "folder":
                        os.rmdir(path)
                    else:
                        os.remove(path)

                self.videos_metadata_collection.delete_one({"dc:identifier": dc_identifier}, fsync=True)
                self.request_refresh_signal.emit()

    def edit_record(self):
        """
        Check that the user selected the dc:identifier field and make the EditWidget show up
        """

        selected_item_parent = None
        dc_identifier = None
        try:
            selected_item = self.search_results_tree.currentItem()
            selected_item_parent = selected_item.parent().text(0)
            dc_identifier = selected_item.text(0)
            print(dc_identifier)
            if selected_item_parent == "dc:identifier":
                self.send_dc_identifier.emit(dc_identifier)
                self.show_edit_widget_signal.emit()
            else:
                raise ValueError

        except (AttributeError, ValueError):
            error_box = QMessageBox()
            error_message = "Vous devez sélectionner l'identifiant sous dc:identifier"

            error_box.setText(error_message)
            error_box.setWindowTitle("Erreur")
            error_box.exec_()

    def search_done(self, search_results):
        """
        Display the search results send by the SearchWidget in a QTreeWidget

        Args:
            search_results (list): list of dictionary
                [{'dc:type': 'video', 'dcterms:modified': '2015-10-29T02:13:30',
                'files_path': {'h264': file_path}, 'dc:title': ['the title']}]
        """

        print(search_results)
        self.search_results_tree.clear()

        for result in search_results:
            result_tree = QTreeWidgetItem()
            self.movie_title = ""
            self.movie_creation_date = ""
            for key, value in result.items():
                if key == "dc:title":
                    self.movie_title = value
                elif key == "dcterms:created":
                    self.movie_creation_date = str(value)

                dc_tree = QTreeWidgetItem()
                dc_tree.setText(0, key)
                if isinstance(value, list):
                    if key == "dc:description":
                        for x in value:
                            item = QTreeWidgetItem()
                            text_browser = QTextBrowser()
                            text_browser.setText(str(x))
                            text_browser.setMinimumHeight(0)
                            text_browser.setMaximumHeight(100)
                            dc_tree.addChild(item)
                            self.search_results_tree.setItemWidget(item, 0, text_browser)
                    else:
                        for x in value:
                            item = QTreeWidgetItem()
                            item.setText(0, str(x))
                            dc_tree.addChild(item)
                elif isinstance(value, dict):
                    for key1, value2 in value.items():
                        item = QTreeWidgetItem()
                        if key1 == "duration":
                            blup = str(key1) + ": " + str(value2/60)  # convert seconds to minutes
                        else:
                            blup = str(key1) + ": " + str(value2)
                        item.setText(0, blup)
                        dc_tree.addChild(item)
                elif key == "dc:description":
                    item = QTreeWidgetItem()
                    text_browser = QTextBrowser()
                    text_browser.setText(str(value))
                    text_browser.setMinimumHeight(0)
                    text_browser.setMaximumHeight(100)
                    dc_tree.addChild(item)
                    self.search_results_tree.setItemWidget(item, 0, text_browser)
                else:
                    item = QTreeWidgetItem()
                    item.setText(0, str(value))
                    dc_tree.addChild(item)
                result_tree.addChild(dc_tree)
            result_tree.setText(0, self.movie_title[0] + " -- " + self.movie_creation_date)
            self.search_results_tree.addTopLevelItem(result_tree)
        # 0 == column, 0 == sort_order // 1 to reverse_sort
        self.search_results_tree.sortItems(0, 0)

    def tab_init(self):
        """
        Is called when the ResultWidget class init

        Its job is to put the widgets instantiated in the init function to their place and set some link between
         functions and buttons
        """

        grid = QGridLayout()
        self.setLayout(grid)

        #########
        self.search_results_tree.setFont(self.result_font)
        self.search_results_tree.setHeaderLabel("")

        #########
        grid.addWidget(self.search_results_tree, 0, 0, 3, 2)
        grid.addWidget(self.delete_video_button, 4, 0)
        grid.addWidget(self.return_to_search_button, 4, 1)

        #########
        self.return_to_search_button.clicked.connect(self.show_search_widget_signal.emit)

        self.search_results_tree.itemDoubleClicked.connect(self.handle_doubleclick)

        self.delete_video_button.clicked.connect(self.delete_video)
        self.edit_record_button.clicked.connect(self.edit_record)

        self.receive_search_results.connect(self.search_done)

__author__ = 'adrien'

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QPushButton, QGridLayout, QTreeWidget, QTreeWidgetItem, QTextBrowser, QMessageBox
from PyQt5.QtGui import QFont
import subprocess
from pymongo import MongoClient
import atexit
import os


class ResultWidget(QWidget):
    show_search_widget_signal = pyqtSignal()
    request_refresh = pyqtSignal()
    receive_list = pyqtSignal([list])

    def __init__(self):
        super().__init__()

        #########
        self.display_result = QTreeWidget()
        self.result_font = QFont(QFont().defaultFamily(), 12)

        #########
        self.return_to_search_button = QPushButton('Back')
        self.delete_video_button = QPushButton('Supprimer')

        #########
        # litle hack to set the label of each result; sort of global variable
        self.movie_title = ""
        self.movie_creation_date = ""

        #########
        self.db_client = MongoClient("mongodb://localhost:27017/")
        metadata_db = self.db_client["metadata"]
        self.videos_metadata_collection = metadata_db["videos_metadata"]

        #########
        self.tab_init()
        atexit.register(self.cleanup)

    def cleanup(self):
        """
        This function is called when the DigitiseWidgetWorker class is about to be destroyed

        :return:
        """
        self.db_client.close()
        print("ResultWidget's db connection closed")

    def launch_vlc(self):
        """
        This function launch vlc in a separate process when the user double click on a file path

        :return:
        """
        selected_item = self.display_result.currentItem().text(0)

        if selected_item.startswith("h264: ") or selected_item.startswith("unknown: "):
            # unknown: /media/storage/imported/le beau fichier importé: -- 4.mkv
            file_path = "".join(selected_item.split(": ")[1:])
            print(file_path)
            shell_command = ['vlc', '--quiet', file_path]
            subprocess.Popen(shell_command, stdout=None)

    def delete_video(self):
        """
        This function delete a video after requesting user confirmation

        :return:
        """
        selected_item_parent = None
        dc_identifier = None
        try:
            selected_item = self.display_result.currentItem()
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
                try:
                    file_path = video_metadata["files_path"]["h264"]
                except KeyError:
                    file_path = video_metadata["files_path"]["unknown"]
                os.remove(file_path)
                self.videos_metadata_collection.remove(spec_or_id={"dc:identifier": dc_identifier}, fsync=True)
                self.request_refresh.emit()

    def search_done(self, search_results):
        """
        This function display the search results send by the SearchWidget
        :param search_results: list of dictionary
        :return:
        """
        self.display_result.clear()

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
                            self.display_result.setItemWidget(item, 0, text_browser)
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
                    self.display_result.setItemWidget(item, 0, text_browser)
                else:
                    item = QTreeWidgetItem()
                    item.setText(0, str(value))
                    dc_tree.addChild(item)
                result_tree.addChild(dc_tree)
            result_tree.setText(0, self.movie_title[0] + " -- " + self.movie_creation_date)
            self.display_result.addTopLevelItem(result_tree)
        # 0 == column, 0 == sort_order // 1 to reverse_sort
        self.display_result.sortItems(0, 0)

    def tab_init(self):
        """
        This function is called when the DigitiseWidget class init
        Its job is to put the widgets instantiated in the init function to their place and
        set some link between functions and buttons

        :return:
        """
        grid = QGridLayout()
        self.setLayout(grid)

        #########
        self.display_result.setFont(self.result_font)
        self.display_result.setHeaderLabel("")

        #########
        grid.addWidget(self.display_result, 0, 0, 3, 2)
        grid.addWidget(self.delete_video_button, 4, 0)
        grid.addWidget(self.return_to_search_button, 4, 1)

        #########
        self.return_to_search_button.clicked.connect(self.show_search_widget_signal.emit)
        self.display_result.itemDoubleClicked.connect(self.launch_vlc)
        self.delete_video_button.clicked.connect(self.delete_video)
        self.receive_list.connect(self.search_done)

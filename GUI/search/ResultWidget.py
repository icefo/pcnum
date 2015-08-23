__author__ = 'adrien'

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QPushButton, QGridLayout, QTreeWidget, QTreeWidgetItem, QTextBrowser
from PyQt5.QtGui import QFont

class ResultWidget(QWidget):
    show_search_widget_signal = pyqtSignal()
    receive_list = pyqtSignal([list])

    def __init__(self):
        super().__init__()

        self.display_result = QTreeWidget()
        self.result_font = QFont(QFont().defaultFamily(), 12)
        self.return_to_search_button = QPushButton('Back')

        # litle hack to set the label of each result; sort of global variable
        self.movie_title = ""
        self.movie_creation_date = ""

        self.tab_init()

    def search_done(self, search_results):
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
        result_widget_layout = QGridLayout()
        self.setLayout(result_widget_layout)

        self.display_result.setFont(self.result_font)
        self.display_result.setHeaderLabel("")

        result_widget_layout.addWidget(self.display_result, 0, 0, 3, 2)
        result_widget_layout.addWidget(self.return_to_search_button, 4, 1)

        self.return_to_search_button.clicked.connect(self.show_search_widget_signal.emit)
        self.receive_list.connect(self.search_done)

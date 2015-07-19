__author__ = 'adrien'

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from functools import partial
from GUI.search.SearchWidget import SearchWidget
from GUI.search.ResultWidget import ResultWidget

class MainSearchWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.search_widget = SearchWidget()
        self.result_widget = ResultWidget()
        self.stack = QStackedWidget()
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        layout.addWidget(self.stack)

        self.stack.addWidget(self.search_widget)
        self.stack.addWidget(self.result_widget)

        self.search_widget.show_result_widget_signal.connect(partial(self.stack.setCurrentWidget, self.result_widget))
        self.search_widget.search_transmit.connect(self.result_widget.receive_list)
        self.result_widget.show_search_widget_signal.connect(partial(self.stack.setCurrentWidget, self.search_widget))

        self.stack.setCurrentWidget(self.search_widget)

__author__ = 'adrien'

from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QLineEdit, QGridLayout


class ResultWidget(QWidget):
    show_search_widget_signal = QtCore.pyqtSignal()
    # receive_text = QtCore.pyqtSignal([str])

    def __init__(self):
        super().__init__()
        widget_layout = QGridLayout()
        self.setLayout(widget_layout)

        line_edit = QLabel()
        # self.receive_text.connect(line_edit.setText)
        widget_layout.addWidget(line_edit, 0, 0)
        self.button = QPushButton('Back')
        widget_layout.addWidget(self.button, 0, 1)
        self.button.clicked.connect(self.show_search_widget_signal.emit)
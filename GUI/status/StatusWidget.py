__author__ = 'adrien'
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QWidget,
                             QHeaderView, QGridLayout,
                             QRadioButton, QTextEdit, QLabel, QLineEdit, QCheckBox, QTableWidget, QComboBox, QPushButton)
from PyQt5.QtGui import QFont
from collections import OrderedDict
from datetime import datetime
from functools import partial

class StatusWidget(QWidget):
    def __init__(self):
        # Initialize the parent class QWidget
        super().__init__()

        self.label = QLabel("elelellee")

        self.tab_init()

    def tab_init(self):
        grid = QGridLayout()
        self.setLayout(grid)

        grid.addWidget(self.label, 0, 0)
__author__ = 'adrien'
import sys
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QApplication, QLineEdit, QGridLayout, QStackedWidget
from functools import partial

# thx dude: http://stackoverflow.com/questions/9314095/pyqt-how-to-set-up-a-widget-hidding-an-other-widget-if-its-visible
# less hacky http://stackoverflow.com/questions/7690677/pyqt-widgets-in-multiple-files
# this is the good version


class SenderWidget(QWidget):
    show_receiver_widget_signal = QtCore.pyqtSignal()
    send_text = QtCore.pyqtSignal([str])

    def __init__(self):
        super().__init__()
        widget_layout = QGridLayout()
        self.setLayout(widget_layout)

        self.line_edit = QLineEdit()
        widget_layout.addWidget(self.line_edit, 0, 0)
        self.button = QPushButton('Send')
        widget_layout.addWidget(self.button, 0, 1)
        self.button.clicked.connect(self.do_test)
        self.button.clicked.connect(self.show_receiver_widget_signal.emit)

    def do_test(self):
        text = self.line_edit.displayText()
        self.send_text.emit(text)


class ReceiverWidget(QWidget):
    show_sender_widget_signal = QtCore.pyqtSignal()
    receive_text = QtCore.pyqtSignal([str])

    def __init__(self):
        super().__init__()
        widget_layout = QGridLayout()
        self.setLayout(widget_layout)

        line_edit = QLabel()
        self.receive_text.connect(line_edit.setText)
        widget_layout.addWidget(line_edit, 0, 0)
        self.button = QPushButton('Back')
        widget_layout.addWidget(self.button, 0, 1)
        self.button.clicked.connect(self.show_sender_widget_signal.emit)


class MainWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.sender_widget = SenderWidget()
        self.receiver_widget = ReceiverWidget()
        self.stack = QStackedWidget()
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        layout.addWidget(self.stack)

        self.stack.addWidget(self.sender_widget)
        self.stack.addWidget(self.receiver_widget)

        self.sender_widget.show_receiver_widget_signal.connect(partial(self.stack.setCurrentWidget, self.receiver_widget))
        self.receiver_widget.show_sender_widget_signal.connect(partial(self.stack.setCurrentWidget, self.sender_widget))

        self.sender_widget.send_text.connect(self.receiver_widget.receive_text)

        # some test code
        self.stack.setCurrentWidget(self.receiver_widget)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWidget()
    widget.resize(640, 480)
    widget.show()

    sys.exit(app.exec_())
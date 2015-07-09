import sys
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QApplication, QLineEdit, QGridLayout

# thx dude: http://stackoverflow.com/questions/9314095/pyqt-how-to-set-up-a-widget-hidding-an-other-widget-if-its-visible
# less hacky http://stackoverflow.com/questions/7690677/pyqt-widgets-in-multiple-files
# this is th hacky version


class SenderWidget(QWidget):
    signal_hided = QtCore.pyqtSignal()
    signal_shown = QtCore.pyqtSignal()
    send_text = QtCore.pyqtSignal([str])

    def __init__(self):
        super().__init__()
        widget_layout = QGridLayout()
        self.line_edit = QLineEdit()
        widget_layout.addWidget(self.line_edit, 0, 0)
        self.button = QPushButton('Send')
        widget_layout.addWidget(self.button, 0, 1)
        self.button.clicked.connect(self.do_test)
        self.setLayout(widget_layout)

    def hideEvent(self, event):
        print('SenderWidget hideEvent')
        super(SenderWidget, self).hideEvent(event)
        self.signal_hided.emit()

    def showEvent(self, event):
        print('SenderWidget showEvent')
        super(SenderWidget, self).showEvent(event)
        self.signal_shown.emit()

    def do_test(self):
        text = self.line_edit.displayText()
        self.send_text.emit(text)
        self.hide()


class ReceiverWidget(QWidget):
    signal_hided = QtCore.pyqtSignal()
    signal_shown = QtCore.pyqtSignal()
    receive_text = QtCore.pyqtSignal([str])

    def __init__(self):
        super().__init__()
        widget_layout = QGridLayout()
        line_edit = QLabel()
        self.receive_text.connect(line_edit.setText)
        widget_layout.addWidget(line_edit, 0, 0)
        self.button = QPushButton('Back')
        widget_layout.addWidget(self.button, 0, 1)
        self.button.clicked.connect(self.hide)
        self.setLayout(widget_layout)
        # Hide the widget on init, happen only once
        self.hide()

    def hideEvent(self, event):
        print('ReceiverWidget hideEvent')
        super(ReceiverWidget, self).hideEvent(event)
        self.signal_hided.emit()

    def showEvent(self, event):
        print('ReceiverWidget showEvent')
        super(ReceiverWidget, self).showEvent(event)
        self.signal_shown.emit()


class MainWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.sender_widget = SenderWidget()
        self.receiver_widget = ReceiverWidget()

        # connect signals, so if one widget is hidden then other is shown
        self.sender_widget.signal_hided.connect(self.receiver_widget.show)
        self.receiver_widget.signal_hided.connect(self.sender_widget.show)

        # self.receiver_widget.signal_shown.connect(self.sender_widget.hide)
        # self.sender_widget.signal_shown.connect(self.receiver_widget.hide)

        self.sender_widget.send_text.connect(self.receiver_widget.receive_text)

        # some test code
        layout = QVBoxLayout()
        layout.addWidget(self.sender_widget)
        layout.addWidget(self.receiver_widget)
        self.setLayout(layout)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWidget()
    widget.resize(640, 480)
    widget.show()

    sys.exit(app.exec_())
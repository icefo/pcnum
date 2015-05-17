import sys
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QApplication, QLineEdit, QGridLayout

# thx dude: http://stackoverflow.com/questions/9314095/pyqt-how-to-set-up-a-widget-hidding-an-other-widget-if-its-visible

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
        print('hideEvent')
        super(SenderWidget, self).hideEvent(event)
        self.signal_hided.emit()

    def showEvent(self, event):
        print('showEvent')
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

    def hideEvent(self, event):
        print('hideEvent')
        super(ReceiverWidget, self).hideEvent(event)
        self.signal_hided.emit()

    def showEvent(self, event):
        print('showEvent')
        super(ReceiverWidget, self).showEvent(event)
        self.signal_shown.emit()


class MainWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.widget1 = SenderWidget()
        self.widget2 = ReceiverWidget()

        # connect signals, so if one widget is hidden then other is shown
        self.widget1.signal_hided.connect(self.widget2.show)
        self.widget2.signal_hided.connect(self.widget1.show)
        self.widget2.signal_shown.connect(self.widget1.hide)
        self.widget1.signal_shown.connect(self.widget2.hide)

        self.widget1.send_text.connect(self.widget2.receive_text)

        # some test code
        layout = QVBoxLayout()
        layout.addWidget(self.widget1)
        layout.addWidget(self.widget2)
        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWidget()
    widget.resize(640, 480)
    widget.show()

    sys.exit(app.exec_())
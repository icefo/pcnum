__author__ = 'adrien'

import sys

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QWidget, QLineEdit, QGridLayout

import setproctitle
from autobahn.asyncio.wamp import ApplicationRunner
from autobahn.asyncio.wamp import ApplicationSession
from asyncio import coroutine
from quamash import QEventLoop, QThreadExecutor
import asyncio
from functools import partial


class MainWindow(ApplicationSession, QMainWindow):

    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        QMainWindow.__init__(self)

        self.the_widget = MainWidget()

        #########
        self.main_window_init()

    @coroutine
    def onJoin(self, details):
        print("session ready")
        try:
            res = yield from self.call('com.myapp.add2', 6, 3)
            print("call result: {}".format(res))
        except Exception as e:
            print("call error: {0}".format(e))

    def main_window_init(self):

        self.the_widget.push_button_clicked.connect(self.main_widget_button_clicked)
        self.setCentralWidget(self.the_widget)

        #########
        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('gui_wamp_test')
        self.show()

    def main_widget_button_clicked(self):

        @coroutine
        def call_it_baby():
            print("call it baby !")
            res = yield from self.call('com.myapp.add2', 6, 4)
            print("I called baby ! ", res)

            self.the_widget.push_button_answer.emit(str(res))

        asyncio.async(call_it_baby())


class MainWidget(QWidget):

    push_button_clicked = pyqtSignal()
    push_button_answer = pyqtSignal([str])

    def __init__(self):
        QWidget.__init__(self)

        self.widget_init()

    def widget_init(self):
        grid = QGridLayout()
        self.setLayout(grid)

        push_button = QPushButton("push push push !")
        push_button.clicked.connect(self.push_button_clicked)

        line_edit = QLineEdit()
        self.push_button_answer.connect(line_edit.setText)

        grid.addWidget(push_button, 0, 0)
        grid.addWidget(line_edit, 1, 0)

if __name__ == "__main__":
    qapp = QApplication(sys.argv)

    loop = QEventLoop(qapp)
    asyncio.set_event_loop(loop)

    runner = ApplicationRunner(url = "ws://127.0.0.1:8080/ws", realm = "realm1")
    runner.run(MainWindow)

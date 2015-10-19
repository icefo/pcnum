__author__ = 'adrien'

import sys

from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton

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

        #########
        self.main_window_init()

    @coroutine
    def onJoin(self, details):
        print("session ready")
        try:
            res = yield from self.call('com.myapp.add2', 6, 3)
            print("call result: {}".format(res))
            self.buttonpushed()
        except Exception as e:
            print("call error: {0}".format(e))

    def main_window_init(self):

        button = QPushButton("push push push !")
        button.clicked.connect(self.buttonpushed)
        self.setCentralWidget(button)

        #########
        self.setGeometry(300, 300, 200, 200)
        self.setWindowTitle('gui_wamp_test')
        self.show()

    def buttonpushed(self):

        @coroutine
        def call_it_baby():
            print("he pushed it !")
            res = yield from self.call('com.myapp.add2', 6, 4)
            print(res)

        asyncio.async(call_it_baby())

if __name__ == "__main__":
    qapp = QApplication(sys.argv)

    loop = QEventLoop(qapp)
    asyncio.set_event_loop(loop)

    runner = ApplicationRunner(url = "ws://127.0.0.1:8080/ws", realm = "realm1")
    runner.run(MainWindow)

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import sys
import xmlrpc.client
from time import sleep

# fallait directement integrer ça dans l'application pyqt5 et pas essayer d'en faire un module importable
# very testable class (hint: you can use mock.Mock for the signals)
class Worker(QtCore.QObject):

    client = xmlrpc.client.ServerProxy('http://localhost:8000')

    launch_digitise_done = QtCore.pyqtSignal(list)


    @QtCore.pyqtSlot(list)
    def launch_digitise(self, listo):
        print("briedge dicoo()")
        return_status = self.client.launch_digitise(listo)
        # self.dataReady.emit(['dummy', 'data'], {'dummy': ['data']})
        self.launch_digitise_done.emit(return_status)


class MetaStuff():
    def __init__(self):
        self.app = QApplication(sys.argv)

        self.thread = QtCore.QThread()  # no parent!
        self.worker = Worker()  # no parent!
        self.worker.launch_digitise_done.connect(self.launch_digitise_done)

        self.worker.moveToThread(self.thread)

        # if you want the thread to stop after the worker is done
        # you can always call thread.start() again later
        # obj.finished.connect(thread.quit)

        # one way to do it is to start processing as soon as the thread starts
        # this is okay in some cases... but makes it harder to send data to
        # the worker object from the main gui thread.  As you can see I'm calling
        # processA() which takes no arguments
        # thread.started.connect(obj.processA)

        self.thread.finished.connect(self.app.exit)

        self.thread.start()
        self.app.exec_()



    def launch_digitise_done(self, arg):
        print('onDataReady')
        print(arg[0])


    def terminate_worker(self):
        self.thread.quit()
        self.app.exit()

    def maman(self):
        QtCore.QMetaObject.invokeMethod(self.worker, 'launch_digitise', Qt.QueuedConnection,
                                QtCore.Q_ARG(list, [{"hbh":"jhvb"}, {"ghvghvki":18}]))


# another way to do it, which is a bit fancier, allows you to talk back and
# forth with the object in a thread safe way by communicating through signals
# and slots (now that the thread is running I can start calling methods on
# the worker object)



#QtCore.QMetaObject.invokeMethod(worker, 'launch_digitise', Qt.QueuedConnection,
#                                QtCore.Q_ARG(list, [{"hbh":"jhvb"}, {"ghvghvki":18}]))

# that looks a bit scary, but its a totally ok thing to do in Qt,
# we're simply using the system that Signals and Slots are built on top of,
# the QMetaObject, to make it act like we safely emitted a signal for
# the worker thread to pick up when its event loop resumes (so if its doing
# a bunch of work you can call this method 10 times and it will just queue
# up the calls.  Note: PyQt > 4.6 will not allow you to pass in a None
# instead of an empty list, it has stricter type checking
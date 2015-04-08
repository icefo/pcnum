from autobahn.asyncio.wamp import ApplicationRunner
from autobahn.asyncio.wamp import ApplicationSession
from asyncio import coroutine
import asyncio
import struct
import threading
import queue

class MyComponent(ApplicationSession):

    @coroutine
    def onJoin(self, details):
        print("session ready")

    @coroutine
    def myfunc(self, bla):
        print(bla)
        try:
            res = yield from self.call("com.myapp.add2", 6, 3)
            print("call result: {}".format(res))
        except Exception as e:
            print("call error: {0}".format(e))

class SocketClientThread(threading.Thread):
    """ Implements the threading.Thread interface (start, join, etc.) and
        can be controlled via the cmd_q queue attribute. Replies are placed in
        the reply_q queue attribute.
    """
    def __init__(self, cmd_q=queue.Queue(), reply_q=queue.Queue()):
        super(SocketClientThread, self).__init__()
        self.cmd_q = cmd_q
        self.reply_q = reply_q
        self.alive = threading.Event()
        self.alive.set()
        self.runner = ApplicationRunner(url = "ws://127.0.0.1:8080/ws", realm = "realm1")


    def run(self):

        self.sess = self.runner.run(MyComponent)
        MyComponent.myfunc(self.runner.run(MyComponent), "jhvjh")
        while self.alive.isSet():
            try:
                self.runner.loop.run_until_complete(self.sess.myfunc(self.sess, "bla"))
                # queue.get with timeout to allow checking self.alive
                #cmd = self.cmd_q.get(True, 0.1)
                #self.handlers[cmd.type](cmd)
            except queue.Empty as e:
                continue


SocketClientThread().run()


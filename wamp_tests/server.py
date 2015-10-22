from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
import asyncio
from datetime import datetime
import signal
from autobahn import wamp

CLOSING_TIME = False


class MyComponent(ApplicationSession):

    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)

    @wamp.register("com.myapp.add2")
    def add2(self, x, y):
        result = x + y
        print(str(x) + " + " + str(y) + " = " + str(result))

        return result

    @asyncio.coroutine
    def onJoin(self, details):
        print("session ready")

        try:
            res = yield from self.register(self)
            print("{0} procedures registered".format(len(res)))
        except Exception as e:
            print("could not register procedure: {0}".format(e))

        asyncio.async(self.time_teller())

        asyncio.async(self.exit_cleanup())

    @asyncio.coroutine
    def time_teller(self):
        while True:
            time_today = str(datetime.now().replace(microsecond=0))
            self.publish('com.myapp.the_time', time_today)
            yield from asyncio.async(asyncio.sleep(2))

    @asyncio.coroutine
    def exit_cleanup(self):
        while True:
            yield from asyncio.sleep(2)
            if CLOSING_TIME is True:
                print("hes")
                break

        loopy = asyncio.get_event_loop()
        for task in asyncio.Task.all_tasks():
            # this is to avoid the cancellation of this coroutine because this coroutine need to be the last one running
            # to cancel all the others.
            if task is not asyncio.Task.current_task():
                task.cancel()

        # little trick to allow the event loop to process the cancel events
        yield from asyncio.sleep(1)

        with open("/home/adrien/" + "testfile.txt", "w"):
                kkll = True

        loopy.stop()


class GracefulKiller:

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        global CLOSING_TIME
        CLOSING_TIME = True


if __name__ == "__main__":
    killer = GracefulKiller()
    runner = ApplicationRunner(url="ws://127.0.0.1:8080/ws", realm="realm1")
    runner.run(MyComponent)

from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
import asyncio
from datetime import datetime
import signal
from autobahn import wamp
from time import sleep
import functools


def async_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        asyncio.async(func(*args, **kw))
    return wrapper


class MyComponent(ApplicationSession):
    def __init__(self, config=None):
        # maybe replace this with super()
        ApplicationSession.__init__(self, config)
        loop = asyncio.get_event_loop()
        # you should abort any long operation on SIGINT and you can do what you want SIGTERM
        # In both cases the program should exit cleanly
        loop.add_signal_handler(signal.SIGINT, self.exit_cleanup)  # SIGINT = Ctrl-C
        loop.add_signal_handler(signal.SIGTERM, self.exit_cleanup)  # the kill command use this signal by default

        print(config.extra)

    @wamp.register("com.myapp.add")
    def add(self, list_of_number):

        result = 0

        for x in list_of_number:
            try:
                x = float(x)
            except ValueError:
                x = 0
            result += x
        print('The addition of {0} = {1}'.format(list_of_number, result))
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

    @asyncio.coroutine
    def time_teller(self):
        while True:
            time_today = str(datetime.now().replace(microsecond=0))
            self.publish('com.myapp.the_time', time_today)
            yield from asyncio.sleep(2)

    @async_call  # the signal handler can't call a coroutine directly
    @asyncio.coroutine
    def exit_cleanup(self):
        print("closing_time")

        # do some cleaning, wait for subprocess/coroutines to complete..,
        yield from asyncio.sleep(10)

        loop = asyncio.get_event_loop()
        for task in asyncio.Task.all_tasks():
            # this is to avoid the cancellation of this coroutine because this coroutine need to be the last one running
            # to cancel all the others.
            if task is not asyncio.Task.current_task():
                task.cancel()

        print("everything has been cancelled")
        loop.stop()


if __name__ == "__main__":
    runner = ApplicationRunner(url="ws://127.0.0.1:8080/ws", realm="realm1",
                               extra={'key': 'value that will be passed to MyComponent'})
    runner.run(MyComponent)

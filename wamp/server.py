from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from asyncio import coroutine
import asyncio


class MyComponent(ApplicationSession):

    @coroutine
    def onJoin(self, details):
        print("session ready")

        def add2(x, y):
            print("yay !")
            return x + y

        try:
            yield from self.register(add2, 'com.myapp.add2')
            print("procedure registered")
        except Exception as e:
            print("could not register procedure: {0}".format(e))

runner = ApplicationRunner(url="ws://127.0.0.1:8080/ws", realm="realm1")
try:
    runner.run(MyComponent)
    runner.loop.run_forever()
except KeyboardInterrupt:
    asyncio.get_event_loop().stop()

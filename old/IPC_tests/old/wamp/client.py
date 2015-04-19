from autobahn.asyncio.wamp import ApplicationRunner
from autobahn.asyncio.wamp import ApplicationSession
from asyncio import coroutine
import asyncio



class MyComponent(ApplicationSession):

   @coroutine
   def onJoin(self, details):
      print("session ready")

      try:
         res = yield from self.call(u'com.myapp.add2', 6, 3)
         print("call result: {}".format(res))
      except Exception as e:
         print("call error: {0}".format(e))

runner = ApplicationRunner(url = "ws://127.0.0.1:8080/ws", realm = "realm1")
try:
    runner.run(MyComponent)
    runner.loop.run_forever()
except KeyboardInterrupt:
    asyncio.get_event_loop().stop()

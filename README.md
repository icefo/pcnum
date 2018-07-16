# features:
* digitize vhs, encode dvds and import files at the same time and save all relevant metadata in a database
* search to
  * edit and delete records
  * play a video
* progress tab: display the progress of vhs / dvd / file import

# Under the hood
* The backend has a wamp driven event loop and this event loop spawn subprocess with their own loop to deal with the captures.
* The frontend use a combination of PyQT5 and a wamp driven event loop. This was made possible by [quamash](https://github.com/harvimt/quamash) lib.


![pic1](https://cloud.githubusercontent.com/assets/7746352/13540034/76d0ccf0-e254-11e5-8edb-3ac4ec5ae046.png)
![pic2](https://cloud.githubusercontent.com/assets/7746352/10670788/904c6c9c-78e7-11e5-91d3-06ddd0967c66.png)
![pic3](https://cloud.githubusercontent.com/assets/7746352/10670789/90545fa6-78e7-11e5-8efb-2d21cf5486f3.png)
![pic4](https://cloud.githubusercontent.com/assets/7746352/10670791/90591ca8-78e7-11e5-9ecf-e96994b88919.png)
![capture-logiciel numerisation-5](https://cloud.githubusercontent.com/assets/7746352/11020151/83346ed8-8616-11e5-9c85-74e9400a70e2.png)
![capture-4](https://cloud.githubusercontent.com/assets/7746352/11020152/9064ab54-8616-11e5-8928-351d9c93417d.png)


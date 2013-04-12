web-tsp
=======

It's my Traveler Salesman Problem solution - an Artificial Intelligence lab for my university's AI class.
I've used existing draft of a TSP lib, made a web UI for it and tuned some options.

Download
========
```
$ git clone git://github.com/webknjaz/web-tsp.git
```

How to run it
=============

You need python3 interpreter, blueberrypy package (for python3) from a repo on my bitbucket acc and
routes package (for python3) from this acc.
Navigate to dir with project and run app with:
```
$ cd web-tsp
$ blueberrypy serve -b 0.0.0.0:8080
```
This will force app to listen to port 8080, so just navigate to ```http://localhost:8080/index.html``` (replace
```localhost``` with your IP or whatever if you need to)

Have fun!

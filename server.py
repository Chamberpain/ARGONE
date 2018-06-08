#!env/bin/python

import web
import json
from tracer import run_tracer, is_landpoint, get_closest_index, is_lacking_data
# from cache import get_cached_results, NotCached, cache_results, NotWritten
from logging import getLogger, INFO, Formatter
from logging.handlers import TimedRotatingFileHandler

urls = ('/', 'Index',
        '/map', 'Map',
        '/run', 'RunTracer',
        '/backward', 'Backward',
        '/runBwd', 'RunTracerBwd',
        '/bwdfwd','BwdFwd')

render = web.template.render('templates', base='map_layout')

# set up logging. for more information, see
# http://docs.python.org/2/howto/logging.html#logging-basic-tutorial

logger = getLogger(__name__)
logger.propagate = False

handler = TimedRotatingFileHandler("log/adrift.log", when="D", interval=1)
formatter = Formatter("%(asctime)s,%(message)s", datefmt='%m/%d/%Y %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.setLevel(INFO)


# other pages

class Index:
    def GET(self):
        logger.info(str(web.ctx.ip) + " root")
        return render.map()

class Map:
    def GET(self):
        i = web.input()
        try:
            try:
                center = i.center
            except AttributeError:
                center = 30
            return render.map(lat=i.lat, lng=i.lng, center=center)
        except AttributeError:
            return render.map()

class RunTracer:
    def GET(self):
        print 'I am in the run tracer class'
        i = web.input()
        try:
            given_lat = float(i.lat)
            given_lng = float(i.lng)
        except AttributeError:
            # if no attributes are given, return nothing.
            return ""

        logger.info(str(web.ctx.ip) + " map," + str(given_lat) + "," + str(given_lng))

        closest_index = get_closest_index(given_lat, given_lng,'Global')

        ret = ""

        if is_lacking_data(closest_index,'Global'):
            ret = json.dumps("Sorry, we have no data for that ocean area")
        elif is_landpoint(closest_index,'Global'):
            ret = json.dumps("You clicked on land, please click on the ocean")
        else:
            # linkfile = "https://swift.rc.nectar.org.au/v1/AUTH_24efaa1ca77941c18519133744a83574/globalCsvMonthly/Global_index"+str(closest_index).zfill(5)+"_startsin"+i.startmon+".csv";
            # ret = json.dumps(linkfile)
            results = run_tracer(closest_index,'Global')
            ret = json.dumps(results)
        web.header("Content-Type", "application/x-javascript")
        print ret
        return ret

class BwdFwd:
    def GET(self):
        logger.info(str(web.ctx.ip) + " bwdfwd")
        return render.map(open_page="bwdfwd")


class Backward:
    def GET(self):
        i = web.input()
        try:
            return render.backward(lat=i.lat, lng=i.lng)
        except AttributeError:
            return render.backward()
class RunTracerBwd:
    def GET(self):
        i = web.input()
        try:
            given_lat = float(i.lat)
            given_lng = float(i.lng)
        except AttributeError:
            # if no attributes are given, return nothing.
            return ""
        logger.info(str(web.ctx.ip) + " backward," + str(given_lat) + "," + str(given_lng))
        closest_index = get_closest_index(given_lat, given_lng,'GlobalBwd')
        ret = ""
        if is_lacking_data(closest_index,'GlobalBwd'):
            ret = json.dumps("Sorry, we have no data for that ocean area")
        elif is_landpoint(closest_index,'GlobalBwd'):
            ret = json.dumps("You clicked on land, please click on the ocean")
        else:
            results = run_tracer(closest_index,'GlobalBwd')
            ret = json.dumps(results)
        web.header("Content-Type", "application/x-javascript")
        return ret

def notfound():
    return web.notfound(render.map())


if __name__ == "__main__":
    from sys import argv
    if not (len(argv) >= 2 and argv[1].startswith("dev")):
        web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
    else:
        argv.pop(1)
    app = web.application(urls,globals())
    app.notfound = notfound
    app.run()
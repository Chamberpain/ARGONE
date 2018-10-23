import web
import json
# from tracer import run_tracer, is_landpoint, get_closest_index, is_lacking_data
# from cache import get_cached_results, NotCached, cache_results, NotWritten
# from logging import getLogger, INFO, Formatter
# from logging.handlers import TimedRotatingFileHandler
import scipy.io
from scipy import *
import time

data={}
try:
    data['Global'] = scipy.io.loadmat('/var/www/webpy-app/data/tracerappdataGlobal.mat')
#     data['GlobalBwd'] = scipy.io.loadmat('/var/www/webpy-app/data/tracerappdataGlobal_rev.mat')

except IOError as e:
#     print("({})".format(e))
#     # print
#     # print "Error: You need to get the tracerappdata*.mat files first. It then goes in ./data/"
#     # print "       Contact Erik van Sebille (mailto: e.vansebille@unsw.edu.au) for this."
#     # print
    exit()

lon = {}
lat = {}
lon['Global']=data['Global']['lon'][0]
lat['Global']=data['Global']['lat'][0]
# lon['GlobalBwd']=data['GlobalBwd']['lon'][0]
# lat['GlobalBwd']=data['GlobalBwd']['lat'][0]


def is_landpoint(closest_index,type):
    return data[type]['landpoints'][0][closest_index] == +1

def is_lacking_data(closest_index,type):
    return data[type]['landpoints'][0][closest_index] == -1

def get_closest_index(given_lat, given_lng,type):
    def findindex(array, value):
        diffs=abs(array-value) % 360
        return diffs.argmin()
    return findindex(lat[type], given_lat) * len(lon[type]) + findindex(lon[type], given_lng)

# this function is not to be used anymore!!
def run_tracer(closest_index,type):
    # print 'I am running tracer'
    if type=='Global':
        maxyears=5
        minplotval=2.5e-4
    if type=='GlobalBwd':
        maxyears=5
        minplotval=2.5e-4

    v = zeros((1, data[type]['P'][0][0].shape[0]))

    v[0][closest_index] = 1

    results = []

    def extract_important_points(v):
        heatMapData = []
        index = 0
        for i in lat[type]:
            for j in lon[type]:
                if v[0][index] > minplotval:
                    vval = int(min(v[0][index]*10000, 100))
                    heatMapData.append({'location': {'lat':int(i*10)/10.,'lng':int(j*10)/10.}, 'weight': vval})
                index += 1
        return heatMapData

    for y in range(maxyears):
          
          for bm in data[type]['P'][0]:
              v = v * bm
              results.append(extract_important_points(v))
    # print 'I have finished and am returning results'
    return results

urls = ('/', 'Index',
       '/map', 'Map',
       '/run', 'RunTracer',
       '/backward', 'Backward',
       '/runBwd', 'RunTracerBwd',
       '/bwdfwd','BwdFwd'
)
template_path = '/var/www/webpy-app/templates/'
render = web.template.render(template_path, base='map')

# set up logging. for more information, see
# http://docs.python.org/2/howto/logging.html#logging-basic-tutorial

#logger = getLogger(__name__)
#logger.propagate = False

# handler = TimedRotatingFileHandler("log/adrift.log", when="D", interval=1)
# formatter = Formatter("%(asctime)s,%(message)s", datefmt='%m/%d/%Y %H:%M:%S')
# handler.setFormatter(formatter)
# logger.addHandler(handler)

# logger.setLevel(INFO)


# other pages

class Index:
    def GET(self):
        # logger.info(str(web.ctx.ip) + " root")
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
        # print 'I am in the run tracer class'
        i = web.input()
        try:
            given_lat = float(i.lat)
            given_lng = float(i.lng)
        except AttributeError:
            # if no attributes are given, return nothing.
            return ""

        # logger.info(str(web.ctx.ip) + " map," + str(given_lat) + "," + str(given_lng))

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
        # print ret
        return ret

class BwdFwd:
    def GET(self):
        # logger.info(str(web.ctx.ip) + " bwdfwd")
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
        # logger.info(str(web.ctx.ip) + " backward," + str(given_lat) + "," + str(given_lng))
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

app = web.application(urls, globals())
application = app.wsgifunc()
web.config.debug=True
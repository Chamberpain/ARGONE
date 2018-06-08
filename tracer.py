#!env/bin/python

import scipy.io
from scipy import *
import time

data={}
try:
      data['Global'] = scipy.io.loadmat('data/tracerappdataGlobal.mat')
      data['GlobalBwd'] = scipy.io.loadmat('data/tracerappdataGlobal_rev.mat')

except IOError as e:
      print("({})".format(e))
      print
      print "Error: You need to get the tracerappdata*.mat files first. It then goes in ./data/"
      print "       Contact Erik van Sebille (mailto: e.vansebille@unsw.edu.au) for this."
      print
      exit()

lon = {}
lat = {}
lon['Global']=data['Global']['lon'][0]
lat['Global']=data['Global']['lat'][0]
lon['GlobalBwd']=data['GlobalBwd']['lon'][0]
lat['GlobalBwd']=data['GlobalBwd']['lat'][0]


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
    print 'I am running tracer'
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

    for y in xrange(maxyears):
          
          for bm in data[type]['P'][0]:
              v = v * bm
              results.append(extract_important_points(v))
    print 'I have finished and am returning results'
    return results

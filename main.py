from TransitionMatrix.Utilities.ArgoData import Core
from TransitionMatrix.Utilities.TransGeo import TransitionGeo
import argparse
from TransitionMatrix.__init__ import ROOT_DIR
import argparse
import folium
import folium.plugins
import pandas as pd
import os
import geopy
import numpy as np
from TransitionMatrix.Utilities.TransMat import TransMat
from folium.plugins import HeatMap
class ExcelGeo(TransitionGeo):
	def make_filename(self):
		return os.path.join(ROOT_DIR,'argo-90-2-2')

class ExcelFloat(Core):
	@classmethod
	def from_excel(cls,filename):
		from GeneralUtilities.Compute.list import LonList,LatList
		from TransitionMatrix.Utilities.TransMat import TransMat
		trans_mat = TransMat.load_from_type(GeoClass=ExcelGeo,lat_spacing = 2,lon_spacing = 2,time_step = 90)
		file_path = os.path.join(ROOT_DIR,'FloatData/'+filename+'.csv')
		df = pd.read_csv(file_path,usecols=['Latitude','Longitude'])
		float_lats = LatList(df.Latitude.tolist())
		lat_bins = trans_mat.trans_geo.get_lat_bins()
		adjusted_lats = LatList(lat_bins.find_nearest(x) for x in float_lats)
		float_lons = LonList(df.Longitude.tolist())
		lon_bins = trans_mat.trans_geo.get_lon_bins()
		adjusted_lons = LonList(lon_bins.find_nearest(x) for x in float_lons)
		float_idxs = [trans_mat.trans_geo.total_list.index(geopy.Point(y,x)) for y,x in zip(adjusted_lats,adjusted_lons)]
		holder_array = np.zeros([len(trans_mat.trans_geo.total_list),1])
		for idx in float_idxs:
			holder_array[idx]+=1
		return (cls(holder_array,trans_geo=trans_mat.trans_geo),float_lats,float_lons)






parser = argparse.ArgumentParser()
parser.add_argument("filename", help="filename of csv file with argo locations",
                    type=str)
parser.add_argument("timestep", help="timestep of prediction",
                    type=float)
args = parser.parse_args()
assert args.timestep>45, "timestep must be greater than 45 days"
timestep = round(args.timestep/90)
if args.timestep-timestep*90>45:
	timestep += 1
float_array,float_lats,float_lons = ExcelFloat.from_excel(args.filename)
trans_mat = TransMat.load_from_type(GeoClass=ExcelGeo,lat_spacing = 2,lon_spacing = 2,time_step = 90)
trans_calc = trans_mat.multiply(timestep-1)

output = trans_calc.todense().dot(float_array.todense())
output = [x[0] for x in output.tolist()]
lats,lons = zip(*trans_mat.trans_geo.total_list.tuple_total_list())
df = pd.DataFrame({'Latitude':lats,'Longitude':lons,'Probability':output})
df = df[df.Probability!=0]

url = 'https://server.arcgisonline.com/arcgis/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}'
map=folium.Map(location=[0,0],zoom_start=2)
folium.TileLayer(tiles=url, attr='World_Ocean_Base').add_to(map)
for x,y in zip(float_lons,float_lats):
	folium.Marker([y,x],
	              popup='Float Located at %s , %s'%(y,x),
	              icon=folium.Icon(color='green')
	             ).add_to(map)	
HeatMap(df, 
        min_opacity=0.4,
        blur = 18
               ).add_to(folium.FeatureGroup(name='Heat Map').add_to(map))
folium.LayerControl().add_to(map)

map.save(outfile=os.path.join(ROOT_DIR,'FloatData/map.html'))
os.system('open '+os.path.join(ROOT_DIR,'FloatData/map.html'))
from list import GeoList
import numpy as np
import geopy
import matplotlib.colors

class GeoBase(object):
	""" geo information and tools for transition matrices """
	def __init__(self,lat_sep=2,lon_sep=2):
		# assert isinstance(lat_sep,int)
		# assert isinstance(lon_sep,int)

		self.lat_sep = lat_sep
		self.lon_sep = lon_sep

	def set_total_list(self,total_list):
		lats,lons = zip(*[tuple(x) for x in total_list])
		lons = [x if x<180 else x-360 for x in lons]
		total_list = GeoList([geopy.Point(x) for x in zip(lats,lons)],lat_sep=self.lat_sep, lon_sep=self.lon_sep)
		lats,lons = total_list.lats_lons()
		assert isinstance(total_list,GeoList) 
		#total list must be a geolist
		assert (set(lats).issubset(set(self.get_lat_bins())))&(set(lons).issubset(set(self.get_lon_bins())))
		# total list must be a subset of the coordinate lists
		total_list = GeoList(total_list,lat_sep=self.lat_sep,lon_sep=self.lon_sep)
		self.total_list = total_list #make sure they are unique

	def get_lat_bins(self):
		lat_grid,lon_grid = GeoList([],lat_sep=self.lat_sep,lon_sep=self.lon_sep).return_dimensions()
		return lat_grid

	def get_lon_bins(self):
		lat_grid,lon_grid = GeoList([],lat_sep=self.lat_sep,lon_sep=self.lon_sep).return_dimensions()
		return lon_grid

	def get_coords(self):
		XX,YY = np.meshgrid(self.get_lon_bins(),self.get_lat_bins())
		return (XX,YY)

	def transition_vector_to_plottable(self,vector):
		lon_grid = self.get_lon_bins()
		lat_grid = self.get_lat_bins()
		plottable = np.zeros([len(lon_grid),len(lat_grid)])
		plottable = np.ma.masked_equal(plottable,0)
		for n,pos in enumerate(self.total_list):
			ii_index = lon_grid.index(pos.longitude)
			qq_index = lat_grid.index(pos.latitude)
			plottable[ii_index,qq_index] = vector[n]
		return plottable.T

class TransitionGeo(GeoBase):
	file_type = 'argo'
	number_vmin=0
	number_vmax=250
	std_vmax=50	
	def __init__(self,*args,time_step=90,**kwargs):
		super().__init__(*args,**kwargs)
		assert isinstance(time_step,int)
		self.time_step = time_step

	@classmethod
	def new_from_old(cls,trans_geo):
		new_trans_geo = cls(lat_sep=trans_geo.lat_sep,lon_sep=trans_geo.lon_sep,time_step=trans_geo.time_step)
		new_trans_geo.set_total_list(trans_geo.total_list)
		assert isinstance(new_trans_geo.total_list,GeoList) 
		return new_trans_geo
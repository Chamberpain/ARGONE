from __future__ import print_function
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
import os, sys
import datetime
from scipy.sparse.base import isspmatrix
import scipy.sparse
import matplotlib.pyplot as plt
import geopy
import copy
import csv

class Float(scipy.sparse.csc_matrix):
	traj_file_type = 'float'
	marker_color = 'm'
	marker_size = 15

	def __init__(self,*args,trans_geo=None,**kwargs):
		self.trans_geo = trans_geo
		super().__init__(*args,**kwargs)


	def __setitem__(self, index, x):
		# Process arrays from IndexMixin
		i, j = self._unpack_index(index)
		i, j = self._index_to_arrays(i, j)

		if isspmatrix(x):
			broadcast_row = x.shape[0] == 1 and i.shape[0] != 1
			broadcast_col = x.shape[1] == 1 and i.shape[1] != 1
			if not ((broadcast_row or x.shape[0] == i.shape[0]) and
					(broadcast_col or x.shape[1] == i.shape[1])):
				raise ValueError("shape mismatch in assignment")

			# clear entries that will be overwritten
			ci, cj = self._swap((i.ravel(), j.ravel()))
			self._zero_many(ci, cj)

			x = x.tocoo(copy=True)
			x.sum_duplicates()
			r, c = x.row, x.col
			x = np.asarray(x.data, dtype=self.dtype)
			if broadcast_row:
				r = np.repeat(np.arange(i.shape[0]), len(r))
				c = np.tile(c, i.shape[0])
				x = np.tile(x, i.shape[0])
			if broadcast_col:
				r = np.repeat(r, i.shape[1])
				c = np.tile(np.arange(i.shape[1]), len(c))
				x = np.repeat(x, i.shape[1])
			# only assign entries in the new sparsity structure
			i = i[r, c]
			j = j[r, c]
		else:
			# Make x and i into the same shape
			x = np.asarray(x, dtype=self.dtype)
			x, _ = np.broadcast_arrays(x, i)

			if x.shape != i.shape:
				raise ValueError("shape mismatch in assignment")

		if np.size(x) == 0:
			return
		i, j = self._swap((i.ravel(), j.ravel()))
		self._set_many(i, j, x.ravel())
		lat,lon = self.total_list[index]
		for _ in range(x):
			self.df = pd.concat([self.df,pd.DataFrame({'latitude':[lat],'longitude':[lon]})])

	@classmethod
	def recent_pos_list(cls,FloatClass,days_delta=0):
		pos_list = FloatClass.get_recent_pos()
		recent_date_list = FloatClass.get_recent_date_list()
		deployment_date_list = FloatClass.get_deployment_date_list()
		date_mask =[max(recent_date_list)-datetime.timedelta(days=270)<x for x in recent_date_list]
		age_list = [(max(recent_date_list)-x).days for x in deployment_date_list]
		age_mask = [(x+days_delta)<(365*5) for x in age_list]
		mask = np.array(date_mask)&np.array(age_mask)
		return np.array(pos_list)[mask].tolist()

	@classmethod
	def recent_floats(cls,GeoClass, FloatClass, days_delta = 0):
		out_list = []
		lat_bins = GeoClass.get_lat_bins()
		lon_bins = GeoClass.get_lon_bins()
		deployment_date_list = FloatClass.get_deployment_date_list()
		recent_date_list = FloatClass.get_recent_date_list()
		bin_list = FloatClass.get_recent_bins(lat_bins,lon_bins)
		date_mask =[max(recent_date_list)-datetime.timedelta(days=270)<x for x in recent_date_list]
		age_list = [(max(recent_date_list)-x).days for x in deployment_date_list]
		type_mask = [x==cls.traj_file_type for x in FloatClass.get_suite_list()]
		for variable in GeoClass.variable_list:
			float_var = GeoClass.variable_translation_dict[variable]
			sensor_list = FloatClass.get_sensors()
			sensor_mask = [float_var in x for x in sensor_list]
			age_mask = [(x+days_delta)<(365*5) for x in age_list]
			mask = np.array(sensor_mask)&np.array(date_mask)&np.array(age_mask)
			var_grid = np.array(bin_list)[mask]

			idx_list = [GeoClass.total_list.index(x) for x in var_grid if x in GeoClass.total_list]
			holder_array = np.zeros([len(GeoClass.total_list),1])
			for idx in idx_list:
				holder_array[idx]+=1
			out_list.append(holder_array)
		out = np.vstack(out_list)
		return cls(out,trans_geo=GeoClass)

	def get_sensor(self,row_var):
		row_idx = self.trans_geo.variable_list.index(row_var)
		split_array = np.split(self.todense(),len(self.trans_geo.variable_list))[row_idx]
		trans_geo = copy.deepcopy(self.trans_geo)
		trans_geo.variable_list = [row_var]
		return BGC(split_array,split_array.shape,trans_geo=trans_geo)

class Core(Float):
	traj_file_type = 'Core'
	marker_color = 'r'
	marker_size = 5


class BGC(Float):
	traj_file_type = 'BGC'	
	marker_color = 'm'
	marker_size = 20



import sys,os
sys.path.append(os.path.abspath("./../transition_matrix/"))
from scipy.io import loadmat,savemat
from transition_matrix_compute import argo_traj_data
degree_stepsize = 1
time_stepsize = 60
traj_class = argo_traj_data(degree_bins=degree_stepsize,date_span_limit=time_stepsize)
dat = loadmat('./data/tracerappdataGlobal.mat')
right_shape = dat['P'][0][0].shape
web_lat_list = dat['lat'][0]
web_lon_list = dat['lon'][0]
import scipy


def find_index(pos_list):
	lat,lon = pos_list
	pos_list = []
	def index_calc(lat_,lon_):
		lat_index = lat_+74
		if lon_<0:
			lon_index = lon_+360
		else:
			lon_index = lon_
		return_value = int(lat_index * len(web_lon_list) + lon_index)
		if return_value<0:
			print lat
			print lon 
			raise
		return return_value
	pos_list.append(index_calc(lat,lon))
	pos_list.append(index_calc(lat,lon+1))
	pos_list.append(index_calc(lat+1,lon))
	pos_list.append(index_calc(lat+1,lon+1))
	return pos_list

def get_right_matrix(mat):
	data_list = []
	row_list = []
	col_list = []
	for n in range(len(mat.indptr)-1):
		row_loc = traj_class.total_list[n]
		lat_check,lon_check=row_loc
		if lon_check == -180:
			continue
		if lat_check < -74:
			continue
		row_index = find_index(row_loc)
		for k,data in zip(mat.indices[mat.indptr[n]:mat.indptr[n+1]],mat.data[mat.indptr[n]:mat.indptr[n+1]]):
			col_loc = traj_class.total_list[k]
			lat_check,lon_check=col_loc
			if lon_check == -180:
				continue
			if lat_check < -74:
				continue
			col_index = find_index(col_loc)
			data_list += [data]*4
			row_list += row_index
			col_list += col_index
	return scipy.sparse.csc_matrix((data_list,(row_list,col_list)),shape=right_shape)
for n in range(6):
	traj_class.load_w(n)

	dat['P'][0][n] = get_right_matrix(traj_class.w)
savemat('./data/tracerappdataGlobal.mat',dat)
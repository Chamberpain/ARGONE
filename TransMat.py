from __init__ import ROOT_DIR
import sys
sys.path.append(ROOT_DIR)
from list import flat_list,LonList,LatList,GeoList
from TransGeo import TransitionGeo
import numpy as np
import scipy.sparse
import json
import scipy.sparse.linalg
import os 
from scipy.sparse import _sparsetools
from scipy.sparse.sputils import (get_index_dtype,upcast)
import pickle
import geopy

class BaseMat(scipy.sparse.csc_matrix):
	"""Base class for transition and correlation matrices"""
	def __init__(self, *args,trans_geo=None,**kwargs):
		super().__init__(*args,**kwargs)
		if trans_geo:
			self.set_trans_geo(trans_geo)

	def set_trans_geo(self,trans_geo):
		self.trans_geo = trans_geo

	@classmethod
	def load(cls,filename,GeoClass=TransitionGeo):
		row_idx,column_idx,data,tuple_list = np.load(filename,allow_pickle=True)
		shape_num = len(tuple_list)
		trans_geo = GeoClass()
		trans_geo.set_total_list(tuple_list)
		out_data = cls((data.tolist(),(row_idx.tolist(),column_idx.tolist())),shape=(shape_num,shape_num),trans_geo = trans_geo)
		return out_data

	def new_sparse_matrix(self,data):
		row_idx,column_idx,dummy = scipy.sparse.find(self)
		return BaseMat((data,(row_idx,column_idx)),shape=(len(self.trans_geo.total_list),len(self.trans_geo.total_list)))             

	def mean(self,axis=0):
		return np.array(self.sum(axis=axis)/(self!=0).sum(axis=axis)).flatten()

	def _binopt(self, other, op):
		""" This is included so that when sparse matrices are added together, their instance variables are maintained this code was grabbed from the scipy source with the small addition at the end"""

		other = self.__class__(other)

		# e.g. csr_plus_csr, csr_minus_csr, etc.
		fn = getattr(_sparsetools, self.format + op + self.format)

		maxnnz = self.nnz + other.nnz
		idx_dtype = get_index_dtype((self.indptr, self.indices,
									 other.indptr, other.indices),
									maxval=maxnnz)
		indptr = np.empty(self.indptr.shape, dtype=idx_dtype)
		indices = np.empty(maxnnz, dtype=idx_dtype)

		bool_ops = ['_ne_', '_lt_', '_gt_', '_le_', '_ge_']
		if op in bool_ops:
			data = np.empty(maxnnz, dtype=np.bool_)
		else:
			data = np.empty(maxnnz, dtype=upcast(self.dtype, other.dtype))

		fn(self.shape[0], self.shape[1],
		   np.asarray(self.indptr, dtype=idx_dtype),
		   np.asarray(self.indices, dtype=idx_dtype),
		   self.data,
		   np.asarray(other.indptr, dtype=idx_dtype),
		   np.asarray(other.indices, dtype=idx_dtype),
		   other.data,
		   indptr, indices, data)
		if issubclass(type(self),TransMat):
			try:
				A = self.__class__((data, indices, indptr), shape=self.shape,trans_geo=self.trans_geo
					,number_data=self.number_data)
			except AttributeError:
				A = self.__class__((data, indices, indptr), shape=self.shape,trans_geo=self.trans_geo)
		else:
			try:
				A = self.__class__((data, indices, indptr), shape=self.shape,trans_geo=self.trans_geo
					,number_data=self.number_data)
			except AttributeError:
				A = self.__class__((data, indices, indptr), shape=self.shape,trans_geo=self.trans_geo)				
		A.prune()

		return A


	def _mul_sparse_matrix(self, other):
		""" This is included so that when sparse matrices are multiplies together, 
		their instance variables are maintained this code was grabbed from the scipy 
		source with the small addition at the end"""
		M, K1 = self.shape
		K2, N = other.shape

		major_axis = self._swap((M, N))[0]
		other = self.__class__(other)  # convert to this format

		idx_dtype = get_index_dtype((self.indptr, self.indices,
									 other.indptr, other.indices))

		fn = getattr(_sparsetools, self.format + '_matmat_maxnnz')
		nnz = fn(M, N,
				 np.asarray(self.indptr, dtype=idx_dtype),
				 np.asarray(self.indices, dtype=idx_dtype),
				 np.asarray(other.indptr, dtype=idx_dtype),
				 np.asarray(other.indices, dtype=idx_dtype))

		idx_dtype = get_index_dtype((self.indptr, self.indices,
									 other.indptr, other.indices),
									maxval=nnz)

		indptr = np.empty(major_axis + 1, dtype=idx_dtype)
		indices = np.empty(nnz, dtype=idx_dtype)
		data = np.empty(nnz, dtype=upcast(self.dtype, other.dtype))

		fn = getattr(_sparsetools, self.format + '_matmat')
		fn(M, N, np.asarray(self.indptr, dtype=idx_dtype),
		   np.asarray(self.indices, dtype=idx_dtype),
		   self.data,
		   np.asarray(other.indptr, dtype=idx_dtype),
		   np.asarray(other.indices, dtype=idx_dtype),
		   other.data,
		   indptr, indices, data)

		if issubclass(type(self),TransMat):
			try:
				return self.__class__((data, indices, indptr), shape=self.shape,trans_geo=self.trans_geo
					,number_data=self.number_data)
			except AttributeError:
				return self.__class__((data, indices, indptr), shape=self.shape,trans_geo=self.trans_geo)
		else:
			try:
				return self.__class__((data, indices, indptr), shape=self.shape,trans_geo=self.trans_geo
					,number_data=self.number_data)
			except AttributeError:
				return self.__class__((data, indices, indptr), shape=self.shape,trans_geo=self.trans_geo)


class TransMat(BaseMat):
	def __init__(self, *args,rescale=False,**kwargs):
		super().__init__(*args,**kwargs)
		if rescale:
			self.rescale()

	def remove_small_values(self,value):
		row_idx,column_idx,data = scipy.sparse.find(self)
		mask = data>value
		row_idx = row_idx[mask]
		column_idx = column_idx[mask]
		data = data[mask]
		return self.__class__((data,(row_idx,column_idx)),shape=self.shape,trans_geo=self.trans_geo
				,rescale=True)	

	def multiply(self,mult,value=0.02):
		mat1 = self.remove_small_values(self.data.mean()/25)
		mat2 = self.remove_small_values(self.data.mean()/25)
		for k in range(mult):
			print('I am at ',k,' step in the multiplication')
			mat_holder = mat1.dot(mat2)
			mat1 = mat_holder.remove_small_values(mat_holder.data.mean()/25)
		return mat1

	def rescale(self,checksum=10**-2):
		div_array = np.abs(self.sum(axis=0)).tolist()[0]
		row_idx,column_idx,data = scipy.sparse.find(self)
		col_count = []
		for col in column_idx:
			col_count.append(float(div_array[col]))
		self.data = np.array(data)/np.array(col_count)
		zero_idx = np.where(np.abs(self.sum(axis=0))==0)[1]
		self[zero_idx,zero_idx]=1
		self.matrix_column_check(checksum=checksum)

	def matrix_column_check(self,checksum):
		assert (np.abs(self.sum(axis=0)-1)<checksum).all()

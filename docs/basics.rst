.. _usage:

The Basics
==========

|dlfn| data objects are built on xarray `DataArrays
<http://xarray.pydata.org/en/stable/user-guide/data-structures.html>`_
combined into a single `Dataset <http://xarray.pydata.org/en/stable/generated/xarray.Dataset.html#xarray.Dataset>`_ with `attributes`, or info about the data. 
Xarray can be thought of as a multidimensional extension of pandas, though it is not built on top of pandas. Datasets and DataArrays support all of the same basic functionality of dictionaries (e.g., indexing, iterating, etc.), with additional functionality that is designed to streamline the process of analyzing and working with data.
 

Reading Source Datafiles
------------------------

To begin, we load the |dlfn| module and read a data file::

  >> import dolfyn as dlfn
  >> dat = dlfn.read(<path/to/my_data_file>)

|dlfn|'s read function supports reading Nortek and TRDI binary data files straight 
from the ADCP or from the manufacturer's processing software (e.g. TRDI's WinADCP, 
VMDAS, or WinRiver).

In an interactive shell, typing the variable name followed by enter/return will display information about the dataset, e.g.::

    >> dat = dlfn.read_example('AWAC_test01.wpr')
    >> dat
	<xarray.Dataset>
	Dimensions:              (earth: 3, inst: 3, dir: 3, range: 20, time: 9997, x: 3, x*: 3)
	Coordinates:
	  * dir                  (dir) <U1 'E' 'N' 'U'
	  * range                (range) float32 1.41 2.41 3.4 4.4 ... 18.36 19.35 20.35
	  * time                 (time) float64 1.34e+09 1.34e+09 ... 1.34e+09 1.34e+09
	  * x                    (x) int32 1 2 3
	  * x*                   (x*) int32 1 2 3
	  * inst                 (inst) <U1 'X' 'Y' 'Z'
	  * earth                (earth) <U1 'E' 'N' 'U'
	Data variables:
		beam2inst_orientmat  (x, x*) float64 1.577 -0.7891 -0.7891 ... 0.3677 0.3677
		c_sound              (time) float32 1.489e+03 1.489e+03 ... 1.512e+03
		heading              (time) float32 119.3 119.4 119.7 ... 128.7 128.9 129.0
		pitch                (time) float32 6.55e+03 6.55e+03 ... 6.552e+03
		roll                 (time) float32 0.7 0.2 0.3 0.5 ... 0.5 0.5 0.5 0.5
		pressure             (time) float32 16.03 16.01 16.02 ... 0.042 0.032 0.038
		temp                 (time) float32 11.49 11.49 11.48 ... 18.72 18.72 18.72
		vel                  (orient, range, time) float64 -0.6648 -0.655 ... 0.645
		amp                  (orient, range, time) uint8 146 147 144 ... 25 25 25
		orientmat            (inst, earth, time) float64 0.3026 0.2995 ... 0.3123
	Attributes:
		config:                    {'ProLogID': 156, 'ProLogFWver': '4.06', 'conf...
		inst_make:                 Nortek
		inst_model:                AWAC
		inst_type:                 ADCP
		rotate_vars:               ['vel']
		freq:                      1000
		SerialNum:                 WPR 1549
		Comments:                  AWAC on APL-UW Tidal Turbulence Mooring at Adm...
		DutyCycle_NBurst:          836
		DutyCycle_NCycle:          1.0
		fs:                        1.0
		coord_sys:                 earth
		has_imu:                   0
		cell_size:                 1.0
		blank_dist:                0.41

This view reveals all the data stored within the xarray Dataset. There are four types of data displyed here: data variables, coordinates, dimensions and attributes.

 - Data variables contain the main information stored as xarray DataArrays::
 
    >> dat.vel
	<xarray.DataArray 'vel' (dir: 3, range: 20, time: 9997)>
	array([[[-0.66479734, -0.65496222, -0.69909159, ...,  1.90351055,
			  1.94648366,  1.91131579],
			[-0.53663862, -0.56178903, -0.76993938, ...,  0.67961291,
			  6.46099706, -0.3679769 ],
			[-0.63192198, -0.63142786, -0.52826604, ..., -0.0844491 ,
			  2.69917045, -0.69253631],
			...,
			[-0.90170625, -0.85587418, -0.48779671, ...,  3.71806074,
			  0.63299628,  1.34105901],
			[-0.73322984, -0.66709612, -0.46033165, ..., -1.68639582,
			  0.31451557,  2.93691549],
			[-0.90169828, -0.68338529, -0.57451738, ..., -2.77793829,
			  2.43313374, -0.98629605]],
	...
		   [[-0.11800002, -0.06400001,  0.13500002, ...,  1.483     ,
			  1.49100016,  1.50800014],
			[-0.17100002, -0.18900001,  0.029     , ...,  0.86300005,
			 -0.95699996,  0.14500003],
			[-0.08900001, -0.21400001,  0.016     , ..., -1.54799992,
			  1.6550002 , -0.82600006],
			...,
			[ 0.05099999, -0.12099999,  0.22100003, ..., -0.78300005,
			  0.7650001 ,  0.164     ],
			[-0.05500002, -0.17199998,  0.152     , ..., -0.93699997,
			  1.22200003, -0.87500013],
			[ 0.05099998, -0.146     ,  0.16600001, ..., -1.09600008,
			  0.49300008,  0.64500009]]])
	Coordinates:
	  * range    (range) float32 1.41 2.41 3.41 4.41 ... 17.41 18.41 19.41 20.41
	  * time     (time) float64 1.34e+09 1.34e+09 1.34e+09 ... 1.34e+09 1.34e+09
	  * dir      (dir) <U1 'E' 'N' 'U'
	Attributes:
		units:    m/s
   
 - Coordinates are arrays that contain the indices/labels/values of the data variables' dimensions, e.g. time, latitude, or longitude::
 
	>> dat.time
	<xarray.DataArray 'time' (time: 9997)>
	array([1.339528e+09, 1.339528e+09, 1.339528e+09, ..., 1.339538e+09,
		   1.339538e+09, 1.339538e+09])
	Coordinates:
	  * time     (time) float64 1.34e+09 1.34e+09 1.34e+09 ... 1.34e+09 1.34e+09
	Attributes:
		description:  seconds since 1/1/1970
	
 - Dimensions are simply the names of the coordinate arrays
 
 - Attributes can be thought of as comments, or information that provides insight into the data variables, and must be floats, strings or arrays. |dlfn| uses attributes to store information on coordinate rotations.

Data variables and coordinates can be accessed using dict-style syntax, *or* attribute-style syntax. For example::

    >> dat['range']
	<xarray.DataArray 'range' (range: 20)>
	array([ 1.41,  2.41,  3.4 ,  4.4 ,  5.4 ,  6.39,  7.39,  8.39,  9.39, 10.38,
		   11.38, 12.38, 13.37, 14.37, 15.37, 16.36, 17.36, 18.36, 19.35, 20.35],
		  dtype=float32)
	Coordinates:
	  * range    (range) float32 1.41 2.41 3.4 4.4 5.4 ... 17.36 18.36 19.35 20.35
	Attributes:
		units:    m

    >> dat.amp[0]
	<xarray.DataArray 'amp' (range: 20, time: 9997)>
	array([[146, 147, 144, ...,  38,  38,  38],
		   [136, 135, 136, ...,  25,  25,  25],
		   [130, 129, 132, ...,  25,  24,  25],
		   ...,
		   [ 89,  96,  88, ...,  23,  22,  23],
		   [ 77,  82,  84, ...,  23,  23,  23],
		   [ 61,  49,  58, ...,  23,  22,  23]], dtype=uint8)
	Coordinates:
	  * range    (range) float32 1.41 2.41 3.41 4.41 ... 17.41 18.41 19.41 20.41
	  * time     (time) float64 1.34e+09 1.34e+09 1.34e+09 ... 1.34e+09 1.34e+09
		beam     int32 1
	Attributes:
		units:    counts

Dataset/DataArray attributes can be accessed as follows::

  >> dat.blank_dist
  0.41
  
  >> dat.attrs['fs']
  1.0

Note here that the display information includes the size of each array, it's coordinates and attributes. Active DataArray coordinates are signified with a '*'. The units of most variables are in the *MKS* system (e.g., velocity is in m/s), and angles are in degrees. Units are saved in relevant DataArrays as attributes; see the :ref:`units` section for a complete list of the units of |dlfn| variables.


Subsetting Data
---------------

Xarray has its own built-in methods for `selecting data  <http://xarray.pydata.org/en/stable/user-guide/indexing.html>`_.

A section of data can be extracted to a new Dataset or DataArray using ``.isel``, ``.sel`` and/or with python's built-in ``slice`` function, for example::

  # Returns a new DataArray containing data from 0 to 5 m.
  >> datsub = dat.vel.sel(range=slize(0,5))
  
  # Returns velocity in 'streamwise' direction
  >> datsub = dat.vel.sel(orient='streamwise')

  # Returns a new DataArray with the first 1000 indices (timesteps) from the original DataArray
  >> datsub = dat.vel.isel(time=slice(0,1000))
  
  
Data Analysis Tools
-------------------

Analysis in |dlfn| is primarily set up to work through two API's (Advanced Programming Interfaces): the :ref:`adp` and the :ref:`adv`, each of which contain functions that pertain to ADCP and ADV instruments, respectively. Functions and classes that pertain to both can be accessed from the main package import. See the :ref:`package` for further detail.  

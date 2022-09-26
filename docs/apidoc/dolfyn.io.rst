Reading and Loading Data
========================

Contains high level routines for reading in instrument binary data, and saving and loading xarray datasets. DOLfYN will automatically search through and select a binary reader based on the input data's file extension.

.. autosummary::
	:nosignatures:
	
	~dolfyn.io.api.read
	~dolfyn.io.api.read_example
	~dolfyn.io.api.save
	~dolfyn.io.api.load
	~dolfyn.io.api.save_mat
	~dolfyn.io.api.load_mat
	
I/O functions can be accessed directly from |dlfn|'s main import::

	>> import dolfyn
	>> dat = dolfyn.read(<path/to/my_data_file>)
	>> dolfyn.save(dat, <path/to/save_file.nc>)

.. automodule:: dolfyn.io.api
    :members:
    :undoc-members:
    :show-inheritance:
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

.. automodule:: dolfyn.io.api
    :members:
    :undoc-members:
    :show-inheritance:
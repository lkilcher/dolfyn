I/O Module
=====================

Contains high level routines for reading in instrument binary data and loading a DOLfYN h5py data object. DOLfYN will automatically search through and select a binary reader based on the input data's file extension.

.. autosummary::
	:nosignatures:
	
	~dolfyn.io.api.read
	~dolfyn.io.api.read_example
	~dolfyn.io.api.load

.. automodule:: dolfyn.io.api
    :members:
    :undoc-members:
    :show-inheritance:
	
.. automodule:: dolfyn.io.hdf5
    :members:
    :undoc-members:
    :show-inheritance:
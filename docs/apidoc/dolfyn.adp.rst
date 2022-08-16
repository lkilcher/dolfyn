.. _adp:

ADCP Module
===========

This module contains routines for reading and working with ADP/ADCP data. It contains:

.. autosummary::
	:nosignatures:
	
	~dolfyn.io.api.read
	~dolfyn.io.api.load
	~dolfyn.rotate.api.rotate2
	~dolfyn.adp.clean
	~dolfyn.velocity.VelBinner
	
Quick Example
-------------
.. literalinclude:: ../examples/adcp_example.py


Cleaning Data
-------------

.. autosummary::
	:nosignatures:
	
	~dolfyn.adp.clean.set_range_offset
	~dolfyn.adp.clean.find_surface
	~dolfyn.adp.clean.find_surface_from_P
	~dolfyn.adp.clean.nan_beyond_surface
	~dolfyn.adp.clean.val_exceeds_thresh
	~dolfyn.adp.clean.correlation_filter
	~dolfyn.adp.clean.medfilt_orient
	~dolfyn.adp.clean.fillgaps_time
	~dolfyn.adp.clean.fillgaps_depth

.. automodule:: dolfyn.adp.clean
    :members:
    :undoc-members:
    :show-inheritance:
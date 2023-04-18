.. _adv:

ADV Module
==========

This module contains routines for reading and working with ADV data. It contains:

.. autosummary::
	:nosignatures:
	
	~dolfyn.io.api.read
	~dolfyn.io.api.load
	~dolfyn.rotate.api.rotate2
	~dolfyn.rotate.api.set_inst2head_rotmat
	~dolfyn.rotate.api.calc_principal_heading
	~dolfyn.adv.clean
	~dolfyn.adv.motion.correct_motion
	~dolfyn.velocity.VelBinner
	~dolfyn.adv.turbulence.ADVBinner
	~dolfyn.adv.turbulence.calc_turbulence


Quick Example
-------------
.. literalinclude:: ../examples/adv_example.py
	
	
Cleaning Data
-------------

.. autosummary::
	:nosignatures:
	
	~dolfyn.adv.clean.clean_fill
	~dolfyn.adv.clean.fill_nan_ensemble_mean
	~dolfyn.adv.clean.spike_thresh
	~dolfyn.adv.clean.range_limit
	~dolfyn.adv.clean.GN2002
	
.. automodule:: dolfyn.adv.clean
    :members:
    :undoc-members:
    :show-inheritance:
	
.. automodule:: dolfyn.adv.motion
    :members:
    :undoc-members:
    :show-inheritance:
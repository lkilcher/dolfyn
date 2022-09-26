.. _bin:

Binning Tools
=============

Velocity Analysis
"""""""""""""""""

Analysis in DOLfYN is primarily handled through the `VelBinner` class. 
Below is a list of functions that can be called from `VelBinner`.

.. autosummary::
	:nosignatures:
	
	~dolfyn.velocity.VelBinner
	~dolfyn.binned.TimeBinner.reshape
	~dolfyn.binned.TimeBinner.detrend 
	~dolfyn.binned.TimeBinner.demean
	~dolfyn.binned.TimeBinner.mean 
	~dolfyn.binned.TimeBinner.var 
	~dolfyn.binned.TimeBinner.std 
	~dolfyn.binned.VelBinner.do_avg
	~dolfyn.binned.VelBinner.do_var
	~dolfyn.binned.VelBinner.calc_coh
	~dolfyn.binned.VelBinner.calc_phase_angle
	~dolfyn.binned.VelBinner.calc_acov
	~dolfyn.binned.VelBinner.calc_xcov
	~dolfyn.velocity.VelBinner.calc_tke
	~dolfyn.velocity.VelBinner.calc_psd
	~dolfyn.binned.TimeBinner.calc_freq


Turbulence Analysis
"""""""""""""""""""

Functions for analyzing ADV data via the `ADVBinner` class, beyond those described in `VelBinner`.
Functions for analyzing turbulence statistics from ADCP data are in development.

.. autosummary::
	:nosignatures:

	~dolfyn.adv.turbulence.ADVBinner
	~dolfyn.adv.turbulence.calc_turbulence
	~dolfyn.adv.VelBinner.calc_csd
	~dolfyn.adv.VelBinner.calc_stress
	~dolfyn.adv.turbulence.ADVBinner.calc_epsilon_LT83
	~dolfyn.adv.turbulence.ADVBinner.calc_epsilon_SF
	~dolfyn.adv.turbulence.ADVBinner.calc_epsilon_TE01
	~dolfyn.adv.turbulence.ADVBinner.calc_L_int


.. automodule:: dolfyn.binned
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: dolfyn.velocity
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: dolfyn.adv.turbulence
    :members:
    :undoc-members:
    :show-inheritance:
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
	~dolfyn.binned.TimeBinner.calc_psd_base
	~dolfyn.binned.TimeBinner.calc_csd_base


Turbulence Analysis
"""""""""""""""""""

Functions for analyzing ADV data via the `ADVBinner` class, beyond those described in `VelBinner`.

.. autosummary::
	:nosignatures:

	~dolfyn.adv.turbulence.ADVBinner
	~dolfyn.adv.turbulence.calc_turbulence
	~dolfyn.adv.turbulence.ADVBinner.calc_csd
	~dolfyn.adv.turbulence.ADVBinner.calc_stress
	~dolfyn.adv.turbulence.ADVBinner.calc_doppler_noise
	~dolfyn.adv.turbulence.ADVBinner.calc_epsilon_LT83
	~dolfyn.adv.turbulence.ADVBinner.calc_epsilon_SF
	~dolfyn.adv.turbulence.ADVBinner.calc_epsilon_TE01
	~dolfyn.adv.turbulence.ADVBinner.calc_L_int

Functions for analyzing ADCP data via the `ADPBinner` class, beyond those described in `VelBinner`.

.. autosummary::
	:nosignatures:

	~dolfyn.adv.turbulence.ADPBinner
	~dolfyn.adv.turbulence.ADPBinner.dudz
	~dolfyn.adv.turbulence.ADPBinner.dvdz
	~dolfyn.adv.turbulence.ADPBinner.dwdz
	~dolfyn.adv.turbulence.ADPBinner.tau2
	~dolfyn.adv.turbulence.ADPBinner.calc_doppler_noise
	~dolfyn.adv.turbulence.ADPBinner.calc_stress_4beam
	~dolfyn.adv.turbulence.ADPBinner.calc_stress_5beam
	~dolfyn.adv.turbulence.ADPBinner.calc_total_tke
	~dolfyn.adv.turbulence.ADPBinner.calc_dissipation_LT83
	~dolfyn.adv.turbulence.ADPBinner.calc_dissipation_SF
	~dolfyn.adv.turbulence.ADPBinner.calc_ustar_fit


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
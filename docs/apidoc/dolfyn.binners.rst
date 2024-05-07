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
	~dolfyn.velocity.VelBinner.do_avg
	~dolfyn.velocity.VelBinner.do_var
	~dolfyn.velocity.VelBinner.calc_ti
	~dolfyn.velocity.VelBinner.calc_psd
	~dolfyn.velocity.VelBinner.calc_coh
	~dolfyn.velocity.VelBinner.calc_phase_angle
	~dolfyn.velocity.VelBinner.calc_acov
	~dolfyn.velocity.VelBinner.calc_xcov
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
	~dolfyn.velocity.VelBinner.calc_tke
	~dolfyn.adv.turbulence.ADVBinner.calc_stress
	~dolfyn.adv.turbulence.ADVBinner.calc_doppler_noise
	~dolfyn.adv.turbulence.ADVBinner.check_turbulence_cascade_slope
	~dolfyn.adv.turbulence.ADVBinner.calc_epsilon_LT83
	~dolfyn.adv.turbulence.ADVBinner.calc_epsilon_SF
	~dolfyn.adv.turbulence.ADVBinner.calc_epsilon_TE01
	~dolfyn.adv.turbulence.ADVBinner.calc_L_int

Functions for analyzing ADCP data via the `ADPBinner` class, beyond those described in `VelBinner`.

.. autosummary::
	:nosignatures:

	~dolfyn.adp.turbulence.ADPBinner
	~dolfyn.adp.turbulence.ADPBinner.calc_dudz
	~dolfyn.adp.turbulence.ADPBinner.calc_dvdz
	~dolfyn.adp.turbulence.ADPBinner.calc_dwdz
	~dolfyn.adp.turbulence.ADPBinner.calc_shear2
	~dolfyn.adp.turbulence.ADPBinner.calc_doppler_noise
	~dolfyn.adp.turbulence.ADPBinner.calc_stress_4beam
	~dolfyn.adp.turbulence.ADPBinner.calc_stress_5beam
	~dolfyn.adp.turbulence.ADPBinner.check_turbulence_cascade_slope
	~dolfyn.adp.turbulence.ADPBinner.calc_dissipation_LT83
	~dolfyn.adp.turbulence.ADPBinner.calc_dissipation_SF
	~dolfyn.adp.turbulence.ADPBinner.calc_ustar_fit


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

.. automodule:: dolfyn.adp.turbulence
    :members:
    :undoc-members:
    :show-inheritance:

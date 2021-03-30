ADV Module
==========

.. automodule:: dolfyn.adv.api
    :members:
    :undoc-members:
    :show-inheritance:
	
Cleaning Data
"""""""""""""

Contains functions for cleaning ADV data.

.. autosummary::
	:nosignatures:
	
	~dolfyn.adv.clean.cleanFill
	~dolfyn.adv.clean.fillpoly
	~dolfyn.adv.clean.rangeLimit
	~dolfyn.adv.clean.GN2002
	
.. automodule:: dolfyn.adv.clean
    :members:
    :undoc-members:
    :show-inheritance:


Motion Correction
"""""""""""""""""

Contains functions for correcting Nortek Vector ADV data with data from the onboard IMU.

.. autosummary::
	:nosignatures:
	
	~dolfyn.adv.motion.correct_motion
	~dolfyn.adv.motion.CorrectMotion
	
.. automodule:: dolfyn.adv.motion
    :members:
    :undoc-members:
    :show-inheritance:
	
	
VelBinner
"""""""""

Analysis in DOLfYN is primarily handled through the `VelBinner` class. Below is a list of functions that can be called from `VelBinner`.

.. autosummary::
	:nosignatures:
	
	~dolfyn.data.velocity.VelBinner
	~dolfyn.data.binned.TimeBinner.reshape
	~dolfyn.data.binned.TimeBinner.detrend
	~dolfyn.data.binned.TimeBinner.demean
	~dolfyn.data.binned.TimeBinner.mean
	~dolfyn.data.binned.TimeBinner.mean_angle
	~dolfyn.data.binned.TimeBinner.calc_acov
	~dolfyn.data.binned.TimeBinner.calc_lag
	~dolfyn.data.binned.TimeBinner.calc_xcov
	~dolfyn.data.binned.TimeBinner.do_avg
	~dolfyn.data.binned.TimeBinner.do_var
	~dolfyn.data.binned.TimeBinner.cohere
	~dolfyn.data.binned.TimeBinner.phase_angle
	~dolfyn.data.velocity.VelBinner.do_tke
	~dolfyn.data.velocity.VelBinner.calc_tke
	~dolfyn.data.velocity.VelBinner.calc_stress
	~dolfyn.data.velocity.VelBinner.do_spec
	~dolfyn.data.velocity.VelBinner.calc_vel_psd
	~dolfyn.data.binned.TimeBinner.calc_freq
	~dolfyn.data.binned.TimeBinner.calc_omega
	~dolfyn.data.velocity.VelBinner.do_cross_spec
	~dolfyn.data.velocity.VelBinner.calc_vel_cpsd


Turbulence Analysis
"""""""""""""""""""

Functions for analyzing ADV data via the `TurbBinner` class, beyond those described in `VelBinner`.

.. autosummary::
	:nosignatures:

	~dolfyn.adv.turbulence.calc_turbulence
	~dolfyn.adv.turbulence.TurbBinner
	~dolfyn.adv.turbulence.TurbBinner.calc_epsilon_LT83
	~dolfyn.adv.turbulence.TurbBinner.calc_epsilon_SF
	~dolfyn.adv.turbulence.TurbBinner.calc_epsilon_TE01
	~dolfyn.adv.turbulence.TurbBinner.up_angle
	~dolfyn.adv.turbulence.TurbBinner.calc_Lint	

.. automodule:: dolfyn.adv.turbulence
    :members:
    :undoc-members:
    :show-inheritance:
.. _bin:

Binning Tools
=============

Velocity Analysis
"""""""""""""""""

Analysis in DOLfYN is primarily handled through the `VelBinner` class. Below is a list of functions that can be called from `VelBinner`.

.. autosummary::
	:nosignatures:
	
	~dolfyn.velocity.VelBinner
	~dolfyn.binned._TimeBinner.do_avg
	~dolfyn.binned._TimeBinner.do_var
	~dolfyn.binned._TimeBinner.reshape
	~dolfyn.binned._TimeBinner.calc_coh
	~dolfyn.binned._TimeBinner.calc_phase_angle
	~dolfyn.binned._TimeBinner.calc_acov
	~dolfyn.binned._TimeBinner.calc_xcov
	~dolfyn.velocity.VelBinner.do_tke
	~dolfyn.velocity.VelBinner.calc_tke
	~dolfyn.velocity.VelBinner.calc_stress
	~dolfyn.velocity.VelBinner.calc_vel_psd
	~dolfyn.velocity.VelBinner.calc_vel_csd
	~dolfyn.binned._TimeBinner.calc_freq


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
	~dolfyn.adv.turbulence.TurbBinner.calc_L_int


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
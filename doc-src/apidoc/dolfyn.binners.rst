.. _bin:

Binning Tools
=============

VelBinner
"""""""""

Analysis in DOLfYN is primarily handled through the `VelBinner` class. Below is a list of functions that can be called from `VelBinner`.

.. autosummary::
	:nosignatures:
	
	~dolfyn.data.velocity.VelBinner
	~dolfyn.data.binned.TimeBinner.do_avg
	~dolfyn.data.binned.TimeBinner.do_var
	~dolfyn.data.binned.TimeBinner.reshape
	~dolfyn.data.binned.TimeBinner.calc_coh
	~dolfyn.data.binned.TimeBinner.calc_phase_angle
	~dolfyn.data.binned.TimeBinner.calc_acov
	~dolfyn.data.binned.TimeBinner.calc_xcov
	~dolfyn.data.velocity.VelBinner.do_tke
	~dolfyn.data.velocity.VelBinner.calc_tke
	~dolfyn.data.velocity.VelBinner.calc_stress
	~dolfyn.data.velocity.VelBinner.calc_vel_psd
	~dolfyn.data.velocity.VelBinner.calc_vel_csd
	~dolfyn.data.binned.TimeBinner.calc_freq


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


.. automodule:: dolfyn.data.binned
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: dolfyn.data.velocity
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: dolfyn.adv.turbulence
    :members:
    :undoc-members:
    :show-inheritance:
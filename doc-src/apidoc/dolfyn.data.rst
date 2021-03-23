Analysis and Data Types
==========================

VelBinner Class
"""""""""""""""

Analysis in DOLfYN is primarily handled through the `VelBinner` class. Below is a list of Functions that can be called from `VelBinner`.

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

Velocity Data Types
"""""""""""""""""""

Data is handled in DOLfYN through one of two classes, `Velocity` and `TKEdata`. These two classes are primarily provided for reference, and the properties attributed to each are listed in the *Data Structure* tab. Functions and properties listed below are called directly from DOLfYN data objects.

Classes:

.. autosummary::
	:nosignatures:

	~dolfyn.data.velocity.Velocity
	~dolfyn.data.velocity.TKEdata

Functions:

.. autosummary::
	:nosignatures:
	
	~dolfyn.data.velocity.Velocity.set_declination
	~dolfyn.data.velocity.Velocity.rotate2

.. automodule:: dolfyn.data.velocity
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: dolfyn.data.binned
    :members:
    :undoc-members:
    :show-inheritance:
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

Motion Correction
"""""""""""""""""

Contains functions for correcting Nortek Vector ADV velocity data with data from the onboard IMU.

.. autosummary::
	:nosignatures:
	
	~dolfyn.adv.motion.correct_motion
	~dolfyn.adv.motion.CorrectMotion
	
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


.. automodule:: dolfyn.adv.motion
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: dolfyn.adv.clean
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: dolfyn.adv.turbulence
    :members:
    :undoc-members:
    :show-inheritance:
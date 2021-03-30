Data Types
==========

Data is handled in DOLfYN through one of two data objects, `ADPdata` and `ADVdata`, which include the `Velocity` and `TKEdata` classes. The properties attributed to each are listed in the Terminology tab. Functions and properties listed below are called directly from the data variable.

Classes:

.. autosummary::
	:nosignatures:
	
	~dolfyn.adp.base.ADPdata
	~dolfyn.adv.base.ADVdata

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
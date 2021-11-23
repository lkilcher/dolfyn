Rotate Functions
================

Contains functions for rotating data through frames of reference (FoR):
	1. **'beam'**: Follows the acoustic beam FoR, where velocity data is organized by beam number 1-3 or 1-4.
	2. **'inst'**: The instrument's *XYZ* Cartesian directions. For ADVs, this orientation is from the mark on the ADV body/battery canister, not the sensor head. For TRDI 4-beam instruments, the fourth velocity term is the error velocity (aka *XYZE*). For Nortek 4-beam instruments, this is *XYZ1 Z2*, where *E=Z2-Z1*.
	3. **'earth'**: *East North UP* (*ENU*) FoR. Based on either magnetic or true North, depending on whether or not DOLfYN has a magnetic declination associated with the dataset. Instruments do not internally record magnetic declination, unless it has been supplied via external software like TRDI's VMDAS.
	4. **'principal'**: Rotates velocity data into a *streamwise*, *cross-stream*, and *vertical* FoR based on the principal flow direction. One must calculate principal heading first.


.. autosummary::
	:nosignatures:
	
	~dolfyn.rotate.api.rotate2
	~dolfyn.rotate.api.set_declination
	~dolfyn.rotate.api.calc_principal_heading
	~dolfyn.rotate.api.set_inst2head_rotmat
	~dolfyn.rotate.base.euler2orient
	~dolfyn.rotate.base.orient2euler
	~dolfyn.rotate.base.quaternion2orient
	
These functions pertain to both ADCPs and ADVs::

	>> import dolfyn as dlfn
	>> dat = dlfn.read_example('burst_mode01.VEC')
	
	>> dat_mag = dlfn.set_declination(dat, 12) # 12 degrees East
	>> dat_earth = dlfn.rotate2(dat_mag, 'earth') # data is now rotated to true ENU coordinates
	
	>> dat_earth.attrs['principal_heading'] = dlfn.calc_principal_heading(dat_earth['vel'])
	>> dat_flow = dlfn.rotate2(dat_earth, 'principal') # data is now in principal flow directions

.. automodule:: dolfyn.rotate.api
    :members:
    :undoc-members:
    :show-inheritance:
	
.. automodule:: dolfyn.rotate.base
    :members:
    :undoc-members:
    :show-inheritance:
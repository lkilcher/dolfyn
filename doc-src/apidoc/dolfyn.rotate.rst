Rotate Module
=====================

Contains functions for rotating data through frames of reference (FoR):
	1. **'beam'**: Follows the acoustic beam FoR, where velocity data is organized by beam number 1-3 or 1-4.
	2. **'inst'**: The instrument's *XYZ* Cartesian directions. For ADV's, this orientation is from the mark on the ADV body/battery canister, not the sensor head. For TRDI 4-beam instruments, the fourth velocity term is the error velocity (aka *XYZE*). For Nortek 4-beam instruments, this is *XYZ1 Z2*, where *E=Z2-Z1*.
	3. **'earth'**: *East North UP* (*ENU*) FoR. Based on either magnetic or true North, depending on whether or not DOLfYN has a magnetic declination associated with the dataset. Instruments do not internally record magnetic declination, unless it has been supplied via external software like TRDI's VMDAS.
	4. **'princ'**: Rotates velocity data into a *streamwise*, *cross-stream*, and *vertical* FoR based on the principal flow direction. Only applies to ADV data. One must calculate principal heading first.

.. autosummary::
	:nosignatures:
	
	~dolfyn.rotate.main.rotate2
	~dolfyn.rotate.main.calc_principal_heading

.. automodule:: dolfyn.rotate.main
    :members:
    :undoc-members:
    :show-inheritance:
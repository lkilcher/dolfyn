Tools
=====

Spectral analysis and miscellaneous |dlfn| functions are stored here. 
These functions are used throughout |dlfn|'s core code and may also be 
helpful to users in general.

FFT-based Functions:

.. autosummary::
	:nosignatures:
	
	~dolfyn.tools.psd.psd
	~dolfyn.tools.psd.cpsd
	~dolfyn.tools.psd.cpsd_quasisync
	~dolfyn.tools.psd.coherence
	~dolfyn.tools.psd.phase_angle
	~dolfyn.tools.psd.psd_freq

Other Functions:

.. autosummary::
	:nosignatures:
	
	~dolfyn.tools.misc.detrend
	~dolfyn.tools.misc.group
	~dolfyn.tools.misc.slice1d_along_axis
	~dolfyn.tools.misc.fillgaps
	~dolfyn.tools.misc.interpgaps
	~dolfyn.tools.misc.medfiltnan
	~dolfyn.tools.misc.convert_degrees

.. automodule:: dolfyn.tools.psd
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: dolfyn.tools.misc
    :members:
    :undoc-members:
    :show-inheritance:
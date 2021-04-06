"""
This is the Doppler Oceanography Library for pYthoN (DOLfYN). It is
designed to read and work with oceanographyic velocity measurements
from Acoustic Doppler Current Profilers (ADCPs) and Acoustic Doppler
Velocimeters (ADVs). It is a high-level object-oriented library
composed of a set of **data-object** classes (types) that contain data
from a particular measurement instrument, and a collection of
**functions** that manipulate those data objects to accomplish data
processing and data analysis tasks.

"""

from ._version import __version__
from .io.api import read, load, read_example
from .rotate.main import rotate2, orient2euler, euler2orient, calc_principal_heading
from .data.x_velocity import VelBinner, Velocity, TKEdata
from .data.base import TimeData
from .adv import api as adv
from .adp import api as adcp
#from .adp.base import ADPdata, ADPbinner
#from .adv.base import ADVdata
from . import doctools as _dt
#from .adv import api as advtools


#__doc__ = __doc__.format(
#    object_table=_dt.table_obj([Velocity, TKEdata, ]),
#    func_table=_dt.table_obj([read, read_example, load, rotate2, VelBinner]))


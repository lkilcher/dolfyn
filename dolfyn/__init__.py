"""
This is the Doppler Oceanography Library for pYthoN (DOLfYN). It is
designed to read and work with oceanographyic velocity measurements
from Acoustic Doppler Current Profilers (ADPs/ADCPs) and Acoustic Doppler
Velocimeters (ADVs). It is a high-level object-oriented library
composed of a set of **data-object** classes (types) that contain data
from a particular measurement instrument, and a collection of
**functions** that manipulate those data objects to accomplish data
processing and data analysis tasks.

"""

from ._version import __version__
from .io.api import read, read_example, save, load
from .rotate.api import rotate2, calc_principal_heading, set_declination
from .rotate.base import euler2orient, orient2euler, q2orient
from .data.velocity import VelBinner
from dolfyn import adv
from dolfyn import adp
from dolfyn import time
from dolfyn import io
from dolfyn import rotate

# Uncomment h5 for dev/testing
#from dolfyn import h5


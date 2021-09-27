"""
This is the Doppler Oceanography Library for pYthoN (DOLfYN). It is
designed to read and work with oceanographyic velocity measurements
from Acoustic Doppler Current Profilers (ADPs/ADCPs) and Acoustic Doppler
Velocimeters (ADVs). It is a high-level object-oriented library
composed of a set of data-object classes (types) that contain data
from a particular measurement instrument, and a collection of
functions that manipulate those data objects to accomplish data
processing and data analysis tasks.

"""

from ._version import __version__
from .io.api import read, read_example, save, load, save_mat, load_mat
from .rotate.api import rotate2, calc_principal_heading, set_declination
from .rotate.base import euler2orient, orient2euler, quaternion2orient
from .velocity import VelBinner
from dolfyn import adv
from dolfyn import adp
from dolfyn import time
from dolfyn import io
from dolfyn import rotate
from dolfyn import tools

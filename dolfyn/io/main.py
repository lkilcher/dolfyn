"""
Holds the primary high-level interfaces for the io (read/write)
package.
"""
import sys
import inspect
from ..data import base as db
from . import hdf5
from . import mat


# These define the default.
loader = hdf5.Loader
saver = hdf5.Saver


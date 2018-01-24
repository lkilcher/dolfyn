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


def load(fname, data_groups=None,):
    """
    Load data from `fname` into class `type_map`.

    Parameters
    ----------

    fname : string
      The filename to read.

    type : type or list(types)

    """
    with hdf5.loader(fname) as ldr:
        return ldr.load(data_groups)


def mmload(fname):
    """
    Load data from `fname` into class `type_map` as memory mapped
    arrays.

    Parameters
    ----------

    fname : string
      The filename to read.

    type : type or list(types)

    Returns
    -------
    data : A DOLfYN data type.
      The type will match the '_object_type' attribute at the root of
      the file. All data in the file will be accessible as
      memory-mapped arrays.

    """
    with hdf5.loader(fname) as ldr:
        return ldr.mmload('ALL')



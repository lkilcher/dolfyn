"""
This module uses the h5py (HDF5) package to read and write numpy
arrays to disk.

See the h5py and HDF5 documentation for further info on the details of
this approach.

"""


import h5py as h5
import sys
from . import hdf5_legacy as legacy
from pyDictH5.io import load_hdf5

if sys.version_info >= (3, 0):
    import pickle as pkl

    def pkl_loads(s):
        try:
            return pkl.loads(s)
        except UnicodeDecodeError:
            return pkl.loads(s, encoding='bytes')

else:  # Python 2
    input = raw_input
    import cPickle as pkl

    def pkl_loads(s):
        return pkl.loads(s)


def load(fname, data_groups=None,):
    """Load data from ``fname``.

    Parameters
    ----------

    fname : string
      The filename to read.

    data_groups : string or list of strings
      The data groups to load (default: all groups not starting with
      '_').


    """
    if is_pydicth5(fname):
        return load_hdf5(fname, group=data_groups)
    else:
        return legacy.load(fname, data_groups)


def is_pydicth5(fname):
    retval = False
    fd = h5.File(fname, mode='r')
    if fd.attrs.get('__package_name__', None) in [b'pyDictH5', 'pyDictH5']:
        retval = True
    fd.close()
    return retval

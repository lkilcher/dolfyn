"""
This module uses the h5py (HDF5) package to read and write numpy
arrays to disk.

See the h5py and HDF5 documentation for further info on the details of
this approach.

"""


import h5py as h5
import sys
import hdf5_legacy as legacy
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
    """
    Load data from `fname` into class `type_map`.

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
    with Loader(fname) as ldr:
        return ldr.mmload('ALL')


def is_pydicth5(fname):
    retval = False
    fd = h5.File(fname, mode='r')
    if fd.attrs.get('__package_name__', None) == 'pyDictH5':
        retval = True
    fd.close()
    return retval


if __name__ == '__main__':
    # filename='/home/lkilcher/data/eastriver/advb_10m_6_09.h5'
    filename = '/home/lkilcher/data/ttm_dem_june2012/TTM_Vectors/TTM_NRELvector_Jun2012_b5m.h5'
    import adv
    ldr = loader(filename, adv.type_map)
    dat = ldr.load()

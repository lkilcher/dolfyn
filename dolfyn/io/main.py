"""
Holds the primary high-level interfaces for the io (read/write)
package.
"""

import sys
import inspect
from ..data.base import Dgroups
from . import hdf5
from . import mat

# These define the default.
loader = hdf5.Loader
saver = hdf5.Saver


class Saveable(Dgroups):

    """
    An abstract base class for writing objects that are 'Saveable'.
    """

    def save_mat(self, filename, groups=None, appendmat=True,
                 format='5', do_compression=True, oned_as='row'):
        """
        Save data in the object to a matlab file.


        See also
        --------
        scipy.io.save_mat

        """
        with mat.Saver(filename, format=format, do_compression=do_compression,
                       oned_as=oned_as) as svr:
            svr.write(self, groups=groups)

    def save(self, filename, mode='w', where='/', **kwargs):
        """
        Save the data in this object to file `filename` in the DOLfYN
        HDF5 format.

        Parameters
        ----------
        filename : string
          The filename in which to save the data.
        mode : string
          The write mode of the file (default to overwrite the
          existing file).  See File.open for more info.
        where : string
          The location in the hdf5 file to store the data.  (defaults
          to the root of the file, i.e. '/'.)

        See Also:
          the 'File' module
          the 'h5py' module
        """
        with hdf5.Saver(filename, mode=mode) as svr:
            svr.write(self, where=where, **kwargs)

    def load(self, groups, where='/', filename=None,):
        """
        Add data from *groups* in the file *filename*.

        Parameters
        ----------
        groups  : string
          specifies the data 'groups' to load from the file.
        where  : string
          specifies where in the data the groups are loaded (defaults to '/').
        filename  : string
          specifies a file to load data from (default: load data from
          the file this object was loaded from).
        """
        if filename is None:
            filename = self.filename
        # Don't need a typemap, because we are using the current object:
        with hdf5.loader(filename, None) as ldr:
            ldr.load(groups=groups, where=where, out=self)


def get_typemap(space):
    """
    Find the classes in the namespace that have :class:`Saveable` in
    their class heirarchy.

    Parameters
    ----------

    space : namespace
      The namespace in which to find classes that subclass Saveable.

    Returns
    -------

    types : list(types)
      A list containing the types (classes) that subclass Saveable.


    Notes
    -----

    This function is used within a module that defines new data types
    for the DOLfYN package to auto-detect which objects in the
    namespace are types that can be saved.

    """
    type_map = {}
    for name, obj in inspect.getmembers(sys.modules[space]):
        if hasattr(obj, '__mro__') and Saveable in obj.__mro__:
            type_map[str(obj)] = obj
    return type_map


def load(fname, type_map, data_groups=None,):
    """
    Load data from `fname` into class `type_map`.

    Parameters
    ----------

    fname : string
      The filename to read.

    type : type or list(types)

    """
    with hdf5.loader(fname, type_map) as ldr:
        return ldr.load(data_groups)


def mmload(fname, type_map):
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
    with hdf5.loader(fname, type_map) as ldr:
        return ldr.mmload('ALL')


def probeFile(fname):
    """
    Probe a file to determine what data it contains.

    Parameters
    ----------

    fname : string
      The filename to probe.

    Returns
    -------
    type : string
      The type string.

    groups : dict
      A dictionary of the groups, with lists of the data in them.

    """
    out = {}
    with hdf5.loader(fname, None) as ldr:
        for nd, grp in ldr.iter('ALL'):
            grpnm = ldr.get_name(grp)
            if grpnm in out.keys():
                out[grpnm] += [ldr.get_name(nd)]
            else:
                out[grpnm] = [ldr.get_name(nd)]
        tp = ldr.read_type()
        print('Object type: %s' % tp)
    return tp, out

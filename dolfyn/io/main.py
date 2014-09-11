import sys
import inspect
from ..data.base import Dgroups
from . import hdf5
from . import mat

# These define the default.
loader = hdf5.loader
saver = hdf5.saver


class saveable(Dgroups):

    """
    An abstract base class for objects that should be 'saveable'.
    """

    def save_mat(self, filename, groups=None, appendmat=True,
                 format='5', do_compression=True, oned_as='row'):
        """
        Save data in the object, to a matlab file.
        #### THIS NEEDS TO BE UPDATED! ####
        - for meta arrays
        - for properties
        - does it even work at all anymore?
        """
        with mat.saver(filename, format=format, do_compression=do_compression,
                       oned_as=oned_as) as svr:
            svr.write(self, groups=groups)

    def save(self, filename, mode='w', where='/'):
        """
        Save the data in this object to file *filename* in the pyBODT
        hdf5 format.

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
        with hdf5.saver(filename, mode=mode) as svr:
            svr.write(self, where=where)

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
    Find the classes in the namespace *space* that have the saveable
    class in there heirarchy.  These are data objects that should be
    able to be loaded.
    """
    type_map = {}
    for name, obj in inspect.getmembers(sys.modules[space]):
        if hasattr(obj, '__mro__') and saveable in obj.__mro__:
            type_map[str(obj)] = obj
    return type_map


def load(fname, type, data_groups=None,):
    with hdf5.loader(fname, type) as ldr:
        return ldr.load(data_groups)


def mmload(fname, type_map, data_groups=None,):
    with hdf5.loader(fname, type_map) as ldr:
        return ldr.mmload(data_groups)


def probeFile(fname):
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

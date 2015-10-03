"""
This module uses the h5py (HDF5) package to read and write numpy
arrays to disk.

See the h5py and HDF5 documentation for further info on the details of
this approach.

"""


import h5py as h5
try:
    import cPickle as pkl
except:
    import pickle as pkl
from .base import DataFactory
from ..data.base import Dgroups, np, ma, config
from ..data.time import time_array
import copy


class Saver(DataFactory):

    """
    A save data_factory object.  This class saves data in DOLFYN
    classes into DOLFYN format hdf5 files.

    This function should not be used explicitly, instead use the
    :meth:`main.Saveable.save` method of the data object.

    Parameters
    ----------

    filename : string
        Name of fale to save to.

    mode     : string
        File access mode.  Should be 'w' (default) or 'a'.

    where    : string
        Location in hdf5 file to save the data (default: '/')

    max_file_size : int
      option does not currently work.

    See also:
    - file
    - h5py

    """
    ver = 1.3  # The version number of the save format.

    # Version 1.0: underscore ('_') handled inconsistently.
    # Version 1.1: '_' and '#' handled consistently in group naming:
    # '#' is for groups that should be excluded, unless listed explicitly.
    # '##' and ending with '##' is for specially handled groups.
    # Version 1.2: now using time_array.
    #         '_' is for essential groups.
    # Version 1.3: Now load/unload is fully symmetric (needed for __eq__ tests).
    #         Added _config_type to i/o.
    fletcher32 = True
    complib = 'gzip'
    complevel = 2
    shuffle = True

    split_groups_into_files = False
    # Right now, this isn't working, I think it is a bug in h5py.
    # Perhaps later this will work, and it should be pretty
    # transparent.

    def __init__(self, filename, mode='w', where='/', max_file_size_mb=None):
        self.file_mode = mode
        # This does an 'expanduser' on the filename (i.e. '~/'
        # replaced with '/home/<username>/').
        self.filename = filename
        kwargs = {}
        if max_file_size_mb is not None:
            kwargs['driver'] = 'family'
            kwargs['memb_size'] = max_file_size_mb * (2 ** 20)
            # Need to modify the filename to include a %d character.
        self.fd = h5.File(self.filename, mode=self.file_mode, **kwargs)
        self.close = self.fd.close
        self.node = self.fd.get(where)
        self.node.attrs.create('DataSaveVersion', pkl.dumps(self.ver))
        self._extrafiles = []

    def get_group(self, where=None, nosplit=False):
        """
        An internal function for returning the current, or a specified
        node in the hdf5 file.

        Return the h5py node at location `where`, `where` can be:
        - a string indicating a location in the hdf5 file,
        - a node in the hdf5 file (returns this node)
        - None, in which case, the current value of self.node is returned.

        """
        if where is None:
            return self.node
        elif where.__class__ is h5.Group:
            return where
        elif where.__class__ in [str, unicode]:
            if self.split_groups_into_files and where != '/' and not nosplit:
                if self.fd.get(where, None) is None:
                    fname = copy.copy(self.fd.filename)
                    grpname = where.split('/')[-1]
                    if fname.endswith('.h5'):
                        fname = fname[:-2] + grpname + '.h5'
                    else:
                        fname += '.' + grpname
                    thisgroup_file = h5.File(fname, mode=self.file_mode)
                    thisgroup_file.create_group('data')
                    thisgroup_file.close()
                    self.fd[where] = h5.ExternalLink(fname, '/data')
                    return self.fd.get(where)
                else:
                    return self.fd.get(where)
            else:
                return self.fd.require_group(where)
        else:
            raise Exception('Not a valid group specification')

    def write_type(self, obj, where=None):
        """
        Write the type of the object being saved to the hdf5 file.
        This allows for automatic loading of a file into a specific
        DOLfYN class.

        When a file is loaded, a dict of string:class (key:val) pairs
        should be provided to the 'loader' data_factory.  The string
        (key) that matches the value of the file's '_object_type'
        attribute is chosen.  The corresponding class (value) is then
        instanced and data is loaded into it according to the DOLfYN
        specification.

        This function writes the '_object_type' from the current
        DOLfYN instance to the file so that it can be loaded later.

        See also:
        - loader.read_type
        - get_typemap

        """
        self.get_group(where).attrs.create('_object_type', str(obj.__class__))
        if isinstance(obj, config) and obj.config_type not in [None, '*UNKNOWN*']:
            self.get_group(where).attrs.create('_config_type', obj.config_type)

    def write_dict(self, name, dct, where='/'):
        """
        This is a method for writing simple dictionaries.

        It writes the dictionary as attributes in a group.  The keys
        are written as attribute names (only string keys are allowed).
        The values are pickled and written to the attribute value.

        Parameters
        ----------

        name   : string
          name of the dictionary to be written (hdf5 group to create).
        dct    : dict
          The dictionary who's data should be saved.
        where  : string
          The location to write `dct` (a Group named `name` will be
          created at this location).

        """
        tmp = self.get_group(where).require_group(name)
        for ky, val in dct.iteritems():
            tmp.attrs.create(ky, pkl.dumps(val))

    def write(self, obj, where='/', nosplit_file=False, **kwargs):
        """
        Write data in object `obj` to the file at location `where`.
        `obj` should be a DOLfYN type object; a subclass of the
        Dgroups class.

        Parameters
        ----------
        obj    - data_boject
          The object to write to the file.
        where  - string
          The location in the file to write the data in the object
          (default: '/')
        nosplit_file  - bool
          Currently non-functional, for writing data to multiple files.
        """
        nd = self.get_group(where)
        self.write_type(obj, nd)  # Write the data type.
        if hasattr(obj, 'props'):
            self.write_dict('##properties##', obj.props, nd)
                            # Write the 'props' attribute, if the data has one.
        if hasattr(obj, '_units'):
            self.write_dict('##units##', obj._units, nd)
                            # Write the 'units' property if the data has it
                            # (this has been deprecated in the DOLfYN standard,
                            # in favor of meta arrays).
        # iterate over the group names:
        for grp_nm, dat_nms in obj.groups.iteritems():
            grp = self.get_group(where + '/' + grp_nm, nosplit=nosplit_file)
                                # Create or get the group specified.
            for ky in dat_nms:  # Iterate over the data names in the group.
                if not hasattr(obj, ky):
                    continue
                val = getattr(obj, ky)
                if Dgroups in val.__class__.__mro__:
                    self.write(val,
                               where + '/' + grp_nm + '/_' + ky,
                               nosplit_file=True)

                elif isinstance(val, (np.ndarray, )) and len(val) > 0:
                    nd = grp.create_dataset(str(ky),
                                            data=val,
                                            compression=self.complib,
                                            shuffle=self.shuffle,
                                            fletcher32=self.fletcher32,)
                    for kw, d in kwargs.iteritems():
                        if ky in d:
                            nd.attrs.create(str(kw), d[ky])

                    if val.__class__ is time_array:
                        nd.attrs.create('time_var', 'True')

                    if ma.valid and val.__class__ is ma.marray:
                        nd = grp.get(str(ky))
                        # print( 'writing meta data for %s' % ky )
                        for nm, val in val.meta.__dict__.iteritems():
                            if nm not in ['xformat', 'yformat']:
                                # print( nm,val )
                                nd.attrs.create(nm, pkl.dumps(val))

                elif val.__class__ is dict:
                    grp.attrs.create(ky, pkl.dumps(val))
                else:
                    grp.attrs.create(ky, pkl.dumps(val))


# class UpdateTool(DataFactory):

# """
# A class for updating data files when the format specification
# changes.
# """

# def __init__(self, filename, )
# self.file_mode = mode
# This does an 'expanduser' on the filename (i.e. '~/'
# replaced with '/home/<username>/').
# self.filename = filename
# kwargs = {}
# if max_file_size_mb is not None:
# kwargs['driver'] = 'family'
# kwargs['memb_size'] = max_file_size_mb * (2 ** 20)
# Need to modify the filename to include a %d character.
# self.fd = h5.File(self.filename, mode=self.file_mode, **kwargs)
# self.close = self.fd.close
# self.node = self.fd.get('/')
# self.node.attrs.create('DataSaveVersion', pkl.dumps(self.ver))
# self._extrafiles = []

# def change_type_name(self, oldname, newname):
# self.get_group(where).attrs.create('_object_type',
# str(obj.__class__))


class Loader(DataFactory):

    """
    A save data_factory object.  This class saves data in DOLFYN
    classes into DOLFYN format hdf5 files.

    This function should not be used explicitly, instead use the
    :meth:`main.Saveable.save` method of the data object.

    Parameters
    ----------

    filename : string
        Name of fale to save to.
    type_map : (dict, type)
      A mapping of class strings to types (or a specific type) that
      the data should be loaded into.

    """

    def __init__(self, filename, type_map,):
        self.filename = filename
        self.fd = h5.File(self.filename, mode='r+')
                          # Open the file r+ so that we can modify it on the
                          # fly if necessary (e.g. _fix_name)
        self.close = self.fd.close
        self.type_map = type_map
        self.ver = pkl.loads(self.fd.attrs.get('DataSaveVersion', 'I0\n.'))

    def get_group(self, where=None):
        """
        If `where` is:
        - None: return the current node.
        - string: return the node at that address.
        - otherwise return `where` itself.
        """
        if where is None:
            return self.node
        elif where.__class__ in [str, unicode]:
            return self.fd.get(where, None)
        else:
            return where

    def get_name(self, node):
        """
        Return the name of the `node`.
        """
        return node.name.split('/')[-1]

    def iter_data(self, groups=None, where='/'):
        """
        Iterate over data nodes in `groups`.

        See iter_groups for more info on how to specify groups.
        """
        for grp in self.iter_groups(groups=groups, where=where):
            for nd in grp.itervalues():
                yield nd

    def iter(self, groups=None, where='/'):
        """
        Iterate over data nodes in `groups`, with the group name returned.

        See iter_groups for more info on how to specify groups.
        """
        for grp in self.iter_groups(groups=groups, where=where):
            for nd in grp.itervalues():
                yield nd, grp

    __iter__ = iter

    def iter_attrs(self, groups=None, where='/'):
        """
        Iterate over the attributes in `groups`.
        """
        for grp in self.iter_groups(groups=groups, where=where):
            for attnm in grp.attrs.iterkeys():
                if not ((self.ver <= 1.0 and
                         attnm in ['_properties', '_units']) or
                        (attnm.startswith('##') and attnm.endswith('##'))):
                    # Skip the "_properties" attribute, if it exists.
                    yield grp, attnm

    def read_attrs(self, out, groups=None, where='/'):
        """
        Read the attributes in `groups` and add them to `out`.
        """
        for grp, attnm in self.iter_attrs(groups=groups, where=where):
            dat = grp.attrs[attnm]
            try:
                dat = pkl.loads(dat)
            except:
                pass
            out.add_data(attnm, dat, self.get_name(grp))

    def read_props(self, out, where):
        """
        Read the `props` attribute (:class:`Dprops
        <dolfyn.data.base.Dprops>`) class.
        """
        if self.ver >= 1.1:
            propsstr = '##properties##'
            unitsstr = '##units##'
        else:
            propsstr = '_properties'
            unitsstr = '_units'
        if propsstr in self.get_group(where).keys():
            out.props = self.read_dict(where + "/" + propsstr)
        # if unitsstr in self.get_group(where).keys():
        # print( 1 )
        # out._units=self.read_dict(where+"/"+unitsstr)

    def _fix_name(self, nd):
        """
        This is a hook for when the data class definition changes such
        that a data attribute can not be written to the data container
        (object). i.e. when an data attribute is changed to be a
        read-only property.
        """
        var = raw_input(
            """The name '%s' cannot be written to the input.  Do you wish to:
        a) move the data in the file?
        b) specify a different attribute to assign the data to?
        c) skip the attribute (default)?
        """ % (nd.name.rsplit('/', 1)[-1]))
        if var == 'a':
            newnm = raw_input("What name shall the data be reassigned to?")
            grpnm, name = nd.name.rsplit('/', 1)
            grp = self.fd.get(grpnm)
            grp.copy(nd.name, grpnm + '/' + newnm)
            del nd
            return self.fd.get(grpnm + '/' + newnm)
        elif var == 'b':
            return raw_input("What shall the attribute be called?")
        else:
            return None

    def mmload(self, groups=None, where='/', out=None, add_closemethod=True):
        """
        Load the data in `groups` as memory-mapped arrays.

        See Also
        --------

        h5py memory mapped arrays.
        """
        self.closefile = False
        out = self.init_object(out, where=where)
        out.__preload__()
        self.read_props(out, where=where)
        if add_closemethod:
            out._filename = self.filename
            out._fileobject = self.fd
            out.close = self.fd.close
        for nd in self.iter_data(groups=groups, where=where):
            if '_object_type' in nd.attrs.keys():
                out.add_data(self.get_name(nd)[1:],
                             self.mmload(where=nd.name,
                                         add_closemethod=False),
                             self.get_name(nd.parent))
                continue
            if hasattr(nd, 'read_direct'):
                nm = self.get_name(nd)
                out.add_data(nm, nd, self.get_name(nd.parent))
            if (self.ver <= 1.2 and nm == 'mpltime') or \
                    nd.attrs.get('time_var', False) == 'True':
                out[nm] = time_array(out[nm])
        self.read_attrs(out, groups=groups, where=where)
        return out

    def load(self, groups=None, where='/', out=None):
        """
        Load the data in `groups` into memory.
        """
        self.closefile = True
        out = self.init_object(out, where=where)
        out.__preload__()
        self.read_props(out, where=where)
        for nd in self.iter_data(groups=groups, where=where):
            if '_object_type' in nd.attrs.keys():
                out.add_data(self.get_name(nd)[1:], self.load(
                    where=nd.name), self.get_name(nd.parent))
                continue
            if hasattr(nd, 'read_direct'):
                nm = self.get_name(nd)
                out.add_data(
                    nm, np.empty(nd.shape, nd.dtype), self.get_name(nd.parent))
                nd.read_direct(getattr(out, nm))
                               # This puts the data in the output object.
                if (self.ver <= 1.2 and nm == 'mpltime') or \
                        nd.attrs.get('time_var', False) == 'True':
                    out[nm] = out[nm].view(time_array)
                if ma.valid and self.ver == 0:
                    if '_label' in nd.attrs.keys():
                        # This is a deprecated file structure.
                        setattr(out, nm,
                                ma.marray(getattr(out, nm),
                                          meta=ma.varMeta(
                                              nd.attrs.get('_label'),
                                              pkl.loads(nd.attrs.get('_units'))
                                          )
                                          )
                                )
                    if 'label' in nd.attrs.keys():
                        s = nd.attrs.get('units')
                        try:
                            u = pkl.loads(s)
                        except ImportError:
                            # This is to catch a redefinition of data objects.
                            try:
                                u = pkl.loads(
                                    s.replace('cdata_base',
                                              'cdata').replace('unitsDict',
                                                               'dict'))
                            except:
                                u = pkl.loads(
                                    s.replace('cdata_base', 'cdata.marray'))
                        setattr(out, nm,
                                ma.marray(getattr(out, nm),
                                          meta=ma.varMeta(
                                              nd.attrs.get('label'),
                                              u,
                                              pkl.loads(
                                                  nd.attrs.get('dim_names'))
                                          )
                                          )
                                )
                elif ma.valid:
                    if '_name' in nd.attrs.keys():
                        # Confirm this is a meta array
                        s = nd.attrs.get('_units')
                        try:
                            u = pkl.loads(s)
                        except ImportError:
                            # This is to catch a redefinition of data objects.
                            u = pkl.loads(s.replace('cdata_base', 'cdata'))
                        meta = ma.varMeta(pkl.loads(nd.attrs.get('_name')),
                                          u,
                                          pkl.loads(nd.attrs.get('dim_names'))
                                          )
                        for atnm in nd.attrs.keys():
                            if atnm not in ['_name', '_units', 'dim_names']:
                                setattr(meta, atnm, pkl.loads(nd.attrs.get(atnm)))
                        setattr(out, nm, ma.marray(getattr(out, nm), meta=meta))
        self.read_attrs(out, groups=groups, where=where)
        out.__postload__()
        return out

    def read_dict(self, where):
        """
        Read a dictionary object at `where`.
        """
        out = {}
        nd = self.get_group(where)
        for prpnm, prp in nd.attrs.iteritems():
            try:
                out[prpnm] = pkl.loads(prp)
            except TypeError:
                out[prpnm] = prp
        return out

    def read_type(self, where='/'):
        """
        Read the type of object at `where`.
        """
        try:
            return self.get_group(where).attrs['_object_type']
        except KeyError:
            print('Old style data file, trying to load...')
            return self.get_group(where).attrs['object_type']

    def init_object(self, out, where='/'):
        """
        Look at the 'object_type' attribute in the node at `where`.

        Return an attribute of the data type based on type_map.

        If the type_map does not have a key of the type found in the file,
        the basic type is used.
        """
        if out is None:
            if self.type_map.__class__ is dict:
                typestr = self.read_type(where=where)
                if typestr in self.type_map:
                    out = self.type_map[typestr]()
                else:
                    if typestr.endswith("config'>"):
                        # This is a catch for deleted module-specific config
                        # objects
                        out = config()
                        nd = self.get_group(where)
                        if '_config_type' in nd.attrs:
                            out.config_type = nd.attrs.get('_config_type')
                    else:
                        try:
                            out = self.type_map[
                                typestr.split('.')[-1].rstrip("'>")]()
                        except:
                            for ky in self.type_map:
                                #print(ky)
                                if ky.endswith(typestr.split('.')[-1]):
                                    out = self.type_map[ky]()

            else:  # Then it is a type itself.
                out = self.type_map()
        return out

    def iter_groups(self, groups=None, where='/', no_essential=False):
        """
        Returns an iterator of the groups in `groups`.
        Here is how `groups` specification works:

        +-------------+-----------------------------------------------+
        | `groups`    |   Result                                      |
        +=============+===============================================+
        | None        |  (default) Return iterator for 'default'      |
        |             |  groups (those not starting with '#' or '/'.) |
        +-------------+-----------------------------------------------+
        | [<a list>]  |  Iterates over the groups in the list (plus   |
        |             |  the data in 'essential' groups, ie those     |
        |             |  starting with '_'\*\*\*).                    |
        +-------------+-----------------------------------------------+
        | 'ALL'       |  Iterates over all the data in the file.      |
        +-------------+-----------------------------------------------+

        \*\*\*: Unless no_essential=True

        """

        for grp in self.get_group(where).itervalues():
            if grp.__class__ is h5.highlevel.Group:
                gnm = self.get_name(grp)

                if groups is None:
                    if not (gnm[0] in ['#', '/'] or
                            (self.ver <= 1 and gnm in ['_properties',
                                                       '_units'])):
                        yield grp

                elif groups == 'ALL':
                    if not ((gnm.startswith('##') and gnm.endswith('##')) or
                            (self.ver <= 1 and gnm in ['_properties',
                                                       '_units'])):
                        yield grp

                elif gnm in groups or (gnm[0] == '_' and not no_essential):
                    yield grp


if __name__ == '__main__':
    # filename='/home/lkilcher/data/eastriver/advb_10m_6_09.h5'
    filename = '/home/lkilcher/data/ttm_dem_june2012/TTM_Vectors/TTM_NRELvector_Jun2012_b5m.h5'
    import adv
    ldr = loader(filename, adv.type_map)
    dat = ldr.load()

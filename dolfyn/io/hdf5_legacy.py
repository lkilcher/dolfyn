"""
This module uses the h5py (HDF5) package to read and write numpy
arrays to disk.

See the h5py and HDF5 documentation for further info on the details of
this approach.

"""
# pylint: disable=no-member

import h5py as h5
import numpy as np
from . import base
from ..data import base_legacy as db
from ..data import time as dt
import copy
from six import string_types
import sys
from .. import _version as _ver
import warnings
try:
    # There is an organizational inconsistenty in different versions of h5py.
    h5_group = h5.Group
except AttributeError:
    # This is going away, but just in case we're using a version that doesn't have the above, here is this
    h5_group = h5.highlevel.Group


if sys.version_info >= (3, 0):
    import pickle as pkl

    def pkl_loads(s):
        try:
            return pkl.loads(s)
        except UnicodeDecodeError:
            return pkl.loads(s, encoding='bytes')

else:  # Python 2
    input = raw_input  # pylint: disable=undefined-variable
    import cPickle as pkl # pylint: disable=undefined-variable, import-error

    def pkl_loads(s):
        return pkl.loads(s)


class Saver(base.DataFactory):

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
    ver = _ver.version_info

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
        self.node.attrs.create(b'DataSaveVersion',
                               pkl.dumps(_ver.ver2tuple(self.ver)))
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
        elif isinstance(where, string_types):
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
        if isinstance(obj, db.config) and obj.config_type not in [None, '*UNKNOWN*']:
            self.get_group(where).attrs.create('_config_type', obj.config_type.encode('ascii'))

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
        for ky, val in list(dct.items()):
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
        for grp_nm, dat_nms in list(obj.groups.items()):
            grp = self.get_group(where + '/' + grp_nm, nosplit=nosplit_file)
                                # Create or get the group specified.
            for ky in dat_nms:  # Iterate over the data names in the group.
                if not hasattr(obj, ky):
                    continue
                val = getattr(obj, ky)
                if isinstance(val, np.ndarray) and val.dtype.name.startswith('unicode'):
                    val = val.astype('S')
                if db.Dgroups in val.__class__.__mro__:
                    self.write(val,
                               where + '/' + grp_nm + '/_' + ky,
                               nosplit_file=True)

                elif isinstance(val, np.ndarray) and len(val) > 0:
                    nd = grp.create_dataset(str(ky),
                                            data=val,
                                            compression=self.complib,
                                            shuffle=self.shuffle,
                                            fletcher32=self.fletcher32,)
                    for kw, d in list(kwargs.items()):
                        if ky in d:
                            nd.attrs.create(str(kw), d[ky])

                    if val.__class__ is dt.time_array:
                        nd.attrs.create('time_var', 'True')

                    if db.ma.valid and val.__class__ is db.ma.marray:
                        nd = grp.get(str(ky))
                        # print( 'writing meta data for %s' % ky )
                        for nm, val in list(val.meta.__dict__.items()):
                            if nm not in ['xformat', 'yformat']:
                                # print( nm,val )
                                nd.attrs.create(nm, pkl.dumps(val))

                elif val.__class__ is dict:
                    grp.attrs.create(ky, pkl.dumps(val))
                else:
                    grp.attrs.create(ky, pkl.dumps(val))


# class UpdateTool(base.DataFactory):

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


class Loader(base.DataFactory):

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
        self.ver = _ver.ver2tuple(pkl.loads(
            self.fd.attrs.get(b'DataSaveVersion', b'I0\n.')))

    def get_group(self, where=None):
        """
        If `where` is:
        - None: return the current node.
        - string: return the node at that address.
        - otherwise return `where` itself.
        """
        if where is None:
            return self.node
        elif isinstance(where, string_types):
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
            for nd in list(grp.values()):
                yield nd

    def iter(self, groups=None, where='/'):
        """
        Iterate over data nodes in `groups`, with the group name returned.

        See iter_groups for more info on how to specify groups.
        """
        for grp in self.iter_groups(groups=groups, where=where):
            for nd in list(grp.values()):
                yield nd, grp

    __iter__ = iter

    def iter_attrs(self, groups=None, where='/'):
        """
        Iterate over the attributes in `groups`.
        """
        for grp in self.iter_groups(groups=groups, where=where):
            for attnm in list(grp.attrs.keys()):
                if not ((self.ver <= (0, 1, 0) and
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
                dat = pkl_loads(dat)
            except:
                pass
            out.add_data(attnm, dat, self.get_name(grp))

    def read_props(self, out, where):
        """
        Read the `props` attribute (:class:`Dprops
        <dolfyn.data.base.Dprops>`) class.
        """
        if self.ver >= (0, 1, 1):
            propsstr = '##properties##'
            unitsstr = '##units##'
        else:
            propsstr = '_properties'
            unitsstr = '_units'
        if propsstr in self.get_group(where):
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
        var = input((
            """The name '%s' cannot be written to the input.  Do you wish to:
        a) move the data in the file?
        b) specify a different attribute to assign the data to?
        c) skip the attribute (default)?
        """ % (nd.name.rsplit('/', 1)[-1])))
        if var == 'a':
            newnm = input("What name shall the data be reassigned to?")
            grpnm, name = nd.name.rsplit('/', 1)
            grp = self.fd.get(grpnm)
            grp.copy(nd.name, grpnm + '/' + newnm)
            del nd
            return self.fd.get(grpnm + '/' + newnm)
        elif var == 'b':
            return input("What shall the attribute be called?")
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
            if '_object_type' in nd.attrs:
                out.add_data(self.get_name(nd)[1:],
                             self.mmload(where=nd.name,
                                         add_closemethod=False),
                             self.get_name(nd.parent))
                continue
            if hasattr(nd, 'read_direct'):
                nm = self.get_name(nd)
                out.add_data(nm, nd, self.get_name(nd.parent))
            if (self.ver <= (0, 1, 2) and nm == 'mpltime') or \
                    nd.attrs.get('time_var', False) == b'True':
                out[nm] = dt.time_array(out[nm])
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
            if '_object_type' in nd.attrs:
                out.add_data(self.get_name(nd)[1:], self.load(
                    where=nd.name), self.get_name(nd.parent))
                continue
            if hasattr(nd, 'read_direct'):
                nm = self.get_name(nd)
                dtype = nd.dtype
                out.add_data(nm, np.empty(nd.shape, dtype), self.get_name(nd.parent))
                # This puts the data in the output object:
                nd.read_direct(getattr(out, nm))
                if nd.dtype.char == 'S' and sys.version_info >= (3, 0):
                    # This catches a bug in Python3 when reading string arrays
                    # (converts bytes to unicode)
                    out[nm] = out[nm].astype('<U')
                if (self.ver <= (0, 1, 2) and nm == 'mpltime') or \
                        nd.attrs.get('time_var', False) == b'True':
                    out[nm] = out[nm].view(dt.time_array)
                if db.ma.valid and self.ver == (0, 0, 0):
                    if '_label' in nd.attrs:
                        # This is a deprecated file structure.
                        setattr(out, nm,
                                db.ma.marray(getattr(out, nm),
                                             meta=db.ma.varMeta(
                                                 nd.attrs.get('_label'),
                                                 pkl_loads(nd.attrs.get('_units'))
                                )))
                    if 'label' in nd.attrs:
                        s = nd.attrs.get('units')
                        try:
                            u = pkl_loads(s)
                        except ImportError:
                            # This is to catch a redefinition of data objects.
                            try:
                                u = pkl_loads(
                                    s.replace('cdata_base',
                                              'cdata').replace('unitsDict',
                                                               'dict'))
                            except:
                                u = pkl_loads(
                                    s.replace('cdata_base', 'cdata.marray'))
                        setattr(out, nm,
                                db.ma.marray(getattr(out, nm),
                                             meta=db.ma.varMeta(
                                                 nd.attrs.get('label'),
                                                 u,
                                                 pkl_loads(
                                                     nd.attrs.get('dim_names'))
                                             )
                                )
                                )
                elif db.ma.valid:
                    if '_name' in nd.attrs:
                        # Confirm this is a meta array
                        s = nd.attrs.get('_units')
                        try:
                            u = pkl_loads(s)
                        except ImportError:
                            # This is to catch a redefinition of data objects.
                            u = pkl_loads(s.replace('cdata_base', 'cdata'))
                        meta = db.ma.varMeta(pkl_loads(nd.attrs.get('_name')),  # pylint: disable=assignment-from-none
                                             u,
                                             pkl_loads(nd.attrs.get('dim_names'))
                        )
                        for atnm in nd.attrs:
                            if atnm not in ['_name', '_units', 'dim_names']:
                                setattr(meta, atnm, pkl_loads(nd.attrs.get(atnm)))
                        setattr(out, nm, db.ma.marray(getattr(out, nm), meta=meta))
        self.read_attrs(out, groups=groups, where=where)
        self._check_compat(out)
        out.__postload__()
        return out

    def _check_compat(self, out):
        if self.ver < (0, 6, 0):
            for old_name, new_name in [('_u', 'vel'),
                                       ('_corr', 'corr'),
                                       ('_amp', 'amp'),
                                       ('urot', 'velrot'),
                                       ('uacc', 'velacc'),
                                       ('_tke', 'tke_vec'), ]:
                if old_name in out.data_names:
                    g = out.groups.get_group(old_name)
                    out.add_data(new_name, out.pop_data(old_name), g)
                if hasattr(out, 'props') and old_name in out.props.get('rotate_vars', []):
                    out.props['rotate_vars'].remove(old_name)
                    out.props['rotate_vars'].add(new_name)

    def read_dict(self, where):
        """
        Read a dictionary object at `where`.
        """
        out = {}
        nd = self.get_group(where)
        for prpnm, prp in list(nd.attrs.items()):
            try:
                out[prpnm] = pkl_loads(prp)
            except TypeError:
                out[prpnm] = prp.decode('utf-8')
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
            nd = self.get_group(where)
            if self.type_map.__class__ is dict:
                typestr = self.read_type(where=where).decode('utf-8')
                # print(typestr)
                # pdb.set_trace()

                if typestr in self.type_map:
                    out = self.type_map[typestr]()
                else:
                    if typestr.endswith("config'>"):
                        # This is a catch for deleted module-specific config
                        # objects
                        out = db.config()
                    else:
                        try:
                            out = self.type_map[typestr.split('.')[-1]
                                                .rstrip("'>")]()
                        except KeyError:
                            for ky in self.type_map:
                                #print(ky)
                                if ky.endswith(typestr.split('.')[-1]):
                                    out = self.type_map[ky]()

            else:  # Then it is a type itself.
                out = self.type_map()
            if '_config_type' in nd.attrs:
                out.config_type = nd.attrs.get('_config_type').decode('utf-8')
        return out

    def iter_groups(self, groups=None, where='/', no_essential=False):
        r"""
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
        |             |  starting with '_').                          |
        +-------------+-----------------------------------------------+
        | 'ALL'       |  Iterates over all the data in the file.      |
        +-------------+-----------------------------------------------+

        \*\*\*: Unless no_essential=True

        """

        for grp in list(self.get_group(where).values()):
            if grp.__class__ is h5_group:
                gnm = self.get_name(grp)

                if groups is None:
                    if not (gnm[0] in ['#', '/'] or
                            (self.ver <= (0, 1, 0) and gnm in ['_properties',
                                                               '_units'])):
                        yield grp

                elif groups == 'ALL':
                    if not ((gnm.startswith('##') and gnm.endswith('##')) or
                            (self.ver <= (0, 1, 0) and gnm in ['_properties',
                                                               '_units'])):
                        yield grp

                elif gnm in groups or (gnm[0] == '_' and not no_essential):
                    yield grp


def load(fname, data_groups=None, fix_by_overwrite=False):
    from ..adp import base_legacy as adp_base_legacy
    from ..adv import base_legacy as adv_base_legacy
    #pdb.set_trace()
    type_map = dict(**adp_base_legacy.type_map)
    type_map.update(adv_base_legacy.type_map)
    with Loader(fname, type_map) as ldr:
        dat = ldr.load(data_groups)
    out = convert_from_legacy(dat)
    if fix_by_overwrite:
        out.to_hdf5(fname)
        warnings.warn("Updating the data format...")
    else:
        warnings.warn("The data format is old and will be deprecated in the "
                      "future. Consider updating the format of '{}' by "
                      "overwriting the file with the loaded object."
                      .format(fname))
    return out


def convert_from_legacy(dat):
    from ..data import base as db
    typestr = str(type(dat))
    if '.adcp_raw' in typestr:
        from ..adp.base import adcp_raw as TypeNow
    elif '.adcp_binned' in typestr:
        from ..adp.base_legacy import adcp_binned as TypeNow
    elif '.ADVraw' in typestr:
        from ..adv.base import ADVraw as TypeNow
    elif '.ADVbinned' in typestr:
        from ..adv.base import ADVbinned as TypeNow
    out = TypeNow()
    out['config'] = db.config()
    out['config'].update(**dat.config)
    # out = compare_config(old['config'], new['config'])
    for g, ky in dat.groups.iter():
        if g == 'config':
            # This is handled above.
            continue
        if g.startswith('#'):
            g = g[1:]
        if g == 'extra':
            g = '_extra'
        if g == 'index':
            g = 'sys'
        if ky == 'pressure':
            g = 'env'
        if ky == 'AnaIn2MSB':
            g = '_extra'
        if ky == 'orientation_down':
            g = 'orient'
        if g in ['main', '_essential']:
            dnow = out
        else:
            if g not in out:
                out[g] = db.TimeData()
            dnow = out[g]
        try:
            dnow[ky] = dat[ky]
        except KeyError:
            dnow[ky + '_'] = dat[ky]
    out['props'] = dict(copy.deepcopy(dat.props))
    p = out['props']
    if 'Acc' in out['orient']:
        out['orient']['accel'] = out['orient'].pop('Acc') * 9.81
    if 'Acc_b5' in out['orient']:
        out['orient']['accel_b5'] = out['orient'].pop('Acc_b5') * 9.81
    if 'ahrs_gyro' in out['orient']:
        out['orient']['angrt'] = out['orient'].pop('ahrs_gyro') * np.pi / 180
    if 'accel' in out['orient']:
        p['has imu'] = True
    else:
        p['has imu'] = False
    if out['config']['config_type'] == 'Nortek AD2CP':
        p['inst_make'] = "Nortek"
        p['inst_model'] = 'Signature'
        p['inst_type'] = 'ADP'
    if 'inst_make' in p and p['inst_make'] == 'Nortek':
        convert_config(out['config'])
        if p['inst_model'] == 'VECTOR':
            convert_vector(dat, out)
        elif p['inst_model'] == 'Signature':
            convert_signature(dat, out)
        elif p['inst_model'] == 'AWAC':
            convert_awac(dat, out)
        if '.ADVbinned' in typestr:
            tmp = out.pop('spec')
            out['Spec'] = db.FreqData()
            out['Spec']['vel'] = tmp['Spec']
            out['Spec']['omega'] = out.pop('omega')
        if 'rotate_vars' in p:
            for ky in ['velrot', 'velacc',
                       'accel', 'acclow',
                       'angrt', 'mag']:
                if ky in p['rotate_vars']:
                    p['rotate_vars'].remove(ky)
                    p['rotate_vars'].add('orient.' + ky)
    else:
        convert_rdi(dat, out)
    return out


def convert_awac(dat, out):
    out['config']['_type'] = 'NORTEK Header Data'
    out['props'].pop('toff')


def convert_signature(dat, out):
    out['config']['_type'] = 'Nortek AD2CP'
    ornt = out['orient']
    for ky in ['heading', 'pitch', 'roll']:
        ornt[ky] = out.pop(ky)
    out.props.pop('fs')
    out['range'] = (np.arange(out['vel'].shape[1]) *
                    out['config']['cell_size'] +
                    out['config']['blanking'])
    out['range_b5'] = (np.arange(out['vel_b5'].shape[1]) *
                       out['config']['cell_size_b5'] +
                       out['config']['blanking_b5'])


def convert_vector(dat, out):
    out['props'].pop('doppler_noise')
    out['props'].pop('toff')
    out['config']['_type'] = 'NORTEK Header Data'


def convert_config(config):
    from ..data import base as dbnew
    if 'config_type' in config:
        config['_type'] = config.pop('config_type')
    for ky in config:
        if isinstance(config[ky], db.config):
            config[ky] = dbnew.config(**config[ky])
            convert_config(config[ky])


def convert_rdi(dat, out):
    out['config']['_type'] = out['config'].pop('config_type')
    if 'ranges' in out:
        out['range'] = out.pop('ranges')
    if 'envir' in out:
        out['env'] = out.pop('envir')
    out['props']['inst_make'] = dat.props.get('inst_make', 'RDI')
    out['props']['inst_model'] = dat.props.get('inst_model', '<WORKHORSE?>')
    out['props']['inst_type'] = dat.props.get('inst_type', 'ADP')
    out['props']['rotate_vars'] = dat.props.get('rotate_vars', {'vel'})
    odat = out['orient']
    for ky in ['roll', 'pitch', 'heading']:
        odat[ky] = odat.pop(ky + '_deg')

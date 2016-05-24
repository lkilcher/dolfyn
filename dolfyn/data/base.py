import numpy as np
import copy
from ..meta import api_dumb as ma
import numpy.testing as nptest
#from ..OrderedSet import OrderedSet as oset
oset = set

debug_level = 0
objEQ_allclose_tols = dict(rtol=1e-3, atol=1e-6)


class DataError(Exception):
    pass

rad_hz = ma.marray(2 * np.pi, ma.varMeta('', {'s': -1, 'hz': -1}))


def cat(a, axis=0):
    out = np.concatenate(a, axis)
    if ma.valid and (a[0].__class__ is ma.marray):
        out = ma.marray(out, a[0].meta)
        for tmp in a[1:]:
            if not tmp.meta == a[0].meta:
                print("Concatenated objects have different units!")
    return out


def _equiv_dict(d1, d2):
    if set(d2.keys()) == set(d1.keys()):
        retval = True
        for ky in d1:
            try:
                if isinstance(d1[ky], np.ndarray):
                    assert type(d1[ky]) is type(d2[ky])  # nopep8
                    assert d1[ky].shape == d2[ky].shape
                    if (not np.issubdtype(d1[ky].dtype, np.inexact)) or \
                       objEQ_allclose_tols == dict(rtol=0, atol=0):
                        nptest.assert_equal(d1[ky], d2[ky])
                    else:
                        assert np.allclose(d1[ky], d2[ky], equal_nan=True, **objEQ_allclose_tols)
                elif isinstance(d1[ky], dict):
                    assert _equiv_dict(d1[ky], d2[ky])
                else:
                    assert d1[ky] == d2[ky]
            except AssertionError:
                retval = False
                if debug_level > 0:
                    print('The values in {} do not match between the data objects.'
                          .format(ky, d1, d2))
                    if isinstance(d1[ky], np.ndarray):
                        try:
                            assert np.allclose(d1[ky], d2[ky], rtol=1e-3, equal_nan=True)
                            print(' ... but they are close.')
                        except:
                            pass
                else:
                    return False
        return retval
    if debug_level > 0:
        dif1 = set(d1.keys()) - set(d2.keys())
        dif2 = set(d2.keys()) - set(d1.keys())
        print("The list of items are not the same.\n"
              "Entries in 1 that are not in 2: {}\n"
              "Entries in 2 that are not in 1: {}".format(list(dif1), list(dif2)))
    return False


class Dbase(object):

    """
    The base data object class.
    """
    def __eq__(self, other):
        """
        Test for equivalence, between data objects.
        """
        if type(other) is not type(self):
            return False
        return _equiv_dict(self.__dict__, other.__dict__)


class props(dict):

    def copy(self,):
        """
        P.copy() -> a deepcopy of P
        """
        return copy.deepcopy(self)


class Dprops(Dbase):

    """
    A base data class, which implements the 'props' attribute.
    """

    def __eq__(self, other):
        val = Dbase.__eq__(self, other)
        p = _equiv_dict(self.props, other.props)
        return val and p

    @property
    def props(self,):
        if not hasattr(self, '__props__'):
            self.__props__ = props({'fs': None})
        return self.__props__

    @props.setter
    def props(self, val):
        self.__props__ = props(val).copy()

    def __getattr__(self, nm):
        if nm in self.__getattribute__('__props__').keys():
            return self.props[nm]
        return self.__getattribute__(nm)

    # @property
    # def fs(self,):
    # return self.props['fs']
    # @fs.setter
    # def fs(self,val):
    # self.props['fs']=val

    # def _update_props(self,obj=None,**kwargs):
    # self.groups=self._get_props('groups')
    # self.props=self._get_props('props')
    # self._lbls=self._get_props('_lbls')
    # self._units=self._get_props('_units')
    # if obj is not None:
    # self.props=obj._get_props('props')
    # for ky,val in kwargs.iteritems():
    # self.props[ky]=val

    # @property
    # def toff(self,):
    # if 'toff' not in self.props.keys():
    # return self.props['toff']
    # return 0
    # @toff.setter
    # def toff(self,val):
    # self.props['toff']=val

    # def _get_props(self,attr_nm):
    # For now all attributes I will deal with in this way will be dicts.
    # If this changes, I may need to use:
    # if prps.__class__ is dict:
    # prps={}
    # for cls in list(self.__class__.__mro__)[-1::-1]:
    # if hasattr(cls,attr_nm):
    # tmp=getattr(cls,attr_nm)
    # if tmp.__class__ is property:
    # prps.update(**tmp.fget(self))
    # else:
    # prps.update(**tmp)
    # Now update it to the current values:
    # if hasattr(self,attr_nm):
    # prps.update(**getattr(self,attr_nm))
    # for prp in prps.keys():
    # if prps[prp]=='#delete#':
    # prps.pop(prp)
    # return prps

    # def _copy_props(self,obj):
    # obj.props=copy.deepcopy(self.props)


class groups(dict):

    def __init__(self, *args, **kwargs):
        if dict in args[0].__class__.__mro__:
            dict.__init__(self, *args, **kwargs)
        else:
            dict.__init__(self, {'main': oset([]),
                                 '_essential': oset([])},
                          *args, **kwargs)

    def __repr__(self,):
        s = '{'
        sp = ''
        for k in np.sort(self.keys()):
            s += (sp + "'%s'" + ((15 - len(k)) * ' ') + ": %s,\n") % (
                k, self[k].__repr__())
            sp = ' '
        s = s.rstrip('\n')
        s += '}'
        return s

    def copy(self,):
        """
        G.copy() -> a deepcopy of G
        """
        return copy.deepcopy(self)

    def iter(self, groups=None):
        """
        Iterate over data objects in self

        Returns an iterator, which yields:
           *group_name*,*data_name_in_group*
        """
        for grpnm in (groups or self):
            for dnm in self[grpnm]:
                yield grpnm, dnm

    @property
    def data_names(self,):
        anms = oset([])
        for gnms in self.itervalues():
            anms |= oset(gnms)
        return anms

    def remove(self, name):
        for grp, vals in self.items():
            if name in vals:
                self[grp].remove(name)

    def add(self, name, group='main'):
        """
        Add *name* to *group* in self.

        If *group* is not in self.groups, it is initialized.

        All instances of *name* in other groups are removed.
        """
        if not isinstance(name, str) and hasattr(name, '__iter__'):
            for nm in name:
                self.add(nm, group=group)
            return
        if group not in self.keys():
            self[group] = oset([])
        self[group].add(name)
        # This next block makes sure no other groups have name in them.
        for grp, vals in self.items():
            if grp != group:
                if name in vals:
                    vals.remove(name)

    def get_group(self, name):
        """
        Return the group that contains *name*.

        If it is not in a group, return 'main'.
        """
        for grp, nms in self.items():
            if name in nms:
                return grp
        return 'main'


class Dgroups(Dbase):

    """
    This class implements 'data groups' which are used to organize
    datasets.  (also, the io package uses them for loading and saving
    subsets of a data object).

    The critical attribute is the 'data_groups' property.
    """

    @property
    def data_names(self,):
        return self.groups.data_names

    @property
    def groups(self,):
        if not hasattr(self, '__data_groups__'):
            self.__data_groups__ = groups(
                {'main': oset([]), '_essential': oset([])})
        return self.__data_groups__

    @groups.setter
    def groups(self, val):
        self.__data_groups__ = groups(val).copy()

    def iter(self, groups=None,):
        """
        Iterate over data objects in self.groups.

        Returns an iterator that yields:
           *data_name*,*data*

        Parameters:
          *groups* may specify a subset of groups to iterate over.
        """
        for grpnm, dnm in self.groups.iter(groups=groups):
            yield dnm, getattr(self, dnm)

    # This needs to behave like a dict!
    #__iter__ = iter
    iteritems = iter

    def iter_wg(self, groups=None):
        """
        Iterate over data objects "with groups" in self.groups.

        Returns an iterator that yields:
           *data_name*,*data*,*group_name*

        Parameters:
          *groups* may specify a subset of groups to iterate over.
        """
        for grpnm, dnm in self.groups.iter(groups=groups):
                yield dnm, getattr(self, dnm), grpnm

    def init_data(self, shape, name, dtype=np.float64, group=None, meta=None):
        """
        Initialize an empty array of shape *shape*, and *dtype*.

        If dtype is not specified, it defaults to that specified in
        the objects _data_types[*name*] property.  If there is no
        *name* in _data_types, it defaults to np.float64.

        The data 'group' may also be specified (for loading, and
        saving to hdf5 files).
        """
        if name is not None:
            dat = ma.marray(np.empty(shape, dtype=dtype), meta)
            self.add_data(name, dat, group=group)
            if np.issubdtype(dtype, float):
                getattr(self, name)[:] = np.NaN

    def append(self, other, nan_joint=False):
        """
        Append data from other data objects to this one.

        Only the data in groups is updated.
        i.e.:
        This does not update props or meta.

        *nan_joint* is a logical flag that specifies whether to
        insert a slice of NaN between the datasets.
        """
        if self.__class__ is not other.__class__:
            raise Exception('Classes must match to join objects.')
        n = len(self)
        for (nm, dat), (onm, odat) in zip(self, other):
            try:
                dim = self._time_dim(dat, n)
            except (ValueError, AttributeError):
                # No dimension with that shape, so skip it.
                continue
            if nan_joint:
                shp = list(dat.shape)
                shp[dim] = 1
                dtmp = (dat, np.ones(shp) * np.NaN, odat)
            else:
                dtmp = (dat, odat)
            setattr(self, nm, cat(dtmp, axis=dim))
            del dtmp
        return self

    def __iadd__(self, other):
        """
        See append.
        """
        return self.append(other)

    def subset(self, inds=slice(None), group=None):
        """
        Return a copy of the data, subsetted by *inds*.

        *inds* defaults to return all of the data (used to get a copy
         of the data).

        *group* may be specified to load only some of the variables.
        """
        out = self.__class__()
        if hasattr(self, 'props'):
            out.props = self.props
        for grp, nm in self.groups.iter(group):
            if hasattr(self, nm):
                dt = copy.copy(self.__getattribute__(nm))
                if ((inds is not None and hasattr(dt, 'shape') and
                     dt.shape[-1] == self.shape[-1])):
                    dt = dt[..., inds]
                    if np.any(np.array(dt.shape) == 0):
                        raise IndexError('The indexing object yields empty arrays.')
                out.add_data(nm, dt, group=grp)
        return out

    def del_data(self, *args):
        if args[0].__class__ in [list, tuple]:
            args = args[0]
        for nm in args:
            delattr(self, nm)
            self.groups.remove(nm)

    def add_data(self, name, dat, group=None, meta=None):
        if group is None:
            group = self.groups.get_group(name)
        self.groups.add(name, group)
        setattr(self, name, ma.marray(dat, meta))

    def __getitem__(self, indx):
        return getattr(self, indx)

    def __setitem__(self, indx, dat):
        self.add_data(indx, dat)

    def pop_data(self, name,):
        self.groups.remove(name)
        tmp = getattr(self, name)
        delattr(self, name)
        return tmp

    def __preload__(self,):
        """
        This is called just after object creation, and just prior to
        data being loaded from disk.

        It is a placeholder for modifying data types at load time.
        """
        pass

    def __postload__(self,):
        """
        This is called just after data is loaded from disk.

        It is a placeholder for modifying data types at load time.
        """
        pass

    def copy(self,):
        out = self.__class__()
        for dnm, dat, gnm in self.iter_wg():
            if hasattr(dat, 'copy'):
                out.add_data(dnm, dat.copy(), gnm)
            else:
                out.add_data(dnm, copy.deepcopy(dat), gnm)
        if hasattr(self, 'props'):
            out.props = self.props  # implicit copy()
        out.groups = self.groups  # implicit copy()
        return out

    @property
    def shapes(self,):
        out = {}
        for nm, dat in self:
            out[nm] = dat.shape
        return out


class TimeBased(Dprops, Dgroups):

    def __len__(self):
        """
        Returns the number of timesteps in the object.
        """
        return len(self.mpltime)

    def _time_dim(self, dat, n=None):
        """
        Return the dimension of the array self.*name* that has size=*n*.
        If *n* is none,
        """
        if n is None:
            n = len(dat)
        if ma.valid and ma.marray in dat.__class__.__mro__:
            return dat.getdim('time')
        return dat.shape.index(n)

    @property
    def toff(self,):
        if 'toff' not in self.props.keys():
            self.props['toff'] = 0.0
        return self.props['toff']

    @toff.setter
    def toff(self, val):
        self.props['toff'] = val


class config(Dgroups, dict):

    """
    A config object
    """
    _lvl_spaces = 3

    def __init__(self, config_type='*UNKNOWN*'):
        self.config_type = config_type

    def __eq__(self, other):
        return _equiv_dict(self, other) and type(self) is type(other)

    def __getitem__(self, indx):
        return dict.__getitem__(self, indx)

    def __setitem__(self, indx, dat):
        dict.__setitem__(self, indx, dat)

    def __setattr__(self, nm, val):
        self[nm] = val

    def __copy__(self, ):
        out = self.__class__(self.config_type)
        for nm in self:
            out[nm] = copy.copy(self[nm])
        return out

    copy = __copy__

    def __getattr__(self, nm):
        if nm not in self.keys():
            raise AttributeError("{} object has no attribute '{}'".format(self.__class__, nm))
        return self[nm]

    # @property
    # def groups(self,):
    # if not hasattr(self,'__data_groups__'):
    # self.__data_groups__=groups({'main':oset(['config_type']),})
    # return self.__data_groups__

    def __repr__(self,):
        return self.__repr_level__(0)

    def __repr_level__(self, level=0):
        string = level * (self._lvl_spaces) * ' ' + '%s Configuration:\n' % self.config_type
        for nm, dt in self.iteritems():
            if nm in ['system', 'config_type']:
                pass
            elif config in dt.__class__.__mro__:
                string += dt.__repr_level__(level + 1) + ' \n'
            else:
                string += (level + 1) * self._lvl_spaces * \
                    ' ' + '%s = %s,\n' % (nm, dt)
        return string[:-2]

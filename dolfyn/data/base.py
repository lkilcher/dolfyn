from ..meta import api_dumb as ma
import numpy as np
from pyDictH5.base import data as SourceDataType
import six
import copy

rad_hz = ma.marray(2 * np.pi, ma.varMeta('', {'s': -1, 'hz': -1}))


def indent(text, padding='    '):
    return ''.join(padding + line for line in text.splitlines(True))


def _format_repr(dat, level=0, show_all=False, skip=[]):
    s_ky = ''
    s_grp = ''
    for ky in sorted(dat.keys()):
        if ky.startswith('_') and not show_all:
            continue
        if ky in skip:
            continue
        if isinstance(dat[ky], dict):
            if level > 0:
                s_grp += ' > + {: <23}: {}\n'.format(ky, '+ DATA GROUP')
                s_grp += indent(_format_repr(dat[ky], level - 1), '  ')
            else:
                s_grp += ' + {: <25}: {}\n'.format(ky, '+ DATA GROUP')
        else:
            val = dat[ky]
            sval = str(type(val))
            if type(val) is np.ndarray:
                sval = '<array; {}; {}>'.format(val.shape,
                                                val.dtype)
            elif isinstance(val, np.ndarray):
                sval = '<{}; {}; {}>'.format(
                    str(type(val))
                    .rsplit('.')[-1].rstrip("'>"),
                    val.shape,
                    val.dtype)
            s_ky += ' | {: <25}: {}\n'.format(ky, sval)
    s = s_ky + s_grp
    return s


def _format_repr_config(dat, level=0, show_all=False, skip=[]):
    s_ky = ''
    s_grp = ''
    for ky in sorted(dat.keys()):
        if ky.startswith('_') and not show_all:
            continue
        if ky in skip:
            continue
        if isinstance(dat[ky], dict):
            if level > 0:
                s_grp += ' > + {}\n'.format(ky)
                s_grp += indent(_format_repr_config(dat[ky], level - 1), '  ')
            else:
                s_grp += ' + {}\n'.format(ky)
        else:
            val = dat[ky]
            if isinstance(dat[ky], six.string_types):
                if len(dat[ky]) > 30:
                    val = str(type(dat[ky]))
            else:
                try:
                    len(dat[ky])
                except TypeError:
                    pass
                else:
                    val = str(type(dat[ky]))
            s_ky += ' | {: <25}: {}\n'.format(ky, val)
    s = s_ky + s_grp
    return s


class data(SourceDataType):
    """
    This is just an abstract class so that we directly import the
    SourceDataType in one place.
    """

    @property
    def shortcuts(self, ):
        return [p for p in dir(type(self)) if isinstance(getattr(type(self), p), property)
                and not p.startswith('_') and not p == 'shortcuts']

    @property
    def _repr_header(self, ):
        return (
            '{}: Data Object with Keys:\n'
        ).format(self.__class__)

    def __repr__(self,):
        return (self._repr_header +
                '  *------------\n' +
                indent(_format_repr(self), ' '))


class TimeData(data):
    """
    This is a base class that contains arrays where time is the last
    dimension.
    """
    _time_dim = -1
    _subset_copy_vars = ['range', 'range_b5']

    def _subset(self, indx, raise_on_empty_array=True, copy=[]):
        if not isinstance(indx, tuple):
            indx = (Ellipsis, indx)
        return SourceDataType._subset(self, indx,
                                      raise_on_empty_array=raise_on_empty_array,
                                      copy=copy + self._subset_copy_vars)

    def append(self, other):
        """Join two data objects together.

        For example, two data objects ``d1`` and ``d2`` (which must
        contain the same variables, with the same array dimensions)
        can be joined together by::

            >>> dat = d1.append(d2)

        """
        join_ax = self._time_dim
        shapes = {}
        for ky in self._subset_copy_vars:
            if ky in self:
                shapes[ky] = self[ky].shape[join_ax]
        data.append(self, other, array_axis=join_ax)
        for ky in self._subset_copy_vars:
            if ky in self:
                self[ky] = self[ky][..., :shapes[ky]]


class MappedTime(TimeData):

    def _subset(self, indx, raise_on_empty_array=True, copy=[]):
        if not isinstance(indx, tuple):
            indx = [Ellipsis, indx]
        else:
            indx = list(indx)
        N = self.pop('_map_N')
        parent_map = np.arange(N)[indx[-1]]
        indx[-1] = np.in1d(self['_map'], parent_map)
        out = TimeData._subset(self, tuple(indx),
                               raise_on_empty_array=False, copy=copy)
        self['_map_N'] = N
        out['_map_N'] = len(parent_map)
        out['_map'] -= parent_map[0]
        return out

    def append(self, other):
        """Join two data objects together.

        For example, two data objects ``d1`` and ``d2`` (which must
        contain the same variables, with the same array dimensions)
        can be joined together by::

            >>> dat = d1.append(d2)

        """
        Ns = self.pop('_map_N')
        No = other.pop('_map_N')
        self['_map'] = np.hstack((self['_map'], other['_map'] + Ns))
        self['_map_N'] = Ns + No
        other['_map_N'] = No


class FreqData(TimeData):
    """
    This is a base class that contains arrays where frequency is the
    last dimension, and time is the second to last dimension.
    """
    _time_dim = -2
    _subset_copy_vars = ['omega', 'freq']

    def _subset(self, indx, raise_on_empty_array=True, copy=[]):
        if not isinstance(indx, tuple):
            indx = (Ellipsis, indx, slice(None))
        return SourceDataType._subset(self, indx,
                                      raise_on_empty_array=raise_on_empty_array,
                                      copy=copy + self._subset_copy_vars)


class config(data):

    @property
    def _repr_header(self, ):
        return (
            '{} Configuration:\n'
        ).format(self._type)

    def __repr__(self,):
        return (self._repr_header +
                '  *------------\n' +
                indent(_format_repr_config(self, level=2), ' '))

    def _subset(self, indx, **kwargs):
        # Don't subset config objects.
        return copy.deepcopy(self)

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

    def _subset(self, indx):
        if not isinstance(indx, tuple):
            indx = (Ellipsis, indx)
        return SourceDataType._subset(self, indx,
                                      raise_on_empty_array=True)


class FreqData(TimeData):
    """
    This is a base class that contains arrays where frequency is the
    last dimension, and time is the second to last dimension.
    """
    _time_dim = -2

    def _subset(self, indx):
        if not isinstance(indx, tuple):
            indx = (Ellipsis, indx, slice(None))
        return SourceDataType._subset(self, indx,
                                      raise_on_empty_array=True,
                                      copy=['omega', 'freq'])


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

    def _subset(self, indx):
        # Don't subset config objects.
        return copy.deepcopy(self)

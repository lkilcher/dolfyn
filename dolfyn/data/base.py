from ..meta import api_dumb as ma
import numpy as np
from pyDictH5.base import data as SourceDataType
import six

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
                s_grp += ' > + {}\n'.format(ky)
                s_grp += indent(_format_repr(dat[ky], level - 1), '  ')
            else:
                s_grp += ' + {}\n'.format(ky)
        else:
            s_ky += ' | {}\n'.format(ky)
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

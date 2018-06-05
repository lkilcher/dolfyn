"""
Holds the primary high-level interfaces for the io (read/write)
package.
"""
import sys
import inspect
from ..data import base as db
from . import hdf5
from . import mat


def load(*args, **kwargs):
    dat = hdf5.load(*args, **kwargs)
    for old, new in [
            ('orient.Accel', 'orient.accel'),
            ('orient.AngRt', 'orient.angrt'),
            ('orient.Mag', 'orient.mag'),
            ('altraw.orient.Accel', 'altraw.orient.accel'),
            ('altraw.orient.AngRt', 'altraw.orient.angrt'),
            ('altraw.orient.Mag', 'altraw.orient.mag'),
            ('orient.Accel_b5', 'orient.accel_b5'),
            ('orient.AngRt_b5', 'orient.angrt_b5'),
            ('orient.Mag_b5', 'orient.mag_b5'),
            ('orient.AccelStable', 'orient.acclow'),
            ('sys.BIT', 'sys.bit'),
    ]:
        if old in dat:
            dat[new] = dat.pop(old)
        if 'rotate_vars' in dat.props:
            rvars = dat.props['rotate_vars']
            if old in rvars:
                rvars.add(new)
                rvars.remove(old)
    return dat

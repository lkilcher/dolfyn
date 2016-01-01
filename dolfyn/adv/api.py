"""
This module contains routines for reading and working with adv
data. It contains:

+-----------------------------------+-----------------------------------------+
| Name                              | Description                             |
+===================================+=========================================+
| :func:`~dolfyn.adv.base.load`     | A function for loading ADV data in      |
|                                   | DOLfYN format.                          |
+-----------------------------------+-----------------------------------------+
| :func:`~dolfyn.adv.base.mmload`   | A function for loading ADV data in      |
|                                   | DOLfYN format (as memory mapped arrays).|
+-----------------------------------+-----------------------------------------+
| :func:`~dolfyn.io.nortek.\        | A function for reading Nortek Vector    |
| read_nortek`                      | files.                                  |
+-----------------------------------+-----------------------------------------+
| :mod:`rotate <dolfyn.adv.rotate>` | A module containing classes and         |
|                                   | functions for rotating adv data between |
|                                   | different coordinate systems            |
+-----------------------------------+-----------------------------------------+
| :mod:`motion <dolfyn.adv.rotate>` | A module containing classes and         |
|                                   | functions for performing motion         |
|                                   | correction.                             |
+-----------------------------------+-----------------------------------------+
|  :class:`~dolfyn.\                | A class for breaking ADV data into      |
|  adv.turbulence.TurbBinner`       | 'bins', averaging it and estimating     |
|                                   | various turbulence statistics.          |
+-----------------------------------+-----------------------------------------+

Examples
--------

.. literalinclude:: ../examples/adv_example01.py

"""


from .base import load, mmload
from .turbulence import calc_turbulence, TurbBinner
from . import clean
from ..io.nortek import read_nortek
from . import rotate
from . import motion

# pylint: disable=anomalous-backslash-in-string
"""
This module contains routines for reading and working with adv
data. It contains:

+-----------------------------------+-----------------------------------------+
| Name                              | Description                             |
+===================================+=========================================+
| :func:`~dolfyn.adv.base.load`     | A function for loading ADV data in      |
|                                   | DOLfYN format.                          |
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


from .turbulence import calc_turbulence, TurbBinner
from . import clean
from ..rotate import vector as rotate
from . import motion
from ..io.api import read, load

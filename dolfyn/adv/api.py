# pylint: disable=anomalous-backslash-in-string
"""
This module contains routines for reading and working with ADV
data. It contains:

+-----------------------------------+-----------------------------------------+
| Name                              | Description                             |
+===================================+=========================================+
| :func:`load <dolfyn.io.api.load>` | A function for loading DOLfYN's h5 data |
|                                   | files.                                  |
+-----------------------------------+-----------------------------------------+
| :func:`read <dolfyn.io.api.read>` | A function for reading Nortek Vector    |
|                                   | files.                                  |
+-----------------------------------+-----------------------------------------+
| :func:`rotate2 <dolfyn.rotate.\   | A function for rotating data            |
| .rotate2>`                        | between different coordinate systems    |
+-----------------------------------+-----------------------------------------+
| :mod:`clean <dolfyn.adv.clean>`   | A module containing functions for       |
|                                   | cleaning data, filling NaN's,           |
|                                   | different coordinate systems            |
+-----------------------------------+-----------------------------------------+
| :mod:`motion <dolfyn.adv.motion>` | A module containing classes and         |
|                                   | functions for performing motion         |
|                                   | correction.                             |
+-----------------------------------+-----------------------------------------+
| :class:`~dolfyn.adv.\             | A class for breaking ADV data into      |
| turbulence.TurbBinner`            | 'bins', averaging it and calculating    |
|                                   | various turbulence statistics           |
+-----------------------------------+-----------------------------------------+
| :func:`~dolfyn.adv.\              | Functional version of TurbBinner        |
| turbulence.calc_turbulence`       |                                         |
+-----------------------------------+-----------------------------------------+


Examples
--------

.. literalinclude:: ../examples/adv_example01.py

"""

from ..io.api import read, load
from ..rotate import rotate2
from . import clean
from . import motion
from .turbulence import calc_turbulence, TurbBinner

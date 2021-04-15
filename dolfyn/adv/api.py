# pylint: disable=anomalous-backslash-in-string
"""
This module contains routines for reading and working with ADV
data. It contains:

+-----------------------------------+-----------------------------------------+
| Name                              | Description                             |
+===================================+=========================================+
| :func:`read <dolfyn.io.api.read>` | A function for reading Nortek Vector    |
|                                   | files.                                  |
+-----------------------------------+-----------------------------------------+
| :func:`load <dolfyn.io.api.load>` | A function for loading DOLfYN's h5 data |
|                                   | files.                                  |
+-----------------------------------+-----------------------------------------+
| :func:`rotate2 <dolfyn.rotate.\   | A function for rotating data            |
| .main.rotate2>`                   | between different coordinate systems    |
+-----------------------------------+-----------------------------------------+
| :mod:`clean <dolfyn.adv.clean>`   | A module containing functions for       |
|                                   | cleaning, "despiking" and filling       |
|                                   | NaN's in data                           |
+-----------------------------------+-----------------------------------------+
| :mod:`motion <dolfyn.adv.motion>` | A module containing classes and         |
|                                   | functions for performing motion         |
|                                   | correction.                             |
+-----------------------------------+-----------------------------------------+
| :class:`VelBinner <dolfyn.data.\  | A class for breaking data into          |
| velocity.VelBinner>`              | 'bins'/'ensembles', averaging it and    |
|                                   | estimating basic turbulence statistics. |
+-----------------------------------+-----------------------------------------+
| :class:`~dolfyn.adv.\             | A class that builds upon `VelBinner`    |
| turbulence.TurbBinner`            | for calculating statistics from spectra |
+-----------------------------------+-----------------------------------------+
| :func:`~dolfyn.adv.\              | Functional version of `TurbBinner`      |
| turbulence.calc_turbulence`       |                                         |
+-----------------------------------+-----------------------------------------+


Examples
--------

.. literalinclude:: ../examples/adv_example01.py

"""

from ..io.api import read, load
from ..rotate.main import rotate2
from . import x_clean
from .x_motion import correct_motion
from .x_turbulence import calc_turbulence, TurbBinner

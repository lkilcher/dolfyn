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
| :func:`load <dolfyn.io.api.load>` | A function for loading xarray-saved     |
|                                   | netCDF files.                           |
+-----------------------------------+-----------------------------------------+
| :func:`rotate2 <dolfyn.rotate.\   | A function for rotating data            |
| main.rotate2>`                    | between different coordinate systems    |
+-----------------------------------+-----------------------------------------+
| :mod:`clean <dolfyn.adv.clean>`   | A module containing functions for       |
|                                   | cleaning, "despiking" and filling       |
|                                   | NaN's in data                           |
+-----------------------------------+-----------------------------------------+
| :func:`set_inst2head_rotmat       | A function for setting inst2head        |
| <dolfyn.rotate.base.\             | rotation matrix for motion-correction   |
| set_inst2head_rotmat>`            | if not set in userdata.json file        |
+-----------------------------------+-----------------------------------------+
| :func:`correct_motion <dolfyn.\   | A function for performing motion        |
| adv.motion.correct_motion>`       | correction on ADV velocity data         |
+-----------------------------------+-----------------------------------------+
| :class:`VelBinner <dolfyn.data.\  | A class for breaking data into          |
| velocity.VelBinner>`              | 'bins' or 'ensembles', averaging it and |
|                                   | estimating basic turbulence statistics  |
+-----------------------------------+-----------------------------------------+
| :class:`~dolfyn.adv.\             | A class that builds upon `VelBinner`    |
| turbulence.TurbBinner`            | for calculating turbulence statistics   |
|                                   | and velocity spectra                    |
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
from ..rotate.base import set_inst2head_rotmat
from . import clean
from .motion import correct_motion
from .turbulence import calc_turbulence, TurbBinner

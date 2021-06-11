# pylint: disable=anomalous-backslash-in-string
"""
This module contains routines for reading and working with ADP/ADCP
data. It contains:

+-----------------------------------+-----------------------------------------+
| Name                              | Description                             |
+===================================+=========================================+
| :func:`read <dolfyn.io.api.read>` | A function for reading ADCP files       |
+-----------------------------------+-----------------------------------------+
| :func:`load <dolfyn.io.api.load>` | A function for loading xarray-saved     |
|                                   | netCDF files.                           |
+-----------------------------------+-----------------------------------------+
| :func:`rotate2 <dolfyn.rotate.\   | A function for rotating data            |
| .api.rotate2>`                    | between different coordinate systems    |
+-----------------------------------+-----------------------------------------+
| :mod:`clean <dolfyn.adp.clean>`   | A module containing functions for       |
|                                   | cleaning data, filling NaN's,           |
|                                   | different coordinate systems            |
+-----------------------------------+-----------------------------------------+
| :class:`VelBinner <dolfyn.\       | A class that breaks data into           |
| velocity.VelBinner>`              | 'bins'/'ensembles' and contains         |
|                                   | analysis functions                      |
+-----------------------------------+-----------------------------------------+

Examples
--------

.. literalinclude:: ../../examples/adcp_example.py

"""

from ..io.api import read, load
from ..rotate.api import rotate2
from . import clean
from ..velocity import VelBinner
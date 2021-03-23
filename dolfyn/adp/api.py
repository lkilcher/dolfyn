# pylint: disable=anomalous-backslash-in-string
"""
This module contains routines for reading and working with ADP/ADCP
data. It contains:

+-----------------------------------+-----------------------------------------+
| Name                              | Description                             |
+===================================+=========================================+
| :func:`load <dolfyn.io.api.load>` | A function for loading DOLfYN's h5 data |
|                                   | files.                                  |
+-----------------------------------+-----------------------------------------+
| :func:`read <dolfyn.io.api.read>` | A function for reading files            |
+-----------------------------------+-----------------------------------------+
| :func:`rotate2 <dolfyn.rotate.\   | A function for rotating data            |
| .rotate2>`                        | between different coordinate systems    |
+-----------------------------------+-----------------------------------------+
| :mod:`clean <dolfyn.adp.clean>`   | A module containing functions for       |
|                                   | cleaning data, filling NaN's,           |
|                                   | different coordinate systems            |
+-----------------------------------+-----------------------------------------+
| :class:`VelBinner <dolfyn.data.\  | A class for breaking data into          |
| velocity.VelBinner>`              | 'bins', averaging it and estimating     |
|                                   | basic turbulence statistics.            |
+-----------------------------------+-----------------------------------------+

Examples
--------

.. literalinclude:: ../examples/adcp_example01.py

"""

from ..io.api import read, load
from ..rotate import rotate2
from . import clean
from ..data.velocity import VelBinner

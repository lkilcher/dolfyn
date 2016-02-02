from ..meta import api_dumb as ma
import numpy as np
from pycoda.base import PropData, data

rad_hz = ma.marray(2 * np.pi, ma.varMeta('', {'s': -1, 'hz': -1}))


class config(PropData):
    pass


class SpecData(data):
    """
    A class for storing spectral data.

    The last dimension of all data in this class should be frequency.
    """
    
    pass

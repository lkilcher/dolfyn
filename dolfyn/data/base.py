from ..meta import api_dumb as ma
import numpy as np
from pyDictH5.base import data


rad_hz = ma.marray(2 * np.pi, ma.varMeta('', {'s': -1, 'hz': -1}))


class config(data):
    pass

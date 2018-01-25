from ..meta import api_dumb as ma
import numpy as np
from pyDictH5.base import data as SourceDataType


rad_hz = ma.marray(2 * np.pi, ma.varMeta('', {'s': -1, 'hz': -1}))


class data(SourceDataType):
    """
    This is just an abstract class so that we directly import the
    SourceDataType in one place.
    """
    pass


class config(data):
    pass

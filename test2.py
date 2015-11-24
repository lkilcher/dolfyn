import pycoda.base as pc
import numpy as np
reload(pc)

a = pc.marray([10, 20, 30], meta={'units': 'm/s'})
b = np.array([1, 5, 10])
c = a + b
d = b + a

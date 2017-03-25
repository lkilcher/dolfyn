import numpy as np
from six import string_types


class bitstring(object):

    def __init__(self, width):
        self.form = '{:0%db}' % width

    def __call__(self, val):
        return self.form.format(val)

bs8 = bitstring(8)
bs16 = bitstring(16)
bs32 = bitstring(32)


class i2ba(object):
    """int 2 binarray"""

    def __init__(self, width):
        self._masks = 2 ** np.arange(width)[::-1]

    def __call__(self, val):
        return (val & self._masks).astype('bool')

i8ba = i2ba(8)
i16ba = i2ba(16)
i32ba = i2ba(32)


# class parsebits(i2ba):

#     def __init__(self, ):
#         m = []
#         for a in masks:
#             if isinstance(a, string_types):
#                 m.append(int(a, 2))
#             else:
#                 m.append(a)
#         self._masks = m

#     def __call__(self, val):
#         return (val & self._masks).astype('bool')

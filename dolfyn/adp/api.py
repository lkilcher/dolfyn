from .base import type_map, dio, binner
from ..io.rdi import read_rdi
from ..io.nortek import read_nortek
from ..io.nortek2 import read_signature
from .rotate import beam2inst, inst2earth, earth2principal
from ..io.nortek import read_nortek


def load(fname, data_groups=None):
    with dio.loader(fname, type_map) as ldr:
        return ldr.load(data_groups)


def mmload(fname, data_groups=None):
    with dio.loader(fname, type_map) as ldr:
        return ldr.mmload(data_groups)

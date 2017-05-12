from .base import type_map, dio, binner
from ._readbin import adcp_loader
from .rotate import beam2inst, inst2earth, earth2principal


def load(fname, data_groups=None):
    with dio.loader(fname, type_map) as ldr:
        return ldr.load(data_groups)


def mmload(fname, data_groups=None):
    with dio.loader(fname, type_map) as ldr:
        return ldr.mmload(data_groups)


def read_rdi(fname, nens=None):
    with adcp_loader(fname) as ldr:
        dat = ldr.load_data(nens=nens)
    return dat

from base import type_map, dio
from _readbin import adcp_loader

def load(fname, data_groups=None):
    with dio.loader(fname, type_map) as ldr:
        return ldr.load(data_groups)


def mmload(fname, data_groups=None):
    with dio.loader(fname, type_map) as ldr:
        return ldr.mmload(data_groups)


def read_rdi(fname):
    with adcp_loader(fname) as ldr:
        dat = ldr.load_data()
    return dat

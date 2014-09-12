from base import type_map, dio


def load(fname, data_groups=None):
    with dio.loader(fname, type_map) as ldr:
        return ldr.load(data_groups)


def mmload(fname, data_groups=None):
    with dio.loader(fname, type_map) as ldr:
        return ldr.mmload(data_groups)

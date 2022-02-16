import dolfyn.io.api as io
from dolfyn import time
from xarray.testing import assert_allclose as _assert_allclose
import numpy as np
import pkg_resources
import atexit


atexit.register(pkg_resources.cleanup_resources)


def assert_allclose(dat0, dat1, *args, **kwargs):
    names = []
    # Time checking
    # for v in dat0.variables:
    #     if np.issubdtype(dat0[v].dtype, np.datetime64):
    #         dat0[v] = time.dt642epoch(dat0[v])
    #         dat1[v] = time.dt642epoch(dat1[v])
    #         names.append(v)
    # Check coords and data_vars
    _assert_allclose(dat0, dat1, *args, **kwargs)
    # Check attributes
    assert dat0.attrs == dat1.attrs, "The attributes do not match."
    # Revert time back
    # for v in names:
    #     dat0[v] = time.epoch2dt64(dat0[v])
    #     dat1[v] = time.epoch2dt64(dat1[v])


def drop_config(dataset):
    # Can't save configuration string in netcdf
    for key in list(dataset.attrs.keys()):
        if 'config' in key:
            dataset.attrs.pop(key)
    return dataset


class ResourceFilename(object):

    def __init__(self, package_or_requirement, prefix=''):
        self.pkg = package_or_requirement
        self.prefix = prefix

    def __call__(self, name):
        return pkg_resources.resource_filename(self.pkg, self.prefix + name)


rfnm = ResourceFilename('dolfyn.tests', prefix='data/')
exdt = ResourceFilename('dolfyn', prefix='example_data/')


def load_ncdata(name, *args, **kwargs):
    return io.load(rfnm(name), *args, **kwargs)


def save_ncdata(data, name, *args, **kwargs):
    io.save(data, rfnm(name), *args, **kwargs)


def load_matlab(name,  *args, **kwargs):
    return io.load_mat(rfnm(name), *args, **kwargs)


def save_matlab(data, name,  *args, **kwargs):
    io.save_mat(data, rfnm(name), *args, **kwargs)

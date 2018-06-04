import pkg_resources
import atexit
import pyDictH5.base as pb
from dolfyn.io.hdf5 import load as _load
import numpy as np

pb.debug_level = 10

atexit.register(pkg_resources.cleanup_resources)


def rungen(gen):
    for g in gen:
        pass


def data_equiv(dat1, dat2, message=''):
    assert dat1 == dat2, message


def assert_close(dat1, dat2, message='', *args):
    assert np.allclose(dat1, dat2, *args), message


class ResourceFilename(object):

    def __init__(self, package_or_requirement, prefix=''):
        self.pkg = package_or_requirement
        self.prefix = prefix

    def __call__(self, name):
        return pkg_resources.resource_filename(self.pkg, self.prefix + name)


rfnm = ResourceFilename('dolfyn.test', prefix='data/')
exdt = ResourceFilename('dolfyn', prefix='example_data/')


def load_tdata(name, *args, **kwargs):
    return _load(rfnm(name), *args, **kwargs)


def save_tdata(data, name, *args, **kwargs):
    data.to_hdf5(rfnm(name), *args, **kwargs)

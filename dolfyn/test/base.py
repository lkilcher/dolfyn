import pkg_resources
import atexit
import pyDictH5.base as pb
from dolfyn import load, save
from dolfyn.h5.io.hdf5 import load as load_h5

pb.debug_level = 10

atexit.register(pkg_resources.cleanup_resources)

# Modernize testing
# def rungen(gen):
#     for g in gen:
#         pass

# def data_equiv(dat1, dat2, message=''):
#     assert dat1 == dat2, message

# def assert_close(dat1, dat2, message='', *args):
#     assert np.allclose(dat1, dat2, *args), message


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


rfnm = ResourceFilename('dolfyn.test', prefix='data/')
exdt = ResourceFilename('dolfyn', prefix='example_data/')


def load_ncdata(name, *args, **kwargs):
    return load(rfnm(name), *args, **kwargs)


def save_ncdata(data, name, *args, **kwargs):
    save(data, rfnm(name), *args, **kwargs)


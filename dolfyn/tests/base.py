import pkg_resources
import atexit
import dolfyn.io.api as io

atexit.register(pkg_resources.cleanup_resources)


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

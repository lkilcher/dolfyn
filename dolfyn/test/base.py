import pkg_resources
import atexit
import pyDictH5.base as pb

pb.debug_level = 10

atexit.register(pkg_resources.cleanup_resources)


def rungen(gen):
    for g in gen:
        pass


class ResourceFilename(object):

    def __init__(self, package_or_requirement):
        self.pkg = package_or_requirement

    def __call__(self, name):
        return pkg_resources.resource_filename(self.pkg, name)

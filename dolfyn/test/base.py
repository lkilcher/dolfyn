import pkg_resources
import atexit

atexit.register(pkg_resources.cleanup_resources)


class ResourceFilename(object):

    def __init__(self, package_or_requirement):
        self.pkg = package_or_requirement

    def __call__(self, name):
        return pkg_resources.resource_filename(self.pkg, name)

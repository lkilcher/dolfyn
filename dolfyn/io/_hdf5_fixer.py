"""
This module is used to fix data files when the format specification
changes.
"""


import h5py as h5
try:
    import cPickle as pkl
except:
    import pickle as pkl
from .base import DataFactory


class UpdateTool(DataFactory):

    """
    A class for updating data files when the format specification
    changes.
    """

    def __init__(self, filename, ):
        self.file_mode = 'a'
        # This does an 'expanduser' on the filename (i.e. '~/'
        # replaced with '/home/<username>/').
        self.filename = filename
        kwargs = {}
        self.fd = h5.File(self.filename, mode=self.file_mode, **kwargs)
        self.close = self.fd.close
        self.node = self.fd.get('/')
        self.node.attrs.create('DataSaveVersion', pkl.dumps(self.ver))
        self._extrafiles = []

    def change_type_name(self, oldname, newname):
        self.getGroup('/').attrs.create('_object_type',
                                        newname)

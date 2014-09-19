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
import numpy as np


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
        self._extrafiles = []

    def set_type(self, newname):
        self.fd.attrs['_object_type'] = newname

    def change_name(self, where, oldname, newname):
        """
        Change the name of the attribute at location `where`/`oldname`
        to `where`/`newname`.
        """
        if oldname in self.fd[where].keys():
            self.fd[where].move(oldname, newname)
        else:
            print('%s not found at %s' % (oldname, where))

    def join_and_move(self, where, oldnames, newname):
        """
        Concatenate the data in oldnames along (a new) dimension 0,
        and save them as newname.
        """
        if oldnames[0] in self.fd[where].keys():
            nd = self.fd[where][oldnames[0]]
            dat = np.empty([len(oldnames)] + list(nd.shape), dtype=nd.dtype)
            for idx, nm in enumerate(oldnames):
                nd = self.fd[where][nm]
                nd.read_direct(dat[idx])
                del nd
                self.fd[where].create_dataset(newname, data=dat)
            else:
                print('%s not found at %s' % (oldnames[0], where))

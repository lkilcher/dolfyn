import pkg_resources
import atexit
import pyDictH5.base as pb
from dolfyn import load, save
from dolfyn.h5.io.hdf5 import load as load_h5
import numpy as np
import scipy.io as sio

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
    save(rfnm(name), *args, **kwargs)


def load_nortek_matfile(filename):
    # remember to transpose this data
    data = sio.loadmat(filename, 
                       struct_as_record=False, 
                       squeeze_me=True)
    d = data['Data']
    #print(d._fieldnames)
    burst = 'Burst'
    bt = 'BottomTrack'
    
    beam = ['_VelBeam1','_VelBeam2','_VelBeam3','_VelBeam4']
    b5 = 'IBurst_VelBeam5'
    inst = ['_VelX','_VelY','_VelZ1','_VelZ2']
    earth = ['_VelEast','_VelNorth','_VelUp1','_VelUp2']
    axis = {'beam':beam, 'inst':inst, 'earth':earth}
    
    vel = {'beam':{},'inst':{},'earth':{}}
    for ky in vel.keys():
        for i in range(len(axis[ky])):
            vel[ky][i] = np.transpose(getattr(d, burst+axis[ky][i]))
        vel[ky] = np.stack((vel[ky][0], vel[ky][1], 
                            vel[ky][2], vel[ky][3]), axis=0)
    
    if b5 in d._fieldnames:
        vel['b5'] = getattr(d, b5)
        
    if bt+beam[0] in d._fieldnames:
        vel_bt = {'beam':{},'inst':{},'earth':{}}
        for ky in vel_bt.keys():
            for i in range(len(axis[ky])):
                vel_bt[ky][i] = np.transpose(getattr(d, bt+axis[ky][i]))
            vel_bt[ky] = np.stack((vel_bt[ky][0], vel_bt[ky][1], 
                                   vel_bt[ky][2], vel_bt[ky][3]), axis=0)
    
        return vel, vel_bt
    else:
        return vel

"""
The base module for the io package.
"""

import numpy as np
import xarray as xr
from ..data import time
import six
import json
import io
import os
import warnings

try:
    file_types = (file, io.IOBase)
except NameError:
    file_types = io.IOBase
    
    
class WrongFileType(Exception):
    pass


def read_userdata(filename, userdata=True):
    """
    Reads a userdata.json file and returns the data it contains as a
    dictionary.
    """
    # This function finds the file to read
    if userdata is True:
        for basefile in [filename.rsplit('.', 1)[0],
                         filename]:
            jsonfile = basefile + '.userdata.json'
            if os.path.isfile(jsonfile):
                return _read_userdata(jsonfile)

    elif isinstance(userdata, (six.string_types)) or hasattr(userdata, 'read'):
        return _read_userdata(userdata)
    return {}


def _read_userdata(fname):
    # This one actually does the read
    if isinstance(fname, file_types):
        data = json.load(fname)
    else:
        with open(fname) as data_file:
            data = json.load(data_file)
    for nm in ['body2head_rotmat', 'body2head_vec']:
        if nm in data:
            new_name = 'inst' + nm[4:]
            warnings.warn(
                '{} has been deprecated, please change this to {} in {}.'
                .format(nm, new_name, fname))
            data[new_name] = data.pop(nm)
    if 'inst2head_rotmat' in data and \
       data['inst2head_rotmat'] in ['identity', 'eye', 1, 1.]:
        data['inst2head_rotmat'] = np.eye(3)
    for nm in ['inst2head_rotmat', 'inst2head_vec']:
        if nm in data:
            data[nm] = np.array(data[nm])
    if 'time_range' in data:
        if isinstance(data['time_range'][0], six.string_types):
            data['time_range'] = time.isotime2mpltime(data['time_range'])
    if 'coord_sys' in data:
        raise Exception("The instrument coordinate system "
                        "('coord_sys') should not be specified in "
                        "the .userdata.json file, remove this and "
                        "read the file again.")
    return data


def handle_nan(data):
    '''
    Hunting down nan's and eliminating them.
    
    '''
    nan = np.zeros(data['coords']['time'].shape, dtype=bool)
    l = data['coords']['time'].size
    
    if any(np.isnan(data['coords']['time'])):
        nan += np.isnan(data['coords']['time'])
    
    var = ['heading', 'pitch', 'roll', 'accel', 'angrt', 'mag']
    for key in data['data_vars']:
        if any(val in key for val in var):
            shp = data['data_vars'][key].shape
            if shp[-1]==l:
                if len(shp)==1:
                    if any(np.isnan(data['data_vars'][key])):
                        nan += np.isnan(data['data_vars'][key])
                elif len(shp)==2:
                    if any(np.isnan(data['data_vars'][key][-1])):
                        nan += np.isnan(data['data_vars'][key][-1])

    if nan.sum()>0:
        data['coords']['time'] = data['coords']['time'][~nan]
        for key in data['data_vars']:
            if data['data_vars'][key].shape[-1]==l:
                data['data_vars'][key] = data['data_vars'][key][...,~nan]


def create_dataset(data):
    '''
    Creates an xarray dataset from dictionary created from binary datafile 
    readers
    
    '''
    ds = xr.Dataset()
    Time = data['coords']['time']
    beam = list(range(1,data['data_vars']['vel'].shape[0]+1))
    # orient coordinates get reset in _set_coords()
    for key in data['data_vars']:
        # orientation matrices
        if 'mat' in key:
            try: # orientmat
                ds[key] = xr.DataArray(data['data_vars'][key],
                                       coords={'inst':['X','Y','Z'],
                                               'earth':['E','N','U'], 
                                               'time':Time},
                                       dims=['inst','earth','time'])
            except: # the other 2
                ds[key] = xr.DataArray(data['data_vars'][key],
                                       coords={'x':beam,
                                               'x*':beam},
                                       dims=['x','x*'])
        # quaternion units never change
        elif 'quat' in key: 
            ds[key] = xr.DataArray(data['data_vars'][key],
                                   coords={'q':[1,2,3,4],
                                           'time':Time},
                                   dims=['q','time'])
        # the rest of the madness
        else:
            ds[key] = xr.DataArray(data['data_vars'][key])
            try: # not all variables have units
                ds[key].attrs['units'] = data['units'][key]
            except:
                pass
            
            shp = data['data_vars'][key].shape
            vshp = data['data_vars']['vel'].shape
            l = len(shp)
            if l==1: # 1D variables
                ds[key] = ds[key].rename({'dim_0':'time'})
                ds[key] = ds[key].assign_coords({'time':Time})

            elif l==2: # 2D variables
                if key=='echo':
                    ds[key] = ds[key].rename({'dim_0':'range_echo',
                                              'dim_1':'time'})
                    ds[key] = ds[key].assign_coords({'range_echo':data['coords']['range_echo'],
                                                     'time':Time})
                # 3- & 4-beam instrument data, bottom tracking
                elif shp[0]==vshp[0]: 
                    ds[key] = ds[key].rename({'dim_0':'orient',
                                              'dim_1':'time'})
                    ds[key] = ds[key].assign_coords({'orient':beam,
                                                     'time':Time})
                # 4-beam instrument IMU data
                elif shp[0]==vshp[0]-1:
                    ds[key] = ds[key].rename({'dim_0':'orientIMU',
                                              'dim_1':'time'})
                    ds[key] = ds[key].assign_coords({'orientIMU':[1,2,3],
                                                     'time':Time})
                else:
                    warnings.warn('Variable not included in dataset: {}'
                                  .format(key))

            elif l==3: # 3D variables
                dtype = ['b5']
                if not any(val in key for val in dtype):
                    ds[key] = ds[key].rename({'dim_0':'orient',
                                              'dim_1':'range',
                                              'dim_2':'time'})
                    ds[key] = ds[key].assign_coords({'orient':beam,
                                                     'range':data['coords']['range'],
                                                     'time':Time})
      
                elif 'b5' in key:
                    ds[key] = ds[key][0] # xarray can't handle coords of length 1
                    ds[key] = ds[key].rename({'dim_1':'range_b5',
                                              'dim_2':'time'})
                    ds[key] = ds[key].assign_coords({'range_b5':data['coords']['range_b5'],
                                                     'time':Time})
                else:
                    warnings.warn('Variable not included in dataset: {}'
                                  .format(key))
    ds.attrs = data['attrs']
    
    return ds
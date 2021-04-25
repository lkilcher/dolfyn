import scipy.io as sio
import xarray as xr
import pkg_resources

from .x_nortek import read_nortek
from .x_nortek2 import read_signature
from .x_rdi import read_rdi
from .x_base import create_dataset, WrongFileType as _WTF
#from .xarray_io import convert_xarray


def read(fname, userdata=True, nens=None):
    """Read a binary Nortek (e.g., .VEC, .wpr, .ad2cp, etc.) or RDI
    (.000, .PD0, etc.) data file.

    Parameters
    ----------
    filename : string
               Filename of Nortek file to read.

    userdata : True, False, or string of userdata.json filename
               (default ``True``) Whether to read the
               '<base-filename>.userdata.json' file.

    nens : None (default: read entire file), int, or
           2-element tuple (start, stop)
              Number of pings to read from the file

    Returns
    -------
    dat : :class:`<~dolfyn.data.velocity.Velocity>`
      A DOLfYN velocity data object.

    """
    # Loop over binary readers until we find one that works.
    for func in [read_nortek, read_signature, read_rdi]:
        try:
            dat = func(fname, userdata=userdata, nens=nens)
        except _WTF:
            continue
        else:
            #dat = convert_xarray(dat)
            return dat
    raise _WTF("Unable to find a suitable reader for "
               "file {}.".format(fname))


def read_example(name, **kwargs):
    """Read an example data file.

    Parameters
    ==========
    name : string
        Available files:

            AWAC_test01.wpr
            BenchFile01.ad2cp
            RDI_test01.000
            burst_mode01.VEC
            vector_data01.VEC
            vector_data_imu01.VEC
            winriver01.PD0
            winriver02.PD0

    Returns
    =======
    dat : ADV or ADP data object.

    """
    filename = pkg_resources.resource_filename(
        'dolfyn',
        'example_data/' + name)
    return read(filename, **kwargs)


def save(filename, dataset):
    """
    Save xarray dataset as netCDF (.nc).
    Drops 'config' lines.
    
    """
    for key in list(dataset.attrs.keys()):
        if 'config' in key:
            dataset.attrs.pop(key)
    
    dataset.to_netcdf(filename, 
                      format='NETCDF4', 
                      engine='h5netcdf', 
                      invalid_netcdf=True)
    

def load(filename):
    """
    Load xarray dataset from netCDF
    
    """
    return xr.load_dataset(filename)


def save_mat(filename, data):
    """
    Save xarray dataset as a MATLAB (.mat) file
    
    """
    matfile = {'vars':{},'coords':{},'config':{},'units':{}}
    for key in data.data_vars:
        matfile['vars'][key] = data[key].values
        if hasattr(data[key], 'units'):
            matfile['units'][key] = data[key].units
    for key in data.coords:
        matfile['coords'][key] = data[key].values
    matfile['config'] = data.attrs
    
    sio.savemat(filename, matfile)
    
    
# def load_mat(filename):
#     """
#     Load xarray dataset from MATLAB (.mat) file
#     
#     Converting to Matlab messes up dimensions somehow
#     """
#     data = sio.loadmat(filename, struct_as_record=False, squeeze_me=True)
    
#     ds_dict = {'vars':{},'coords':{},'config':{},'units':{}}
    
#     for nm in ds_dict:
#         key_list = data[nm]._fieldnames
#         for ky in key_list:
#             ds_dict[nm][ky] = getattr(data[nm], ky)
    
#     ds_dict['data_vars'] = ds_dict.pop('vars')
#     ds_dict['attrs'] = ds_dict.pop('config')
    
#     ds = create_dataset(ds_dict)
            
#     return ds
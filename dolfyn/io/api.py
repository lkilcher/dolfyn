import numpy as np
import scipy.io as sio
import xarray as xr
import pkg_resources
from .nortek import read_nortek
from .nortek2 import read_signature
from .rdi import read_rdi
from .base import _create_dataset, _get_filetype
from ..rotate.base import _set_coords
from ..time import date2matlab, matlab2date, date2dt64, dt642date


# time variables stored as data variables (as opposed to coordinates)
t_additional = ['hdwtime_gps', ]


def read(fname, userdata=True, nens=None):
    """Read a binary Nortek (e.g., .VEC, .wpr, .ad2cp, etc.) or RDI
    (.000, .PD0, .ENX, etc.) data file.

    Parameters
    ----------
    filename : string
        Filename of instrument file to read.
    userdata : True, False, or string of userdata.json filename (default ``True``) 
        Whether to read the '<base-filename>.userdata.json' file.
    nens : None (default: read entire file), int, or 2-element tuple (start, stop)
        Number of pings or ensembles to read from the file

    Returns
    -------
    ds : xarray.Dataset
        An xarray dataset from instrument datafile.

    """
    file_type = _get_filetype(fname)
    if file_type == '<GIT-LFS pointer>':
        raise IOError("File '{}' looks like a git-lfs pointer. You may need to "
                      "install and initialize git-lfs. See https://git-lfs.github.com"
                      " for details.".format(fname))
    elif file_type is None:
        raise IOError("File '{}' is not recognized as a file-type that is readable by "
                      "DOLfYN. If you think it should be readable, try using the "
                      "appropriate read function (`read_rdi`, `read_nortek`, or "
                      "`read_signature`) found in dolfyn.io.api.".format(fname))
    else:
        func_map = dict(RDI=read_rdi,
                        nortek=read_nortek,
                        signature=read_signature)
        func = func_map[file_type]
    return func(fname, userdata=userdata, nens=nens)


def read_example(name, **kwargs):
    """Read an ADCP or ADV datafile from the examples directory.

    Parameters
    ----------
    name : str
        A few available files:

            AWAC_test01.wpr
            BenchFile01.ad2cp
            RDI_test01.000
            burst_mode01.VEC
            vector_data01.VEC
            vector_data_imu01.VEC
            winriver01.PD0
            winriver02.PD0

    Returns
    -------
    ds : xarray.Dataset
        An xarray dataset from the binary instrument data.

    """
    filename = pkg_resources.resource_filename(
        'dolfyn',
        'example_data/' + name)
    return read(filename, **kwargs)


def save(dataset, filename,
         format='NETCDF4', engine='netcdf4',
         **kwargs):
    """Save xarray dataset as netCDF (.nc).

    Parameters
    ----------
    dataset : xarray.Dataset
    filename : str
        Filename and/or path with the '.nc' extension
    **kwargs : these are passed directly to :func:`xarray.Dataset.to_netcdf`.

    Notes
    -----
    Drops 'config' lines.

    Compresses all variables using zlib and complevel=1. Override this
    default behavior by including encoding=<dict-of-dicts> that specify
    compression options for each variable. e.g.::

       encoding=dict()
       for ky in dataset:
            encoding[ky] = dict(zlib=True, complevel=6)
    
    See the xarray.to_netcdf documentation for more details.

    """
    if '.' in filename:
        assert filename.endswith('nc'), 'File extension must be of the type nc'
    else:
        filename += '.nc'

    # Dropping the detailed configuration stats because netcdf can't save it
    for key in list(dataset.attrs.keys()):
        if 'config' in key:
            dataset.attrs.pop(key)

    # Handling complex values for netCDF4
    dataset.attrs['complex_vars'] = []
    for var in dataset.data_vars:
        if np.iscomplexobj(dataset[var]):
            dataset[var+'_real'] = dataset[var].real
            dataset[var+'_imag'] = dataset[var].imag

            dataset = dataset.drop_vars(var)
            dataset.attrs['complex_vars'].append(var)

    if 'encoding' not in kwargs:
        enc = kwargs['encoding'] = dict()
        for ky in dataset.variables:
            enc[ky] = dict(zlib=True, complevel=1)

    dataset.to_netcdf(filename, format=format, engine=engine, **kwargs)


def load(filename):
    """Load xarray dataset from netCDF (.nc)

    Parameters
    ----------
    filename : str
        Filename and/or path with the '.nc' extension

    Returns
    -------
    ds : xarray.Dataset
        An xarray dataset from the binary instrument data.

    """
    if '.' in filename:
        assert filename.endswith('nc'), 'File extension must be of the type nc'
    else:
        filename += '.nc'

    ds = xr.load_dataset(filename, engine='netcdf4')

    # Single item lists were saved as 'int' or 'str'
    if hasattr(ds, 'rotate_vars') and len(ds.rotate_vars[0]) == 1:
        ds.attrs['rotate_vars'] = [ds.rotate_vars]

    # Python lists were saved as numpy arrays
    if hasattr(ds, 'rotate_vars') and type(ds.rotate_vars) is not list:
        ds.attrs['rotate_vars'] = list(ds.rotate_vars)

    # Rejoin complex numbers
    if hasattr(ds, 'complex_vars') and len(ds.complex_vars):
        if len(ds.complex_vars[0]) == 1:
            ds.attrs['complex_vars'] = [ds.complex_vars]
        for var in ds.complex_vars:
            ds[var] = ds[var+'_real'] + ds[var+'_imag'] * 1j
            ds = ds.drop_vars([var+'_real', var+'_imag'])
    ds.attrs.pop('complex_vars')

    return ds


def save_mat(dataset, filename, datenum=True):
    """Save xarray dataset as a MATLAB (.mat) file

    Parameters
    ----------
    dataset : xarray.Dataset
        Data to save
    filename : str
        Filename and/or path with the '.mat' extension
    datenum : bool
        Converts epoch time into MATLAB datenum

    Notes
    -----
    The xarray data format is saved as a MATLAB structure with the fields 
    'vars, coords, config, units'

    See Also
    --------
    scipy.io.savemat()

    """
    if '.' in filename:
        assert filename.endswith(
            'mat'), 'File extension must be of the type mat'
    else:
        filename += '.mat'

    # Convert from epoch time to datenum
    if datenum:
        t_list = [t for t in dataset.coords if 'time' in t]
        for ky in t_list:
            dt = date2matlab(dt642date(dataset[ky]))
            dataset = dataset.assign_coords({ky: dt})

        t_data = [t for t in dataset.data_vars if t in t_additional]
        for ky in t_data:
            dt = date2matlab(dt642date(dataset[ky]))
            dataset[ky].data = dt

    # Save xarray structure with more descriptive structure names
    matfile = {'vars': {}, 'coords': {}, 'config': {}, 'units': {}}
    for key in dataset.data_vars:
        matfile['vars'][key] = dataset[key].values
        if hasattr(dataset[key], 'units'):
            matfile['units'][key] = dataset[key].units

    for key in dataset.coords:
        matfile['coords'][key] = dataset[key].values

    matfile['config'] = dataset.attrs

    sio.savemat(filename, matfile)


def load_mat(filename, datenum=True):
    """Load xarray dataset from MATLAB (.mat) file, complimentary to `save_mat()`

    A .mat file must contain the fields: {vars, coords, config, units},
    where 'coords' contain the dimensions of all variables in 'vars'.

    Parameters
    ----------
    filename : str
        Filename and/or path with the '.mat' extension
    datenum : bool
        Converts MATLAB datenum into epoch time

    Returns
    -------
    ds : xarray.Dataset
        An xarray dataset from the binary instrument data.

    See Also
    --------
    scipy.io.loadmat()

    """
    if '.' in filename:
        assert filename.endswith(
            'mat'), 'File extension must be of the type mat'
    else:
        filename += '.mat'

    data = sio.loadmat(filename, struct_as_record=False, squeeze_me=True)

    ds_dict = {'vars': {}, 'coords': {}, 'config': {}, 'units': {}}
    for nm in ds_dict:
        key_list = data[nm]._fieldnames
        for ky in key_list:
            ds_dict[nm][ky] = getattr(data[nm], ky)

    ds_dict['data_vars'] = ds_dict.pop('vars')
    ds_dict['attrs'] = ds_dict.pop('config')

    # Recreate dataset
    ds = _create_dataset(ds_dict)
    ds = _set_coords(ds, ds.coord_sys)

    # Convert datenum time back into epoch time
    if datenum:
        t_list = [t for t in ds.coords if 'time' in t]
        for ky in t_list:
            dt = date2dt64(matlab2date(ds[ky].values))
            ds = ds.assign_coords({ky: dt})
            ds[ky].attrs['description'] = 'seconds since 1970-01-01 00:00:00'

        t_data = [t for t in ds.data_vars if t in t_additional]
        for ky in t_data:
            dt = date2dt64(matlab2date(ds[ky].values))
            ds[ky].data = dt
            ds[ky].attrs['description'] = 'seconds since 1970-01-01 00:00:00'

    # Restore 'rotate vars" to a proper list
    if hasattr(ds, 'rotate_vars') and len(ds.rotate_vars[0]) == 1:
        ds.attrs['rotate_vars'] = [ds.rotate_vars]
    else:
        ds.attrs['rotate_vars'] = [x.strip(' ') for x in list(ds.rotate_vars)]

    return ds

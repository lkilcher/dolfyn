"""Module containing functions to clean data
"""
import numpy as np
from scipy.signal import medfilt
import xarray as xr
from ..tools.misc import medfiltnan
from ..rotate.api import rotate2
from ..rotate.base import _make_model, quaternion2orient


def set_deploy_altitude(ds, h_deploy):
    """
    Add instrument's height above seafloor to range of depth bins
    
    Parameters
    ----------
    ds : xarray.Dataset
      The adcp dataset to ajust 'range' on
    h_deploy : numeric
      Deployment location in the water column, in [m]
      
    Returns
    -------
    ds : xarray.Dataset
      The adcp dataset with 'range' adjusted
    
    Notes
    -----
    `Center of bin 1 = h_deploy + blank_dist + cell_size`
    
    Nortek doesn't take `h_deploy` into account, so the range that DOLfYN 
    calculates distance is from the ADCP transducers. TRDI asks for `h_deploy` 
    input in their deployment software and is thereby known by DOLfYN.
    
    If the ADCP is mounted on a tripod on the seafloor, `h_deploy` will be
    the height of the tripod +/- any extra distance to the transducer faces.
    If the instrument is vessel-mounted, `h_deploy` is the distance between 
    the surface and downward-facing ADCP's transducers.
    
    """
    r = [s for s in ds.dims if 'range' in s]
    for val in r:
        ds = ds.assign_coords({val: ds[val].values + h_deploy})
        ds[val].attrs['units'] = 'm'
        
    ds.attrs['h_deploy'] = h_deploy
    return ds


def find_surface(ds, thresh=10, nfilt=None):
    """
    Find the surface (water level or seafloor) from amplitude data

    Parameters
    ----------
    ds : xarray.Dataset
      The full adcp dataset
    thresh : int
      Specifies the threshold used in detecting the surface.
      (The amount that amplitude must increase by near the surface for it to
      be considered a surface hit)
    nfilt : int
      Specifies the width of the median filter applied, must be odd
      
    Returns
    -------
    ds : xarray.Dataset
      The full adcp dataset with `depth` added

    """
    # This finds the maximum of the echo profile:
    inds = np.argmax(ds.amp.values, axis=1)
    # This finds the first point that increases (away from the profiler) in
    # the echo profile
    edf = np.diff(ds.amp.values.astype(np.int16), axis=1)
    inds2 = np.max((edf < 0) *
                   np.arange(ds.vel.shape[1] - 1,
                             dtype=np.uint8)[None,:,None], axis=1) + 1

    # Calculate the depth of these quantities
    d1 = ds.range.values[inds]
    d2 = ds.range.values[inds2]
    # Combine them:
    D = np.vstack((d1, d2))
    # Take the median value as the estimate of the surface:
    d = np.median(D, axis=0)

    # Throw out values that do not increase near the surface by *thresh*
    for ip in range(ds.vel.shape[1]):
        itmp = np.min(inds[:, ip])
        if (edf[itmp:, :, ip] < thresh).all():
            d[ip] = np.NaN
    
    if nfilt:
        dfilt = medfiltnan(d, nfilt, thresh=.4)
        dfilt[dfilt==0] = np.NaN
        d = dfilt
        
    ds['depth'] = xr.DataArray(d, dims=['time'], attrs={'units':'m'})
    return ds


def surface_from_P(ds, salinity=35):
    """
    Approximates distance to water surface above ADCP from the pressure sensor.

    Parameters
    ----------
    ds : xarray.Dataset
      The full adcp dataset
    salinity: numeric
      Water salinity in psu
      
    Returns
    -------
    ds : xarray.Dataset
      The full adcp dataset with `depth` added
      
    Notes
    -----
    Requires that the instrument's pressure sensor was calibrated/zeroed
    before deployment to remove atmospheric pressure.
      
    """
    # pressure conversion from dbar to MPa / water weight
    rho = salinity + 1000
    d = (ds.pressure*10000)/(9.81*rho)
    
    if hasattr(ds, 'h_deploy'):
        d += ds.h_deploy
    
    ds['depth'] = xr.DataArray(d, dims=['time'], attrs={'units':'m'})
    
    return ds


def nan_beyond_surface(ds, val=np.nan):
    """
    Mask the values of the data that are beyond the surface.

    Parameters
    ----------
    ds : xarray.Dataset
      The adcp dataset to clean
    val : nan or numeric
      Specifies the value to set the bad values to (default np.nan).
      
    Returns 
    -------
    ds : xarray.Dataset
      The adcp dataset where relevant arrays with values greater than 
      `depth` are set to NaN
    
    Notes
    -----
    Surface interference expected to happen at `r > depth * cos(beam_angle)`

    """
    var = [h for h in ds.keys() if any(s for s in ds[h].dims if 'range' in s)]
    
    if 'nortek' in _make_model(ds):
        beam_angle = 25 *(np.pi/180)
    else: #TRDI
        try:
            beam_angle = ds.beam_angle 
        except:
            beam_angle = 20 *(np.pi/180)
        
    bds = ds.range > (ds.depth * np.cos(beam_angle) - ds.cell_size)
    
    if 'echo' in var:
        bds_echo = ds.range_echo > ds.depth
        ds['echo'].values[...,bds_echo] = val
        var.remove('echo')

    for nm in var:
        # workaround for xarray since it can't handle 2D boolean arrays
        a = ds[nm].values
        try:
            a[...,bds] = val
        except: # correlation
            a[...,bds] = 0 
        ds[nm].values = a
    
    return ds
    

def vel_exceeds_thresh(ds, thresh=5, val=np.nan):
    """
    Find values of the velocity data that exceed a threshold value,
    and assign NaN to the velocity data where the threshold is
    exceeded.

    Parameters
    ----------
    ds : xr.Dataset
      The adcp dataset to clean
    thresh : numeric
      The maximum value of velocity to screen
    val : nan or numeric
      Specifies the value to set the bad values to (default np.nan)
      
    Returns
    -------
    ds : xarray.Dataset
      The adcp dataset with datapoints beyond thresh are set to `val`

    """
    bd = np.zeros(ds.vel.shape, dtype='bool')
    bd |= (np.abs(ds.vel.values) > thresh)
    
    ds.vel.values[bd] = val
    
    return ds


def correlation_filter(ds, thresh=50, val=np.nan):
    """
    Filters out velocity data where correlation is below a 
    threshold in the beam correlation data.
    
    Parameters
    ----------
    ds : xarray.Dataset
      The adcp dataset to clean.
    thresh : numeric
      The maximum value of correlation to screen, in counts or %
    val : numeric
      Value to set masked correlation data to, default is nan
      
    Returns
    -------
    ds : xarray.Dataset
     The adcp dataset with low correlation values set to `val`
    
    """
    # copy original ref frame
    coord_sys_orig = ds.coord_sys
    # correlation is always in beam coordinates
    mask = (ds.corr.values<=thresh)
    
    if hasattr(ds, 'vel_b5'):
        mask_b5 = (ds.corr_b5.values<=thresh)
        ds.vel_b5.values[mask_b5] = val
    
    ds = rotate2(ds, 'beam')
    ds.vel.values[mask] = val
    ds = rotate2(ds, coord_sys_orig)

    return ds


def medfilt_orient(ds, nfilt=7):
    """
    Median filters the orientation data (heading-pitch-roll or quaternions)

    Parameters
    ----------
    ds : xarray.Dataset
      The adcp dataset to clean
    nfilt : numeric
      The length of the median-filtering kernel
      *nfilt* must be odd.
      
    Return
    ------
    ds : xarray.Dataset
      The adcp dataset with the filtered orientation data

    See Also
    --------
    scipy.signal.medfilt()

    """
    if getattr(ds, 'has_imu'):
        q_filt = np.zeros(ds.quaternion.shape)
        for i in range(ds.quaternion.q.size):
            q_filt[i] = medfilt(ds.quaternion[i].values, nfilt)
        ds.quaternion.values = q_filt
        
        ds['orientmat'] = quaternion2orient(ds.quaternion)
        return ds
    
    else:
        # non Nortek AHRS-equipped instruments
        do_these = ['pitch', 'roll', 'heading']
        for nm in do_these:
            ds[nm].values = medfilt(ds[nm].values, nfilt)
            
        return ds.drop_vars('orientmat')


def fillgaps_time(ds, method='cubic', max_gap=None):
    """
    Fill gaps (nan values) across time using the specified method
    
    Parameters
    ----------
    ds : xarray.Dataset
      The adcp dataset to clean
    method : string
      Interpolation method to use
    max_gap : numeric
      Max number of consective NaN's to interpolate across
      
    Returns
    -------
    ds : xarray.Dataset
      The adcp dataset with gaps in velocity interpolated across time
      
    See Also
    --------
    xarray.DataArray.interpolate_na()
        
    """
    ds['vel'] = ds.vel.interpolate_na(dim='time', method=method,
                                      use_coordinate=True,
                                      max_gap=max_gap)
    if hasattr(ds, 'vel_b5'):
        ds['vel_b5'] = ds.vel.interpolate_na(dim='time', method=method,
                                             use_coordinate=True,
                                             max_gap=max_gap)
    return ds


def fillgaps_depth(ds, method='cubic', max_gap=None):
    """
    Fill gaps (nan values) along the depth profile using the specified method

    Parameters
    ----------
    ds : xarray.Dataset
      The adcp dataset to clean
    method : string
      Interpolation method to use
    max_gap : numeric
      Max number of consective NaN's to interpolate across
      
    Returns
    -------
    ds : xarray.Dataset
      The adcp dataset with gaps in velocity interpolated across depth profiles

    See Also
    --------
    xarray.DataArray.interpolate_na()
        
    """
    ds['vel'] = ds.vel.interpolate_na(dim='range', method=method,
                                      use_coordinate=False,
                                      max_gap=max_gap)
    if hasattr(ds, 'vel_b5'):
        ds['vel_b5'] = ds.vel.interpolate_na(dim='range', method=method,
                                             use_coordinate=True,
                                             max_gap=max_gap)
    return ds

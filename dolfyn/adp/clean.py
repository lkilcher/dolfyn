import numpy as np
from scipy.signal import medfilt
import xarray as xr
from ..tools import misc as tbx


def find_surface(adcpo, thresh=10, nfilt=None):
    """
    Find the surface, from the amplitude data of the *adp* adcp object.

    Parameters
    ----------
    adcpo : |xr.Dataset|
      The adcp dataset to clean.
    thresh : numeric
      Specifies the threshold used in detecting the surface.
      (The amount that amplitude must increase by near the surface for it to
       be considered a surface hit)
    nfilt : numeric
      Specifies the width of the median filter applied, must be odd

    """
    # This finds the maximum of the echo profile:
    inds = np.argmax(adcpo.amp.values, axis=1)
    # This finds the first point that increases (away from the profiler) in
    # the echo profile
    edf = np.diff(adcpo.amp.values.astype(np.int16), axis=1)
    inds2 = np.max((edf < 0) *
                   np.arange(adcpo.vel.shape[1] - 1,
                             dtype=np.uint8)[None,:,None], axis=1) + 1

    # Calculate the depth of these quantities
    d1 = adcpo.range.values[inds]
    d2 = adcpo.range.values[inds2]
    # Combine them:
    D = np.vstack((d1, d2))
    # Take the median value as the estimate of the surface:
    d = np.median(D, axis=0)

    # Throw out values that do not increase near the surface by *thresh*
    for ip in range(adcpo.vel.shape[1]):
        itmp = np.min(inds[:, ip])
        if (edf[itmp:, :, ip] < thresh).all():
            d[ip] = np.NaN
    
    if nfilt:
        dfilt = tbx.medfiltnan(d, nfilt, thresh=.4)
        dfilt[dfilt==0] = np.NaN
        d = dfilt
        
    adcpo['d_range'] = xr.DataArray(
        d, 
        dims=['time'], 
        attrs={'units':'m'})
    return adcpo


def surface_from_P(adcpo, salinity=35):
    '''
    Approximates distance to water surface above ADCP from the altimeter.
    Requires that the instrument's pressure sensor was calibrated/zeroed
    before deployment to remove atmospheric pressure.

    Parameters
    ----------
    adcpo : |xr.Dataset|
      The adcp dataset to clean.
    salinity: numeric
      Water salinity in psu.
      
    '''
    if hasattr(adcpo, 'salinity'):
        rho = adcpo.salinity + 1000 # kg/m^3
    else:
        rho = salinity + 1000
        
    # pressure conversion from dbar to MPa / water weight
    d = (adcpo.pressure*10000)/(9.81*rho)
    
    adcpo['d_range'] = xr.DataArray(
        d, 
        dims=['time'], 
        attrs={'units':'m'})
    return adcpo


def nan_beyond_surface(adcpo, val=np.nan):
    """
    NaN the values of the data that are beyond the surface.

    Parameters
    ----------
    adcpo : |xr.Dataset|
      The adcp dataset to clean.
    val : nan or numeric
      Specifies the value to set the bad values to (default np.nan).
    
    Notes
    -----
    Surface interference expected to happen at `r > d_range * cos(beam_angle)`

    """
    var = [h for h in adcpo.keys() if hasattr(adcpo[h],'range')]
    
    if 'nortek' in adcpo.Veldata._make_model.lower():
        beam_angle = 25 *(np.pi/180)
    else: #TRDI
        beam_angle = adcpo.beam_angle #20 *(np.pi/180)
        
    bds = adcpo.range > adcpo.d_range * np.cos(beam_angle)
    
    for nm in var:
        # workaround for xarray since it can't handle 2D boolean arrays
        a = adcpo[nm].values
        try:
            a[...,bds] = val
        except: # correlation
            a[...,bds] = 0 
        adcpo[nm].values = a
    
    return adcpo


def vel_exceeds_thresh(adcpo, thresh=5, val=np.nan):
    """
    Find values of the velocity data that exceed a threshold value,
    and assign NaN to the velocity data where the threshold is
    exceeded.

    Parameters
    ----------
    adcpo : |xr.Dataset|
      The adcp dataset to clean.
    thresh : numeric
      The maximum value of velocity to screen.
    val : nan or numeric
      Specifies the value to set the bad values to (default np.nan).

    """
    bd = np.zeros(adcpo.vel.shape, dtype='bool')
    bd |= (np.abs(adcpo.vel.values) > thresh)
    
    adcpo.vel.values[bd] = val
    
    return adcpo


def correlation_filter(adcpo, thresh=70, val=np.nan):
    '''
    Filters out velocity data where correlation is below a 
    threshold in the beam correlation data.
    
    Parameters
    ----------
    adcpo : |xr.Dataset|
      The adcp dataset to clean.
    thresh : numeric
      The maximum value of correlation to screen.
    
    '''
    mask = (adcpo.corr.values<=thresh)
    
    if hasattr(adcpo, 'vel_b5'):
        mask_b5 = (adcpo.corr_b5.values<=thresh)
        adcpo.vel_b5.values[mask_b5] = val
    
    adcpo = adcpo.Veldata.rotate2('beam')
    adcpo.vel.values[mask] = val
    adcpo = adcpo.Veldata.rotate2('earth')

    return adcpo


def medfilt_orientation(adcpo, nfilt=7):
    """
    Median filters the orientation data (pitch, roll, heading).

    Parameters
    ----------
    adcpo : |xr.Dataset|
      The adcp dataset to clean.
    nfilt : numeric
      The length of the median-filtering kernel.
       *nfilt must be odd.

    see also:
    scipy.signal.medfilt

    """
    do_these = ['pitch', 'roll', 'heading']
    for nm in do_these:
        adcpo[nm].values = medfilt(adcpo[nm].values, nfilt)
        
    return adcpo


def fillgaps_time(adcpo, method='linear', max_gap=None):
    """
    Fill gaps (NaN values) across time by 'method'
    
    Parameters
    ----------
    adcpo : |xr.Dataset|
      The adcp dataset to clean.
    method : string
      Interpolation method to use
    max_gap : numeric
      Max number of consective NaN's to interpolate across
      
    see also :
        xr.DataArray.interpolate_na()
        
    """
    adcpo['vel'] = adcpo.vel.interpolate_na(dim='time', method=method,
                                            use_coordinate=True,
                                            max_gap=max_gap)
    if hasattr(adcpo, 'vel_b5'):
        adcpo['vel_b5'] = adcpo.vel.interpolate_na(dim='time', method=method,
                                                   use_coordinate=True,
                                                   max_gap=max_gap)
    #tbx.fillgaps(adcpo.vel.values, maxgap=maxgap, dim=-1)
    return adcpo


def fillgaps_depth(adcpo, method='linear', max_gap=None):
    """
    Fill gaps (NaN values) up and down the depth profile by 'method'

    Parameters
    ----------
    adcpo : |xr.Dataset|
      The adcp dataset to clean.
    method : string
      Interpolation method to use
    max_gap : numeric
      Max number of consective NaN's to interpolate across

    see also:
        xr.DataArray.interpolate_na()
        
    """
    adcpo['vel'] = adcpo.vel.interpolate_na(dim='range', method=method,
                                            use_coordinate=False,
                                            max_gap=max_gap)
    if hasattr(adcpo, 'vel_b5'):
        adcpo['vel_b5'] = adcpo.vel.interpolate_na(dim='range', method=method,
                                                   use_coordinate=True,
                                                   max_gap=max_gap)
    #tbx.fillgaps(adcpo.vel.values, maxgap=maxgap, dim=0)
    return adcpo

import numpy as np
from scipy.signal import medfilt
import xarray as xr
from ..tools import misc as tbx


def find_surface(adcpo, thresh=10, nfilt=None):
    """
    Find the surface, from the amplitude data of the *adp* adcp object.

    *thresh* specifies the threshold used in detecting the surface.
    (The amount that amplitude must increase by near the surface for it to
    be considered a surface hit)

    *nfilt* specifies the width of the median filter applied, must be odd

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
        
    adcpo['d_range'] = xr.DataArray(d, dims=['time'], 
                                    attrs={'units':'m', 
                                           'description': 'distance to seabed or water surface'})
    return adcpo


def surface_from_pressure(adcpo):
    '''
    Approximates distance to water surface above ADCP from pressure data
    Requires that the instrument's pressure sensor was calibrated/zeroed
    before deployment to remove atmospheric pressure

    '''
    # pressure conversion from dbar to MPa / water weight
    rho = adcpo.salinity + 1000 # kg/m^3
    d = (adcpo.pressure*10000)/(9.81*rho)
    
    adcpo['d_range'] = xr.DataArray(d, dims=['time'], 
                                attrs={'units':'m', 
                                       'description': 'water surface level above instrument'})
    return adcpo   


def nan_beyond_surface(adcpo, dfrac=0.9, val=np.NaN):
    """
    NaN the values of the data that are above the surface (from the
    variable *d_range_filt*) in the *adp* object.

    *var* specifies the values to NaN out.

    *dfrac* specifies the fraction of the depth range that is
     considered good (default 0.9).

    *val* specifies the value to set the bad values to (default np.NaN).

    """
    var = [h for h in adcpo.keys() if hasattr(adcpo[h],'range')]
    
    bds = adcpo.range > adcpo.d_range
    for nm in var:
        getattr(adcpo, nm)[:,bds] = val


def vel_exceeds_thresh(adcpo, thresh=5):
    """
    Find values of the velocity data that exceed a threshold value,
    and assign NaN to the velocity data where the threshold is
    exceeded.

    Parameters
    ----------
    adcpo : :class:`adp_raw <base.adp_raw>`
      The adp object to clean.
    thresh : numeric
      The maximum value of velocity to screen.

    """
    bd = np.zeros(adcpo.vel.shape, dtype='bool')
    bd |= (np.abs(adcpo.vel.values) > thresh)
    
    adcpo.vel.values[bd] = np.NaN
    
    return adcpo


def correlation_filter(adcpo, thresh=70):
    '''
    Filters out datapoints where correlation is below a threshold in the beam 
    data.    
    
    '''
    mask = (adcpo.corr.values<=thresh)
    
    adcpo = adcpo.Velocity.rotate2('beam')
    adcpo.vel.values[mask] = np.NaN
    adcpo = adcpo.Velocity.rotate2('earth')

    return adcpo


def medfilt_orientation(adcpo, nfilt=7):
    """
    Median filters the orientation data (pitch, roll, heading).

    *nfilt* is the length of the median-filtering kernel.
       *nfilt must be odd.

    see also:
    scipy.signal.medfilt

    """
    do_these = ['pitch', 'roll', 'heading']
    for nm in do_these:
        adcpo[nm] = medfilt(adcpo[nm], nfilt)


def fillgaps_time(adcpo, vars=['u', 'v', 'w'], maxgap=np.inf):
    """
    Fill gaps (NaN values) linearly across time. Assumes a constant time delta.
    
    """
    tbx.fillgaps(adcpo.vel.values, maxgap=maxgap, dim=-1)


def fillgaps_depth(adcpo, vars=['u', 'v', 'w'], maxgap=np.inf):
    """
    Fill gaps (NaN values) linearly up and down the depth profile.
    
    """
    tbx.fillgaps(adcpo.vel.values, maxgap=maxgap, dim=0)

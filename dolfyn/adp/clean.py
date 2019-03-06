import numpy as np
from scipy.signal import medfilt
from ..tools import misc as tbx


def find_surface(apd, thresh=10, nfilt=1001):
    """
    Find the surface, from the echo data of the *apd* adcp object.

    *thresh* specifies the threshold used in detecting the surface.
    (The amount that echo must increase by near the surface for it to
    be considered a surface hit)

    *nfilt* specifies the width of the nanmedianfilter applied to
     produce *d_range_filt*.

    """
    # This finds the minimum of the echo profile:
    inds = np.argmin(apd.echo[:], axis=0)
    # This finds the first point that increases (away from the profiler) in
    # the echo profile
    edf = np.diff(apd.echo[:].astype(np.int16), axis=0)
    inds2 = np.max((edf < 0) *
                   np.arange(apd.shape[0] - 1,
                             dtype=np.uint8)[:, None, None], axis=0) + 1

    # Calculate the depth of these quantities
    d1 = apd.ranges[inds]
    d2 = apd.ranges[inds2]
    # Combine them:
    D = np.vstack((d1, d2))
    # Take the median value as the estimate of the surface:
    d = np.median(D, axis=0)

    # Throw out values that do not increase near the surface by *thresh*
    for ip in range(apd.shape[1]):
        itmp = np.min(inds[:, ip])
        if (edf[itmp:, :, ip] < thresh).all():
            d[ip] = np.NaN
    dfilt = tbx.medfiltnan(d, nfilt, thresh=.4)
    dfilt[dfilt == 0] = np.NaN
    apd.add_data('d_range', d, '_essential')
    apd.add_data('d_range_filt', dfilt, '_essential')


def nan_above_surface(adp, dfrac=0.9,
                      vars=['u', 'v', 'w', 'err_vel',
                            'beam1vel', 'beam2vel', 'beam3vel', 'beam4vel',
                            'u_inst', 'v_inst', 'w_inst'],
                      val=np.NaN):
    """
    NaN the values of the data that are above the surface (from the
    variable *d_range_filt*) in the *adp* object.

    *vars* specifies the values to NaN out.

    *dfrac* specifies the fraction of the depth range that is
     considered good (default 0.9).

    *val* specifies the value to set the bad values to (default np.NaN).

    """
    bds = adp.ranges[:, None] > adp.d_range_filt
    for nm in vars:
        if hasattr(adp, nm):
            getattr(adp, nm)[bds] = val


def vel_exceeds_thresh(adcpo, thresh=10, source=None):
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
    source : string {`beam` (default),`earth`,`inst`}
      This specifies whether to use beam, earth or instrument
      velocities to find bad values.  All of these data sources (if
      they exist) are cleaned.

    """

    if source is None or source == 'beam':
        sources = ['beam1vel', 'beam2vel', 'beam3vel', 'beam4vel']
    elif source == 'earth':
        sources = ['u', 'v', 'w']
    elif source == 'inst':
        sources = ['u_inst', 'v_inst', 'w_inst']
    bd = np.zeros(getattr(adcpo, sources[0]).shape, dtype='bool')
    for src in sources:
        bd |= (np.abs(getattr(adcpo, src)[:]) > thresh)
    for dt in ['beam1vel', 'beam2vel', 'beam3vel', 'beam4vel',
               'u', 'v', 'w', 'err_vel'
               'u_inst', 'v_inst', 'w_inst', ]:
        if hasattr(adcpo, dt):
            getattr(adcpo, dt)[bd] = np.NaN


def medfilt_orientation(adcpo, kernel_size=7):
    """
    Median filters the orientation data (pitch, roll, heading).

    *kernel_size* is the length of the median-filtering kernel.
       *kernel_size* must be odd.

    see also:
    scipy.signal.medfilt

    """

    do_these = ['pitch_deg', 'roll_deg', 'heading_deg']
    for nm in do_these:
        setattr(adcpo, nm, medfilt(getattr(adcpo, nm), kernel_size))


def fillgaps_time(adcpo, vars=['u', 'v', 'w'], maxgap=np.inf):
    """
    Fill gaps
    """
    for vr in vars:
        tbx.fillgaps(getattr(adcpo, vr), maxgap=maxgap, dim=-1)


def fillgaps_depth(adcpo, vars=['u', 'v', 'w'], maxgap=np.inf):
    """
    Fill gaps
    """
    for vr in vars:
        tbx.fillgaps(getattr(adcpo, vr), maxgap=maxgap, dim=0)

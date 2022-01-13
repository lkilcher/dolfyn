from datetime import datetime, timedelta, timezone
import numpy as np


def _fullyear(year):
    if year > 100:
        return year
    year += 1900 + 100 * (year < 90)
    return year


def epoch2dt64(ep_time, ):
    # assumes t0=1970-01-01 00:00:00
    out = np.array(ep_time.astype('int')).astype('datetime64[s]')
    out = out + ((ep_time % 1) * 1e9).astype('timedelta64[ns]')
    return out


def dt642epoch(dt64):
    return dt64.astype('datetime64[ns]').astype('float') / 1e9


def date2dt64(dt):
    return np.array(dt).astype('datetime64[ns]')


def dt642date(dt64):
    return epoch2date(dt642epoch(dt64))


def epoch2date(ep_time, offset_hr=0, to_str=False):
    """
    Convert from epoch time (seconds since 1/1/1970 00:00:00) to a list 
    of datetime objects

    Parameters
    ----------
    ep_time : xarray.DataArray
        Time coordinate data-array or single time element
    offset_hr : int
        Number of hours to offset time by (e.g. UTC -7 hours = PDT)
    to_str : logical
        Converts datetime object to a readable string

    Returns
    -------
    time : datetime
        The converted datetime object or list(strings) 

    Notes
    -----
    The specific time instance is set during deployment, usually sync'd to the
    deployment computer. The time seen by |dlfn| is in the timezone of the 
    deployment computer, which is unknown to |dlfn|.

    """
    try:
        ep_time = ep_time.values
    except AttributeError:
        pass

    if isinstance(ep_time, (np.ndarray)) and ep_time.ndim == 0:
        ep_time = [ep_time.item()]
    elif not isinstance(ep_time, (np.ndarray, list)):
        ep_time = [ep_time]

    ######### IMPORTANT #########
    # Note the use of `utcfromtimestamp` here, rather than `fromtimestamp`
    # This is CRITICAL! See the difference between those functions here:
    #    https://docs.python.org/3/library/datetime.html#datetime.datetime.fromtimestamp
    # Long story short: `fromtimestamp` used system-specific timezone
    # info to calculate the datetime object, but returns a
    # timezone-agnostic object.
    if offset_hr != 0:
        delta = timedelta(hours=offset_hr)
        time = [datetime.utcfromtimestamp(t) + delta for t in ep_time]
    else:
        time = [datetime.utcfromtimestamp(t) for t in ep_time]

    if to_str:
        time = date2str(time)

    return time


def date2str(dt, format_str=None):
    """
    Convert list of datetime objects to legible strings

    Parameters
    ----------
    dt : datetime.datetime
        Single or list of datetime object(s)
    format_str : string
        Timestamp string formatting, default: '%Y-%m-%d %H:%M:%S.%f'. 
        See datetime.strftime documentation for timestamp string formatting

    Returns
    -------
    time : string
        Converted timestamps

    """
    if format_str is None:
        format_str = '%Y-%m-%d %H:%M:%S.%f'

    if not isinstance(dt, list):
        dt = [dt]

    return [t.strftime(format_str) for t in dt]


def date2epoch(dt):
    """
    Convert list of datetime objects to epoch time

    Parameters
    ----------
    dt : datetime.datetime
        Single or list of datetime object(s)

    Returns
    -------
    time : float
        Datetime converted to epoch time (seconds since 1/1/1970 00:00:00)

    """
    if not isinstance(dt, list):
        dt = [dt]

    return [t.replace(tzinfo=timezone.utc).timestamp() for t in dt]


def date2matlab(dt):
    """
    Convert list of datetime objects to MATLAB datenum

    Parameters
    ----------
    dt : datetime.datetime
        List of datetime objects

    Returns
    -------
    time : float
        List of timestamps in MATLAB datnum format

    """
    time = list()
    for i in range(len(dt)):
        mdn = dt[i] + timedelta(days=366)
        frac_seconds = (dt[i]-datetime(dt[i].year, dt[i].month,
                        dt[i].day, 0, 0, 0)).seconds / (24*60*60)
        frac_microseconds = dt[i].microsecond / (24*60*60*1000000)
        time.append(mdn.toordinal() + frac_seconds + frac_microseconds)

    return time


def matlab2date(matlab_dn):
    """
    Convert MATLAB datenum to list of datetime objects

    Parameters
    ----------
    matlab_dn : float
        List of timestamps in MATLAB datnum format

    Returns
    -------
    dt : datetime.datetime
        List of datetime objects

    """
    time = list()
    for i in range(len(matlab_dn)):
        day = datetime.fromordinal(int(matlab_dn[i]))
        dayfrac = timedelta(days=matlab_dn[i] % 1) - timedelta(days=366)
        time.append(day + dayfrac)

    return time

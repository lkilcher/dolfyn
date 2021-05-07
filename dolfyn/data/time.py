from __future__ import division
from datetime import datetime, timedelta


def epoch2date(ds_time, utc=False, offset_hr=0, to_str=False):
    '''
    Convert from seconds since 1/1/1970 to datetime object
    
    ds_time : |xr.DataArray|
        Time coordinate data-array
    
    utc : logical, default=False
        If True, converts to UTC. If False, data is in instrument's 
        timezone (unknown to dolfyn)
    
    offset_hr : int
        Number of hours to offset time by (e.g. UTC -7 hours = PDT)
    
    to_str : logical
        Converts epoch time to a readable string
        
    '''
    ds_time = ds_time.values
    
    if utc:
        time = [datetime.utcfromtimestamp(t) for t in ds_time]
    else:
        time = [datetime.fromtimestamp(t) for t in ds_time]
    if offset_hr != 0:
        time = [t + timedelta(hours=offset_hr) for t in time]
    if to_str:
        time = date2str(time)
    
    return time


def date2str(dt, format_str=None):
    '''
    Convert datetimes to actual legible times
    
    '''
    if format_str is None:
        format_str = '%Y-%m-%d %H:%M:%S.%f'
        
    return [t.strftime(format_str) for t in dt]
    
    
def matlab2date(matlab_dn):
    '''
    Convert matlab datenum to python datetime
    
    '''
    time = list()
    for i in range(len(matlab_dn)):
        day = datetime.fromordinal(int(matlab_dn[i]))
        dayfrac = timedelta(days=matlab_dn[i]%1) - timedelta(days=366)
        time.append(day + dayfrac)
        
    return time

def date2matlab(dt):
    '''
    Convert python datetime to matlab datenum
    
    '''
    time = list()
    for i in range(len(dt)):
        mdn = dt[i] + timedelta(days=366)
        frac_seconds = (dt[i]-datetime(dt[i].year,dt[i].month,dt[i].day,0,0,0)).seconds / (24*60*60)
        frac_microseconds = dt[i].microsecond / (24*60*60*1000000)
        time.append(mdn.toordinal() + frac_seconds + frac_microseconds)
        
    return time


def _fullyear(year):
    """
    Convert
    """
    if year > 100:
        return year
    year += 1900 + 100 * (year < 90)
    return year


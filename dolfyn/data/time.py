"""
This modules is a reimplemntation of the 'mpltime' format (ordinal + fractional time).

This is an independent implementation of that format so that the DOLfYN module does not depend on matplotlib (>30MB).

In the future I'd like to move away from this to np.datetime64 once that comes online, but apparently it has several issues so I'm going to simply use this for now.

"""
import numpy as np
from datetime import datetime, timedelta

def num2date(mpltime):
    if np.ndarray in mpltime.__class__.__mro__:
        out = np.empty(len(mpltime),dtype = 'O')
        for idx,val in enumerate(mpltime.flat):
            out[idx] = num2date(val)
        out.shape = mpltime.shape
        return out
    return datetime.fromordinal(int(mpltime)) + timedelta(days=mpltime%1)

def date2num(dt):
    if np.ndarray in dt.__class__.__mro__:
        out = np.empty(len(dt), dtype=np.float64)
        for idx,val in enumerate(dt.flat):
            out[idx] = date2num(val)
        out.shape = dt.shape
        return out
    return dt.toordinal() + (dt.hour + (dt.minute + (dt.second + dt.microsecond/1e6)/60.)/60. )/24.

def mpltime2matlab_datenum(time):
    return time.view(np.ndarray) + 366

class time_array(np.ndarray):
    """
    This class uses time in matplotlib's mpltime format (ordinal + fractional-day).
    """

    def __new__(cls,data):
        obj = np.asarray(data).view(cls)
        return obj
        
    @property
    def datetime(self,):
        if not hasattr(self,'_datetime'):
            self._datetime = num2date(self)
        return self._datetime

    @property
    def year(self,):
        out = np.empty(len(self),dtype = np.uint16)
        for idx,val in enumerate(self.datetime.flat):
            out[idx] = val.year
        out.shape = self.shape
        return out
        
    @property
    def month(self,):
        out = np.empty(len(self),dtype = np.uint8)
        for idx,val in enumerate(self.datetime.flat):
            out[idx] = val.month
        out.shape = self.shape
        return out

    @property
    def day(self,):
        out = np.empty(len(self),dtype = np.uint8)
        for idx,val in enumerate(self.datetime.flat):
            out[idx] = val.day
        out.shape = self.shape
        return out

    @property
    def hour(self,):
        out = np.empty(len(self),dtype = np.uint8)
        for idx,val in enumerate(self.datetime.flat):
            out[idx] = val.hour
        out.shape = self.shape
        return out

    @property
    def minute(self,):
        out = np.empty(len(self),dtype = np.uint8)
        for idx,val in enumerate(self.datetime.flat):
            out[idx] = val.minute
        out.shape = self.shape
        return out

    @property
    def second(self,):
        out = np.empty(len(self),dtype = np.uint8)
        for idx,val in enumerate(self.datetime.flat):
            out[idx] = val.second
        out.shape = self.shape
        return out

    @property
    def matlab_datenum(self,):
        return mpltime2matlab_datenum(self)

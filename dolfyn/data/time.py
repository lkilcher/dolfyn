"""
This modules is a reimplemntation of the 'mpltime' format (ordinal +
fractional time).

This is an independent implementation of that format so that the
DOLfYN module does not depend on matplotlib (>30MB).

In the future I'd like to move away from this to np.datetime64 once
that comes online, but apparently it has several issues so I'm going
to simply use this for now.

"""
from __future__ import division
import numpy as np
from datetime import datetime, timedelta
from six import string_types


def _fullyear(year):
    """
    Convert
    """
    if year > 100:
        return year
    year += 1900 + 100 * (year < 90)
    return year


def isotime2mpltime(val):
    if isinstance(val, string_types):
        return date2num(datetime.strptime(val, '%Y-%m-%dT%H:%M:%S'))
    elif isinstance(val, (tuple, list)):
        out = np.empty(len(val), dtype=np.float64)
    elif isinstance(val, np.ndarray):
        out = np.empty(len(val), dtype=np.float64)
    else:
        raise ValueError("Invalid time type.")
    for idx, v in enumerate(val):
        out[idx] = isotime2mpltime(v)
    return out


def num2date(mpltime):
    if isinstance(mpltime, np.ndarray):
        try:
            n = len(mpltime)
        except TypeError:
            pass
        else:
            out = np.empty(n, dtype='O')
            for idx, val in enumerate(mpltime.flat):
                out[idx] = num2date(val)
            out.shape = mpltime.shape
            return out
    if np.isnan(mpltime):
        return None
    return datetime.fromordinal(int(mpltime)) + timedelta(days=mpltime % 1)


def date2num(dt):
    if isinstance(dt, np.ndarray):
        out = np.empty(len(dt), dtype=np.float64)
        for idx, val in enumerate(dt.flat):
            out[idx] = date2num(val)
        out.shape = dt.shape
        return out
    if dt is None:
        return np.NaN
    return (dt.toordinal() +
            (((dt.microsecond / 1e6 +
               dt.second) / 60 +
              dt.minute) / 60 +
             dt.hour) / 24)


def mpltime2matlab_datenum(time):
    return time.view(np.ndarray) + 366


class time_array(np.ndarray):

    """
    This class uses time in matplotlib's mpltime format (ordinal +
    fractional-day).
    """

    def __new__(cls, data):
        obj = np.asarray(data).view(cls)
        return obj

    @property
    def datetime(self,):
        if not hasattr(self, '_datetime'):
            self._datetime = num2date(self)
        return self._datetime

    @property
    def year(self,):
        out = np.empty(len(self), dtype=np.uint16)
        for idx, val in enumerate(self.datetime.flat):
            out[idx] = val.year
        out.shape = self.shape
        return out

    @property
    def month(self,):
        out = np.empty(len(self), dtype=np.uint8)
        for idx, val in enumerate(self.datetime.flat):
            out[idx] = val.month
        out.shape = self.shape
        return out

    @property
    def day(self,):
        out = np.empty(len(self), dtype=np.uint8)
        for idx, val in enumerate(self.datetime.flat):
            out[idx] = val.day
        out.shape = self.shape
        return out

    @property
    def hour(self,):
        out = np.empty(len(self), dtype=np.uint8)
        for idx, val in enumerate(self.datetime.flat):
            out[idx] = val.hour
        out.shape = self.shape
        return out

    @property
    def minute(self,):
        out = np.empty(len(self), dtype=np.uint8)
        for idx, val in enumerate(self.datetime.flat):
            out[idx] = val.minute
        out.shape = self.shape
        return out

    @property
    def second(self,):
        out = np.empty(len(self), dtype=np.uint8)
        for idx, val in enumerate(self.datetime.flat):
            out[idx] = val.second
        out.shape = self.shape
        return out

    @property
    def matlab_datenum(self,):
        return mpltime2matlab_datenum(self)

    def minmax(self, round_to=None):
        """
        Find the minimum and maximum values in the time object.

        The value `round_to` specifies that the `min`/`max` values
        should be rounded down/up (respectively) to the nearest:
        'second', 's'
        'minute', 'M'
        'hour', 'h'
        'day', 'd'
        'month', 'm'
        'year', 'y'
        """
        minmax = np.array([min(self), max(self)])
        if round_to is None:
            return minmax

        elif round_to.lower().startswith('s'):
            # Round to second:
            minmax[0] = np.floor(minmax[0] * 24 * 3600) / (24 * 3600)
            minmax[1] = np.ceil(minmax[1] * 24 * 3600) / (24 * 3600)

        elif round_to == 'M' or round_to.lower().startswith('mi'):
            # Round to minute:
            minmax[0] = np.floor(minmax[0] * 24 * 60) / (24 * 60)
            minmax[1] = np.ceil(minmax[1] * 24 * 60) / (24 * 60)

        elif round_to.lower().startswith('h'):
            # Round to hour:
            minmax[0] = np.floor(minmax[0] * 24) / (24)
            minmax[1] = np.ceil(minmax[1] * 24) / (24)

        elif round_to.lower().startswith('d'):
            # Round to day:
            minmax[0] = np.floor(minmax[0])
            minmax[1] = np.ceil(minmax[1])

        elif round_to == 'm' or round_to.lower().startswith('mo'):
            # Round to month:
            dt = num2date(minmax[0])
            minmax[0] = date2num(datetime(dt.year, dt.month, 1))
            dt = num2date(minmax[1])
            y = dt.year
            m = dt.month
            if m < 12:
                m += 1
            else:  # m==12
                y += 1
                m = 1
            minmax[1] = date2num(datetime(y, m, 1))

        elif round_to.lower().startswith('y'):
            # Round to year:
            dt = num2date(minmax[0])
            minmax[0] = date2num(datetime(dt.year, 1, 1))
            dt = num2date(minmax[1])
            minmax[1] = date2num(datetime(dt.year + 1, 1, 1))

        return minmax

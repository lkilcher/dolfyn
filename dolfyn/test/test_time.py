from dolfyn.test import test_read_adv as tr
from numpy.testing import assert_equal, assert_allclose
import numpy as np
import dolfyn.time as time
from datetime import datetime


def test_epoch2date():
    td = tr.dat_imu.copy(deep=True)
    
    dt = time.epoch2date(td.time)
    dt1 = time.epoch2date(td.time[0])
    dt_off = time.epoch2date(td.time, offset_hr=-7)
    t_str = time.epoch2date(td.time, to_str=True)
    
    assert_equal(dt[0], datetime(2012, 6, 12, 12, 0, 2, 687283))
    assert_equal(dt1, [datetime(2012, 6, 12, 12, 0, 2, 687283)])
    assert_equal(dt_off[0], datetime(2012, 6, 12, 5, 0, 2, 687283))
    assert_equal(t_str[0], '2012-06-12 12:00:02.687283')


def test_datetime():
    td = tr.dat_imu.copy(deep=True)
    
    dt = time.epoch2date(td.time)
    epoch = np.array(time.date2epoch(dt))
    
    assert_allclose(td.time.values, epoch, atol=1e-7)
    
    
def test_datenum():
    td = tr.dat_imu.copy(deep=True)
    
    dt = time.epoch2date(td.time)
    dn = time.date2matlab(dt)
    dt2 = time.matlab2date(dn)
    epoch = np.array(time.date2epoch(dt2))
    
    assert_allclose(td.time.values, epoch, atol=1e-6)
    assert_equal(dn[0], 735032.5000311028)
    
    
if __name__=='__main__':
    test_epoch2date()
    test_datetime()
    test_datenum()
        
import numpy as np
import os
from dolfyn.rotate.api import set_inst2head_rotmat
import dolfyn.io.nortek as vector
from dolfyn.io.api import read_example as read
import dolfyn.test.base as tb
from xarray.testing import assert_equal
load = tb.load_ncdata
save = tb.save_ncdata

dat = load('vector_data01.nc')
dat_imu = load('vector_data_imu01.nc')
dat_imu_json = load('vector_data_imu01-json.nc')
dat_burst = load('burst_mode01.nc')


def test_save():
    save(dat, 'test_save')
    tb.save_matlab(dat, 'test_save')
    
    assert os.path.exists(tb.rfnm('test_save.nc'))
    assert os.path.exists(tb.rfnm('test_save.mat'))


def test_read(make_data=False):
    td = read('vector_data01.VEC', nens=100)
    tdm = read('vector_data_imu01.VEC',
               userdata=False,
               nens=100)
    tdb = read('burst_mode01.VEC',
               nens=100)
    tdm2 = read('vector_data_imu01.VEC',
                userdata=tb.exdt('vector_data_imu01.userdata.json'),
                nens=100)
    td_debug = tb.drop_config(vector.read_nortek(tb.exdt('vector_data_imu01.VEC'), 
                              debug=True, do_checksum=True, nens=100))
    
    # These values are not correct for this data but I'm adding them for
    # test purposes only.
    tdm = set_inst2head_rotmat(tdm, np.eye(3))
    tdm.attrs['inst2head_vec'] = np.array([-1.0, 0.5, 0.2])

    if make_data:
        save(td, 'vector_data01.nc')
        save(tdm, 'vector_data_imu01.nc')
        save(tdb, 'burst_mode01.nc')
        save(tdm2, 'vector_data_imu01-json.nc')
        return
    
    assert_equal(td, dat)
    assert_equal(tdm, dat_imu)
    assert_equal(tdb, dat_burst)
    assert_equal(tdm2, dat_imu_json)
    assert_equal(td_debug, tdm2)
    

if __name__ == '__main__':
    test_save()
    test_read()
from dolfyn.test import test_read_adv as tv
from dolfyn.test import test_read_adp as tp
import dolfyn.adv.api as avm
from dolfyn.rotate.api import rotate2, set_declination
from dolfyn.test.base import load_ncdata as load, save_ncdata as save
import numpy as np
from xarray.testing import assert_equal, assert_allclose

def test_motion_adv(make_data=False):
    #mc = avm.motion.CorrectMotion()
    tdm = tv.dat_imu.copy(deep=True)
    tdm = avm.correct_motion(tdm)
    
    tdm10 = tv.dat_imu.copy(deep=True)
    # Include the declination.
    tdm10 = set_declination(tdm10, 10.0)
    tdm10 = avm.correct_motion(tdm10)
    
    tdm0 = tv.dat_imu.copy(deep=True)
    # Include the declination.
    tdm0 = set_declination(tdm0, 0.0)
    tdm0 = avm.correct_motion(tdm0)
    
    tdmj = tv.dat_imu_json.copy(deep=True)
    tdmj = avm.correct_motion(tdmj)

    tdmE = tv.dat_imu.copy(deep=True)
    tdmE = set_declination(tdmE, 10.0)
    tdmE = rotate2(tdmE, 'earth', inplace=True)
    tdmE = avm.correct_motion(tdmE)

    if make_data:
        save(tdm, 'vector_data_imu01_mc.nc')
        save(tdm10, 'vector_data_imu01_mcDeclin10.nc')
        save(tdmj, 'vector_data_imu01-json_mc.nc')
        return

    cdm10 = load('vector_data_imu01_mcDeclin10.nc')
    
    assert_equal(tdm, load('vector_data_imu01_mc.nc'))
    # apparently reloading this still fails assert_equal
    assert_allclose(tdm10, cdm10, atol=1e-7)
    assert_allclose(tdmE, cdm10, atol=1e-7)
    assert_allclose(tdmj, load('vector_data_imu01-json_mc.nc'), atol=1e-7)
        
    # yield data_equiv, tdm10, tdmj, \
    #     ".userdata.json motion correction does not match explicit expectations."
    assert_equal(tdm10, tdmj)

    tdm0.attrs.pop('declination')
    tdm0.attrs.pop('declination_in_orientmat')
    # yield data_equiv, tdm0, tdm, \
    #     "The data changes when declination is specified as 0!"
    assert_allclose(tdm0, tdm, atol=1e-7)
    

def test_motion_adcp():
    # Correction for ADCPs not completed yet
    tdm = tp.dat_sig_i.copy(deep=True)
    tdm = avm.set_inst2head_rotmat(tdm, rotmat=np.eye(4)) # 4th doesn't matter
    tdm.attrs['inst2head_vec'] = np.array([0,0,0,0])
    tdmc = avm.correct_motion(tdm)
    
    assert type(tdm)==type(tdmc) # simple way of making sure tdmc exists
    
if __name__=='__main__':
    test_motion_adv()
    test_motion_adcp()
    
    
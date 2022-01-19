from . import test_read_adv as tv
#from . import test_read_adp as tp
from .base import load_ncdata as load, save_ncdata as save
import dolfyn.adv.api as avm
from dolfyn.rotate.api import rotate2, set_declination
from xarray.testing import assert_allclose
#import numpy as np


def test_motion_adv(make_data=False):
    #mc = avm.correct_motion()
    tdm = tv.dat_imu.copy(deep=True)
    tdm = avm.correct_motion(tdm)

    # user added metadata
    tdmj = tv.dat_imu_json.copy(deep=True)
    tdmj = avm.correct_motion(tdmj)

    # set declination and then correct
    tdm10 = tv.dat_imu.copy(deep=True)
    tdm10 = set_declination(tdm10, 10.0)
    tdm10 = avm.correct_motion(tdm10)

    # test setting declination to 0 doesn't affect correction
    tdm0 = tv.dat_imu.copy(deep=True)
    tdm0 = set_declination(tdm0, 0.0)
    tdm0 = avm.correct_motion(tdm0)
    tdm0.attrs.pop('declination')
    tdm0.attrs.pop('declination_in_orientmat')

    # test motion-corrected data rotation
    tdmE = tv.dat_imu.copy(deep=True)
    tdmE = set_declination(tdmE, 10.0)
    tdmE = rotate2(tdmE, 'earth')
    tdmE = avm.correct_motion(tdmE)

    if make_data:
        save(tdm, 'vector_data_imu01_mc.nc')
        save(tdm10, 'vector_data_imu01_mcDeclin10.nc')
        save(tdmj, 'vector_data_imu01-json_mc.nc')
        return

    cdm10 = load('vector_data_imu01_mcDeclin10.nc')

    assert_allclose(tdm, load('vector_data_imu01_mc.nc'), atol=1e-7)
    assert_allclose(tdm10, tdmj, atol=1e-7)
    assert_allclose(tdm0, tdm, atol=1e-7)
    assert_allclose(tdm10, cdm10, atol=1e-7)
    assert_allclose(tdmE, cdm10, atol=1e-7)
    assert_allclose(tdmj, load('vector_data_imu01-json_mc.nc'), atol=1e-7)


def test_sep_probes(make_data=False):
    tdm = tv.dat_imu.copy(deep=True)
    tdm = avm.correct_motion(tdm, separate_probes=True)

    if make_data:
        save(tdm, 'vector_data_imu01_mcsp.nc')
        return

    assert_allclose(tdm, load('vector_data_imu01_mcsp.nc'), atol=1e-7)


# def test_motion_adcp():
#     # Correction for ADCPs not completed yet
#     tdm = tp.dat_sig_i.copy(deep=True)
#     tdm = avm.set_inst2head_rotmat(tdm, rotmat=np.eye(4)) # 4th doesn't matter
#     tdm.attrs['inst2head_vec'] = np.array([0,0,0,0])
#     tdmc = avm.correct_motion(tdm)

#    assert type(tdm)==type(tdmc) # simple way of making sure tdmc exists


if __name__ == '__main__':
    test_motion_adv()
    test_sep_probes()
    # test_motion_adcp()

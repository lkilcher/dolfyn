import numpy as np
import xarray as xr
from dolfyn.adv.motion import correct_motion

from dolfyn.tests import test_read_adv as tv
#from dolfyn.tests import test_read_adp as tp
from dolfyn.tests.base import load_netcdf as load, save_netcdf as save, assert_allclose, drop_config
import dolfyn.adv.api as avm
from dolfyn.io.api import read_example as read


def test_motion_adv(make_data=False):
    tdm = tv.dat_imu.copy(deep=True)
    tdm = avm.correct_motion(tdm)

    # user added metadata
    tdmj = tv.dat_imu_json.copy(deep=True)
    tdmj = avm.correct_motion(tdmj)

    # set declination and then correct
    tdm10 = tv.dat_imu.copy(deep=True)
    tdm10.velds.set_declination(10.0, inplace=True)
    tdm10 = avm.correct_motion(tdm10)

    # test setting declination to 0 doesn't affect correction
    tdm0 = tv.dat_imu.copy(deep=True)
    tdm0.velds.set_declination(0.0, inplace=True)
    tdm0 = avm.correct_motion(tdm0)
    tdm0.attrs.pop('declination')
    tdm0.attrs.pop('declination_in_orientmat')

    # test motion-corrected data rotation
    tdmE = tv.dat_imu.copy(deep=True)
    tdmE.velds.set_declination(10.0, inplace=True)
    tdmE.velds.rotate2('earth', inplace=True)
    tdmE = avm.correct_motion(tdmE)

    # ensure trailing nans are removed from AHRS data
    ahrs = drop_config(read(
        'vector_data_imu01.VEC', userdata=True))
    for var in ['accel', 'angrt', 'mag']:
        assert not ahrs[var].isnull().any(), "nan's in {} variable".format(var)

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


def test_duty_cycle():
    tdc = load('vector_duty_cycle.nc')
    tdc.velds.set_inst2head_rotmat(np.eye(3))
    tdc.attrs['inst2head_vec'] = [0.5, 0, 0.1]

    # with duty cycle code
    td = correct_motion(tdc, accel_filtfreq=0.03, to_earth=False)
    td_ENU = correct_motion(tdc, accel_filtfreq=0.03, to_earth=True)

    # Wrapped function
    n_burst = 50
    n_ensembles = len(tdc.time)//n_burst
    cd = xr.Dataset()
    tdc.attrs.pop('duty_cycle_n_burst')
    for i in range(n_ensembles):
        cd0 = tdc.isel(time=slice(n_burst*i, n_burst*i+n_burst))
        cd0 = correct_motion(cd0, accel_filtfreq=0.03, to_earth=False)
        cd = xr.merge((cd, cd0), combine_attrs='no_conflicts')
    cd.attrs['duty_cycle_n_burst'] = n_burst

    cd_ENU = cd.velds.rotate2('earth', inplace=False)

    assert_allclose(td, cd, atol=1e-7)
    assert_allclose(td_ENU, cd_ENU, atol=1e-7)

# def test_motion_adcp():
#     # Correction for ADCPs not completed yet
#     tdm = tp.dat_sig_i.copy(deep=True)
#     avm.set_inst2head_rotmat(tdm, rotmat=np.eye(4), inplace=True) # 4th doesn't matter
#     tdm.attrs['inst2head_vec'] = np.array([0,0,0,0])
#     tdmc = avm.correct_motion(tdm)

#    assert type(tdm)==type(tdmc) # simple way of making sure tdmc exists

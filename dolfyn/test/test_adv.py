import numpy as np
import dolfyn.adv.api as avm
from dolfyn.rotate.base import orient2euler
from dolfyn import read_example as read
import dolfyn.test.base as tb
from xarray.testing import assert_allclose

load = tb.load_ncdata
save = tb.save_ncdata

dat = load('vector_data01.nc')
dat_imu = load('vector_data_imu01.nc')
dat_imu_json = load('vector_data_imu01-json.nc')
dat_burst = load('burst_mode01.nc')


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
    
    # These values are not correct for this data but I'm adding them for
    # test purposes only.
    tdm = tdm.Veldata.set_inst2head_rotmat(np.eye(3))
    tdm.attrs['inst2head_vec'] = np.array([-1.0, 0.5, 0.2])

    if make_data:
        save(td, 'vector_data01.nc')
        save(tdm, 'vector_data_imu01.nc')
        save(tdb, 'burst_mode01.nc')
        save(tdm2, 'vector_data_imu01-json.nc')
        return
    
    assert_allclose(td, dat)
    assert_allclose(tdm, dat_imu)
    assert_allclose(tdb, dat_burst)
    assert_allclose(tdm2, dat_imu_json)


def test_motion(make_data=False):
    #mc = avm.motion.CorrectMotion()
    tdm = dat_imu.copy(deep=True)
    tdm = avm.correct_motion(tdm)
    
    tdm10 = dat_imu.copy(deep=True)
    # Include the declination.
    tdm10 = tdm10.Veldata.set_declination(10.0)
    tdm10 = avm.correct_motion(tdm10)
    
    tdm0 = dat_imu.copy(deep=True)
    # Include the declination.
    tdm0 = tdm0.Veldata.set_declination(0.0)
    tdm0 = avm.correct_motion(tdm0)
    
    tdmj = dat_imu_json.copy(deep=True)
    tdmj = avm.correct_motion(tdmj)

    tdmE = dat_imu.copy(deep=True)
    tdmE = tdmE.Veldata.set_declination(10.0)
    tdmE = tdmE.Veldata.rotate2('earth', inplace=True)
    tdmE = avm.correct_motion(tdmE)

    if make_data:
        save(tdm, 'vector_data_imu01_mc.nc')
        save(tdm10, 'vector_data_imu01_mcDeclin10.nc')
        save(tdmj, 'vector_data_imu01-json_mc.nc')
        return

    cdm10 = load('vector_data_imu01_mcDeclin10.nc')
    
    assert_allclose(tdm, load('vector_data_imu01_mc.nc'))
    assert_allclose(tdm10, cdm10)
    assert_allclose(tdmE, cdm10, rtol=1e-7, atol=1e-3)
    assert_allclose(tdmj, load('vector_data_imu01-json_mc.nc'))
        
    # yield data_equiv, tdm10, tdmj, \
    #     ".userdata.json motion correction does not match explicit expectations."
    assert_allclose(tdm10, tdmj, rtol=1e-7, atol=1e-3)

    tdm0.attrs.pop('declination')
    tdm0.attrs.pop('declination_in_orientmat')
    # yield data_equiv, tdm0, tdm, \
    #     "The data changes when declination is specified as 0!"
    assert_allclose(tdm0, tdm, rtol=1e-7, atol=1e-3)


def test_heading(make_data=False):
    td = dat_imu.copy(deep=True)

    head, pitch, roll = orient2euler(td)
    td['pitch'].values = pitch
    td['roll'].values = roll
    td['heading'].values = head

    if make_data:
        save(td, 'vector_data_imu01_head_pitch_roll.nc')
        return

    cd = load('vector_data_imu01_head_pitch_roll.nc')

    #assert td == cd, "adv.rotate.orient2euler gives unexpected results!"
    assert_allclose(td, cd)
    

def test_turbulence(make_data=False):
    tmp = dat.copy(deep=True)
    bnr = avm.TurbBinner(n_bin=20.0, fs=tmp.fs)
    td = bnr(tmp)

    if make_data:
        save(td, 'vector_data01_bin.nc')
        return

    cd = load('vector_data01_bin.nc')

    #assert cd == td, "TurbBinner gives unexpected results!"
    assert_allclose(td, cd)
    

def test_clean(make_data=False):
    td = dat.copy(deep=True)
    td['vel'].values[0] = avm.clean.GN2002(td.Veldata.u, 20)

    if make_data:
        save(td, 'vector_data01_uclean.nc')
        return

    cd = load('vector_data01_uclean.nc')

    #assert cd == td, "adv.clean.GN2002 gives unexpected results!"
    assert_allclose(td, cd)


if __name__ == '__main__':
    test_read()
    test_motion()
    test_heading()
    test_turbulence()
    test_clean()

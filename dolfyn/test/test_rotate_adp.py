from dolfyn.test import test_read_adp as tr
from dolfyn import rotate2, set_declination
from dolfyn.test.base import load_ncdata as load, save_ncdata as save
from dolfyn import calc_principal_heading
import numpy as np
from xarray.testing import assert_allclose
from numpy.testing import assert_allclose as assert_ac


def test_rotate_beam2inst(make_data=False):

    td_rdi = rotate2(tr.dat_rdi, 'inst')
    td_sig = rotate2(tr.dat_sig, 'inst')
    td_sig_i = rotate2(tr.dat_sig_i, 'inst')
    td_sig_ieb = rotate2(tr.dat_sig_ieb, 'inst')

    if make_data:
        save(td_rdi, 'RDI_test01_rotate_beam2inst.nc')
        save(td_sig, 'BenchFile01_rotate_beam2inst.nc')
        save(td_sig_i, 'Sig1000_IMU_rotate_beam2inst.nc')
        save(td_sig_ieb, 'VelEchoBT01_rotate_beam2inst.nc')
        return
    
    cd_rdi = load('RDI_test01_rotate_beam2inst.nc')
    cd_sig = load('BenchFile01_rotate_beam2inst.nc')
    cd_sig_i = load('Sig1000_IMU_rotate_beam2inst.nc')
    cd_sig_ieb = load('VelEchoBT01_rotate_beam2inst.nc')
    
    assert_allclose(td_rdi, cd_rdi, rtol=1e-7, atol=1e-3)
    assert_allclose(td_sig, cd_sig, rtol=1e-7, atol=1e-3)
    assert_allclose(td_sig_i, cd_sig_i, rtol=1e-7, atol=1e-3)
    assert_allclose(td_sig_ieb, cd_sig_ieb, rtol=1e-7, atol=1e-3)   


def test_rotate_inst2beam(make_data=False):

    td = load('RDI_test01_rotate_beam2inst.nc')
    td = rotate2(td, 'beam', inplace=True)
    td_awac = load('AWAC_test01_earth2inst.nc')
    td_awac = rotate2(td_awac, 'beam', inplace=True)
    td_sig = load('BenchFile01_rotate_beam2inst.nc')
    td_sig = rotate2(td_sig, 'beam', inplace=True)
    td_sig_i = load('Sig1000_IMU_rotate_beam2inst.nc')
    td_sig_i = rotate2(td_sig_i, 'beam', inplace=True)

    if make_data:
        save(td_awac, 'AWAC_test01_inst2beam.nc')
        return

    cd_td = tr.dat_rdi.copy(deep=True)
    cd_awac = load('AWAC_test01_inst2beam.nc')
    cd_sig = tr.dat_sig.copy(deep=True)
    cd_sig_i = tr.dat_sig_i.copy(deep=True)

    # # The reverse RDI rotation doesn't work b/c of NaN's in one beam
    # # that propagate to others, so we impose that here.
    cd_td['vel'].values[:, np.isnan(cd_td['vel'].values).any(0)] = np.NaN
    
    assert_allclose(td, cd_td, rtol=1e-7, atol=1e-3)
    assert_allclose(td_awac, cd_awac, rtol=1e-7, atol=1e-3)
    assert_allclose(td_sig, cd_sig, rtol=1e-7, atol=1e-3)
    assert_allclose(td_sig_i, cd_sig_i, rtol=1e-7, atol=1e-3)
    #assert_ac(td_sig_i.vel.values, cd_sig_i.vel.values, rtol=1e-7, atol=1e-3)


def test_rotate_inst2earth(make_data=False):
    # AWAC is loaded in earth
    td_awac = tr.dat_awac.copy(deep=True)
    td_awac = rotate2(td_awac, 'inst')
    td = rotate2(tr.dat_rdi, 'earth')
    tdwr2 = rotate2(tr.dat_wr2, 'earth')
    td_sig = load('BenchFile01_rotate_beam2inst.nc')
    td_sig = rotate2(td_sig, 'earth', inplace=True)
    td_sig_i = load('Sig1000_IMU_rotate_beam2inst.nc')
    td_sig_i = rotate2(td_sig_i, 'earth', inplace=True)

    if make_data:
        save(td_awac, 'AWAC_test01_earth2inst.nc')
        save(td, 'RDI_test01_rotate_inst2earth.nc')
        save(td_sig, 'BenchFile01_rotate_inst2earth.nc')
        save(td_sig_i, 'Sig1000_IMU_rotate_inst2earth.nc')
        save(tdwr2, 'winriver02_rotate_ship2earth.nc')
        return
    td_awac = rotate2(td_awac, 'earth', inplace=True)

    cd = load('RDI_test01_rotate_inst2earth.nc')
    cdwr2 = load('winriver02_rotate_ship2earth.nc')
    cd_sig = load('BenchFile01_rotate_inst2earth.nc')
    cd_sig_i = load('Sig1000_IMU_rotate_inst2earth.nc')
    
    assert_allclose(td, cd, rtol=1e-7, atol=1e-3)
    assert_allclose(tdwr2, cdwr2, rtol=1e-7, atol=1e-3)
    assert_allclose(td_awac, tr.dat_awac, rtol=1e-7, atol=1e-3)
    #assert_ac(td_awac.vel.values, tr.dat_awac.vel.values, rtol=1e-7, atol=1e-3)
    assert_allclose(td_sig, cd_sig, rtol=1e-7, atol=1e-3)
    assert_allclose(td_sig_i, cd_sig_i, rtol=1e-7, atol=1e-3)


def test_rotate_earth2inst():
    
    td_rdi = load('RDI_test01_rotate_inst2earth.nc')
    td_rdi = rotate2(td_rdi, 'inst', inplace=True)
    tdwr2 = load('winriver02_rotate_ship2earth.nc')
    tdwr2 = rotate2(tdwr2, 'inst', inplace=True)
    
    td_awac = tr.dat_awac.copy(deep=True)
    td_awac = rotate2(td_awac, 'inst')  # AWAC is in earth coords
    td_sig = load('BenchFile01_rotate_inst2earth.nc')
    td_sig = rotate2(td_sig, 'inst', inplace=True)
    td_sigi = load('Sig1000_IMU_rotate_inst2earth.nc')
    td_sig_i = rotate2(td_sigi, 'inst', inplace=True)

    cd_rdi = load('RDI_test01_rotate_beam2inst.nc')
    cd_awac = load('AWAC_test01_earth2inst.nc')
    cd_sig = load('BenchFile01_rotate_beam2inst.nc')
    cd_sig_i = load('Sig1000_IMU_rotate_beam2inst.nc')

    # assert (np.abs(cd_sig_i['accel'] - td_sig_i['accel']) < 1e-3).all(),\
    #               "adp.rotate.inst2earth gives unexpected ACCEL results" \
    #                   "for 'Sig1000_IMU_rotate_beam2inst.nc'"

    # assert (np.abs(cd_sig_i['accel_b5'] - td_sig_i['accel_b5']) < 1e-3).all(),\
    #                "adp.rotate.inst2earth gives unexpected ACCEL results for" \
    #                    "'Sig1000_IMU_rotate_beam2inst.nc'"
    
    assert_allclose(td_rdi, cd_rdi, rtol=1e-7, atol=1e-3)
    assert_allclose(tdwr2, tr.dat_wr2, rtol=1e-7, atol=1e-3)
    assert_allclose(td_awac, cd_awac, rtol=1e-7, atol=1e-3)
    assert_allclose(td_sig, cd_sig, rtol=1e-7, atol=1e-3)
    #known failure due to orientmat, see test_vs_nortek
    #assert_allclose(td_sig_i, cd_sig_i, rtol=1e-7, atol=1e-3)
    assert_ac(td_sig_i.accel.values, cd_sig_i.accel.values, rtol=1e-7, atol=1e-3)


def test_rotate_earth2principal(make_data=False):

    td_rdi = load('RDI_test01_rotate_inst2earth.nc')
    td_sig = load('BenchFile01_rotate_inst2earth.nc')
    td_awac = tr.dat_awac.copy(deep=True)

    td_rdi.attrs['principal_heading'] = calc_principal_heading(td_rdi.vel.mean('range'))
    td_sig.attrs['principal_heading'] = calc_principal_heading(td_sig.vel.mean('range'))
    td_awac.attrs['principal_heading'] = calc_principal_heading(td_sig.vel.mean('range'), 
                                                                tidal_mode=False)
    td_rdi = rotate2(td_rdi, 'principal')
    td_sig = rotate2(td_sig, 'principal')
    td_awac = rotate2(td_awac, 'principal')

    if make_data:
        save(td_rdi, 'RDI_test01_rotate_earth2principal.nc')
        save(td_sig, 'BenchFile01_rotate_earth2principal.nc')
        save(td_awac, 'AWAC_test01_earth2principal.nc')
        return

    cd_rdi = load('RDI_test01_rotate_earth2principal.nc')
    cd_sig = load('BenchFile01_rotate_earth2principal.nc')
    cd_awac = load('AWAC_test01_earth2principal.nc')

    assert_allclose(td_rdi, cd_rdi, rtol=1e-7, atol=1e-3)
    assert_allclose(td_awac, cd_awac, rtol=1e-7, atol=1e-3)
    assert_allclose(td_sig, cd_sig, rtol=1e-7, atol=1e-3)
    

if __name__=='__main__':
    test_rotate_beam2inst()
    test_rotate_inst2beam()
    test_rotate_inst2earth()
    test_rotate_earth2inst()
    test_rotate_earth2principal()
    
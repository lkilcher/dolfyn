from dolfyn.tests import test_read_adp as tr, test_read_adv as tv
from dolfyn.tests.base import load_netcdf as load, save_netcdf as save, assert_allclose
from dolfyn import VelBinner, read_example
import dolfyn.adv.api as avm
from xarray.testing import assert_identical
import numpy as np
import pytest


class adv_setup():
    def __init__(self, tv):
        self.dat1 = tv.dat.copy(deep=True)
        self.dat2 = read_example('burst_mode01.VEC', nens=90)
        fs = self.dat1.fs
        self.avg_tool = VelBinner(n_bin=fs, fs=fs)


class adp_setup():
    def __init__(self, tr):
        self.dat = tr.dat_sig.copy(deep=True)
        fs = self.dat.fs
        with pytest.warns(UserWarning):
            self.avg_tool = VelBinner(n_bin=fs*20, fs=fs, n_fft=fs*40)


def test_do_func(make_data=False):
    dat_vec = adv_setup(tv)
    adat_vec = dat_vec.avg_tool.do_avg(dat_vec.dat1)
    adat_vec = dat_vec.avg_tool.do_var(dat_vec.dat1, adat_vec)

    dat_sig = adp_setup(tr)
    adat_sig = dat_sig.avg_tool.do_avg(dat_sig.dat)
    adat_sig = dat_sig.avg_tool.do_var(dat_sig.dat, adat_sig)

    if make_data:
        save(adat_vec, 'vector_data01_avg.nc')
        save(adat_sig, 'BenchFile01_avg.nc')
        return

    assert_allclose(adat_vec, load('vector_data01_avg.nc'), atol=1e-6)
    assert_allclose(adat_sig, load('BenchFile01_avg.nc'), atol=1e-6)


def test_calc_func(make_data=False):
    dat_vec = adv_setup(tv)
    test_ds = type(dat_vec.dat1)()
    test_ds_demean = type(dat_vec.dat1)()
    test_ds_dif = type(dat_vec.dat1)()
    c = dat_vec.avg_tool

    dat_adp = adp_setup(tr)
    c2 = dat_adp.avg_tool
    test_ds_adp = type(dat_adp.dat)()

    test_ds['coh'] = c.calc_coh(
        dat_vec.dat1.vel[0], dat_vec.dat1.vel[1], n_fft_coh=dat_vec.dat1.fs)
    test_ds['pang'] = c.calc_phase_angle(
        dat_vec.dat1.vel[0], dat_vec.dat1.vel[1], n_fft_coh=dat_vec.dat1.fs)
    test_ds['xcov'] = c.calc_xcov(dat_vec.dat1.vel[0], dat_vec.dat1.vel[1])
    test_ds['acov'] = c.calc_acov(dat_vec.dat1.vel)
    test_ds['tke_vec'] = c.calc_tke(dat_vec.dat1.vel)
    test_ds_demean['tke_vec'] = c.calc_tke(dat_vec.dat1.vel, detrend=False)
    test_ds['psd'] = c.calc_psd(dat_vec.dat1.vel)

    # Different lengths
    test_ds_dif['coh_dif'] = c.calc_coh(
        dat_vec.dat1.vel, dat_vec.dat2.vel)
    test_ds_dif['pang_dif'] = c.calc_phase_angle(
        dat_vec.dat1.vel, dat_vec.dat2.vel)

    # Test ADCP single vector spectra, cross-spectra to test radians code
    test_ds_adp['psd_b5'] = c2.calc_psd(
        dat_adp.dat.vel_b5.isel(range_b5=5), window='hamm')
    test_ds_adp['tke_b5'] = c2.calc_tke(dat_adp.dat.vel_b5)

    if make_data:
        save(test_ds, 'vector_data01_func.nc')
        save(test_ds_dif, 'vector_data01_funcdif.nc')
        save(test_ds_demean, 'vector_data01_func_demean.nc')
        save(test_ds_adp, 'BenchFile01_func.nc')
        return

    assert_allclose(test_ds, load('vector_data01_func.nc'), atol=1e-6)
    assert_allclose(test_ds_dif, load('vector_data01_funcdif.nc'), atol=1e-6)
    assert_allclose(test_ds_demean, load(
        'vector_data01_func_demean.nc'), atol=1e-6)
    assert_allclose(test_ds_adp, load('BenchFile01_func.nc'), atol=1e-6)


def test_calc_freq():
    dat_vec = adv_setup(tv)

    f = dat_vec.avg_tool.calc_freq(units='Hz')
    omega = dat_vec.avg_tool.calc_freq(units='rad/s')

    np.testing.assert_equal(f, np.arange(1, 17, 1, dtype='float'))
    np.testing.assert_equal(omega, np.arange(
        1, 17, 1, dtype='float')*(2*np.pi))


def test_adv_turbulence(make_data=False):
    dat = tv.dat.copy(deep=True)
    bnr = avm.ADVBinner(n_bin=20.0, fs=dat.fs)
    tdat = bnr(dat)
    acov = bnr.calc_acov(dat.vel)

    assert_identical(tdat, avm.calc_turbulence(dat, n_bin=20.0, fs=dat.fs))

    tdat['stress'] = bnr.calc_stress(dat.vel)
    tdat['stress_detrend'] = bnr.calc_stress(dat.vel, detrend=False)
    tdat['csd'] = bnr.calc_csd(dat.vel, freq_units='rad', window='hamm')
    tdat['LT83'] = bnr.calc_epsilon_LT83(tdat.psd, tdat.velds.U_mag)
    tdat['SF'] = bnr.calc_epsilon_SF(dat.vel[0], tdat.velds.U_mag)
    tdat['TE01'] = bnr.calc_epsilon_TE01(dat, tdat)
    tdat['L'] = bnr.calc_L_int(acov, tdat.velds.U_mag)

    if make_data:
        save(tdat, 'vector_data01_bin.nc')
        return

    assert_allclose(tdat, load('vector_data01_bin.nc'), atol=1e-6)

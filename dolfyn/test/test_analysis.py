from dolfyn.test import test_read_adp as tr, test_read_adv as tv
from dolfyn.test.base import load_ncdata as load, save_ncdata as save
from xarray.testing import assert_equal, assert_allclose
import numpy as np
from dolfyn import VelBinner, read_example
import dolfyn.adv.api as avm

class adv_setup():
    def __init__(self, tv):
        self.dat1 = tv.dat.copy(deep=True)
        self.dat2 = tv.dat_imu.copy(deep=True)
        self.dat3 = read_example('burst_mode01.VEC', nens=200)
        self.avg_tool = VelBinner(self.dat1.fs, self.dat1.fs)
        
class adp_setup():
    def __init__(self, tr):
        self.dat = tr.dat_sig.copy(deep=True)
        self.avg_tool = VelBinner(self.dat.fs*20, self.dat.fs)
        
        
# test each of VelBinner's functions on an ADV and ADCP
def test_do_avg(make_data=False):
    dat_vec = adv_setup(tv)
    adat_vec = dat_vec.avg_tool.do_avg(dat_vec.dat1)
    
    dat_sig = adp_setup(tr)
    adat_sig = dat_sig.avg_tool.do_avg(dat_sig.dat)
    
    if make_data:
        save(adat_vec, 'ADV_average.nc')
        save(adat_sig, 'ADCP_average.nc')
        return
    
    assert_equal(adat_vec, load('ADV_average.nc'))
    assert_equal(adat_sig, load('ADCP_average.nc'))
    
    
def test_do_var(make_data=False):
    dat_vec = adv_setup(tv)
    vdat_vec = dat_vec.avg_tool.do_var(dat_vec.dat1)
    
    dat_sig = adp_setup(tr)
    vdat_sig = dat_sig.avg_tool.do_var(dat_sig.dat)
    
    if make_data:
        save(vdat_vec, 'ADV_variance.nc')
        save(vdat_sig, 'ADCP_variance.nc')
        return 
    
    assert_equal(vdat_vec, load('ADV_variance.nc'))
    assert_equal(vdat_sig, load('ADCP_variance.nc'))
    
    
def test_calc_coh(make_data=False):
    dat_vec = adv_setup(tv)
    coh = type(dat_vec.dat1)()
    # about same size
    coh['same'] = dat_vec.avg_tool.calc_coh(dat_vec.dat1.vel, dat_vec.dat2.vel)
    # larger one should come first if dif lengths
    coh['dif'] = dat_vec.avg_tool.calc_coh(dat_vec.dat3.vel, dat_vec.dat1.vel)
    
    if make_data:
        save(coh, 'coherence.nc')
        return
    
    saved_coh = load('coherence.nc')
    
    assert_equal(coh['same'], saved_coh['same'])
    assert_equal(coh['dif'], saved_coh['dif'])
    
    
def test_calc_phase_angle(make_data=False):
    dat_vec = adv_setup(tv)
    pang = type(dat_vec.dat1)()
    pang['same'] = dat_vec.avg_tool.calc_phase_angle(dat_vec.dat1.vel,
                                                     dat_vec.dat2.vel)
    pang['dif'] = dat_vec.avg_tool.calc_phase_angle(dat_vec.dat3.vel,
                                                    dat_vec.dat1.vel)
    if make_data:
        save(pang, 'phase_angle.nc')
        return
    
    saved_pang = load('phase_angle.nc')
    
    assert_equal(pang['same'], saved_pang['same'])
    assert_equal(pang['dif'], saved_pang['dif'])
    
    
def test_calc_acov(make_data=False):
    dat_vec = adv_setup(tv)
    acov = dat_vec.avg_tool.calc_acov(dat_vec.dat1.vel)
    
    if make_data:
        save(acov, 'auto-cov.nc')
        return
    saved_acov = load('auto-cov.nc')
    
    assert_allclose(acov, saved_acov['auto-covariance'], atol=1e-7)
    
    
def test_calc_xcov(make_data=False):
    dat_vec = adv_setup(tv)
    xcov = dat_vec.avg_tool.calc_xcov(dat_vec.dat1.vel, dat_vec.dat2.vel)
    
    if make_data:
        save(xcov, 'cross-cov.nc')
        return
    saved_xcov = load('cross-cov.nc')
    
    assert_equal(xcov, saved_xcov['cross-covariance'])
    
     
def test_calc_tke(make_data=False):
    dat_vec = adv_setup(tv)
    tke = dat_vec.avg_tool.calc_tke(dat_vec.dat1.vel)
    
    if make_data:
        save(tke, 'tke_vector.nc')
        return
    saved_tke = load('tke_vector.nc')
    
    assert_equal(tke, saved_tke.tke_vec)
    
    
def test_calc_stress(make_data=False):
    dat_vec = adv_setup(tv)
    stress = dat_vec.avg_tool.calc_stress(dat_vec.dat1.vel)
    
    if make_data:
        save(stress, 'stress_vector.nc')
        return
    saved_stress = load('stress_vector.nc')
    
    assert_equal(stress, saved_stress.stress_vec)
    
    
def test_do_tke(make_data=False):
    dat_vec = adv_setup(tv)
    adat = dat_vec.avg_tool.do_avg(dat_vec.dat1)
    tkedat = dat_vec.avg_tool.do_tke(adat, out_ds=adat)
    
    if make_data:
        save(tkedat, 'ADV_avg+tke.nc')
        return
    saved_tkedat = load('ADV_avg+tke.nc')
    
    assert_equal(tkedat, saved_tkedat)
    
    
def test_calc_freq(make_data=False):
    dat_vec = adv_setup(tv)
    
    f = dat_vec.avg_tool.calc_freq(units='Hz')
    omega = dat_vec.avg_tool.calc_freq(units='rad/s')
    
    np.testing.assert_equal(f, np.arange(1, 17, 1, dtype='float'))
    np.testing.assert_equal(omega, np.arange(1, 17, 1, dtype='float')*(2*np.pi))
    
    
def test_calc_vel_psd(make_data=False):
    dat_vec = adv_setup(tv)    
    spec = dat_vec.avg_tool.calc_vel_psd(dat_vec.dat1.vel)
    
    if make_data:
        save(spec, 'spectra.nc')
        return
    saved_spec = load('spectra.nc')
    
    assert_equal(spec, saved_spec.S)
    
    
def test_calc_vel_csd(make_data=False):
    dat_vec = adv_setup(tv)    
    cspec = dat_vec.avg_tool.calc_vel_csd(dat_vec.dat1.vel)
    
    if make_data:
        save(cspec, 'cross-spectra.nc')
        return
    saved_cspec = load('cross-spectra.nc')
    
    assert_equal(cspec, saved_cspec.csd)


# test each of TurbBinner's functions on an ADV
def test_calc_turbulence(make_data=False):
    dat = tv.dat
    tdat = avm.calc_turbulence(dat, n_bin=20.0, fs=dat.fs)
    
    if make_data:
        save(tdat, 'turb_data.nc')
        return
    saved_tdat = load('turb_data.nc')
    
    assert_equal(tdat, saved_tdat)
    
    
def test_calc_epsilon(make_data=False):
    dat = tv.dat
    bnr = avm.TurbBinner(n_bin=20.0, fs=dat.fs)
    tdat = bnr(dat)
    
    tdat['LT83'] = bnr.calc_epsilon_LT83(tdat.S, tdat.Veldata.U_mag)
    tdat['SF'] = bnr.calc_epsilon_SF(dat.vel[0], tdat.Veldata.U_mag)
    tdat['TE01'] = bnr.calc_epsilon_TE01(dat, tdat)
    
    if make_data:
        save(tdat, 'vector_data01_bin.nc')
        return
    
    saved_tdat = load('vector_data01_bin.nc')
    
    assert_equal(tdat, saved_tdat)
    assert_equal(tdat['LT83'], saved_tdat['LT83'])
    assert_equal(tdat['SF'], saved_tdat['SF'])
    assert_equal(tdat['TE01'], saved_tdat['TE01'])
    
    
def test_calc_L_int(make_data=False):
    dat = tv.dat.copy(deep=True)
    bnr = avm.TurbBinner(n_bin=20.0, fs=dat.fs)
    tdat = bnr(dat)
    acov = bnr.calc_acov(dat.vel)
    
    L = bnr.calc_L_int(acov, tdat.vel)
    
    if make_data:
        save(L, 'length_scales.nc')
        return
    saved_L = load('length_scales.nc')
    
    assert_equal(L, saved_L.L_int)

# class warnings_testcase(unittest.TestCase):
#     def test_read_warnings(self):
#         with self.assertRaises(Exception):
#             wh.read_rdi(tb.exdt('H-AWAC_test01.wpr'))
#         with self.assertRaises(Exception):
#             awac.read_nortek(tb.exdt('BenchFile01.ad2cp'))
#         with self.assertRaises(Exception):
#             sig.read_signature(tb.exdt('AWAC_test01.wpr'))
    
if __name__ == '__main__':
    test_do_avg()
    test_do_var()
    test_calc_coh()
    test_calc_phase_angle()
    test_calc_acov()
    test_calc_xcov()
    test_calc_tke()
    test_calc_stress()
    test_do_tke()
    test_calc_freq()
    test_calc_vel_psd()
    test_calc_vel_csd()
    test_calc_turbulence()
    test_calc_epsilon()
    test_calc_L_int()
    
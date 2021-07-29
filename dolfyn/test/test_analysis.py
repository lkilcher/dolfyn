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
    
    
def test_do_tke(make_data=False):
    dat_vec = adv_setup(tv)
    adat = dat_vec.avg_tool.do_avg(dat_vec.dat1)
    tkedat = dat_vec.avg_tool.do_tke(adat, out_ds=adat)
    
    if make_data:
        save(tkedat, 'ADV_avg+tke.nc')
        return
    
    assert_equal(tkedat, load('ADV_avg+tke.nc'))
    

def test_calc_func(make_data=False):
    dat_vec = adv_setup(tv)
    test_ds = type(dat_vec.dat1)()
    c = dat_vec.avg_tool
    
    # about same size
    test_ds['coh_same'] = c.calc_coh(dat_vec.dat1.vel, dat_vec.dat2.vel)
    test_ds['pang_same'] = c.calc_phase_angle(dat_vec.dat1.vel, dat_vec.dat2.vel)
    
    # larger one should come first if dif lengths
    test_ds['coh_dif'] = c.calc_coh(dat_vec.dat3.vel, dat_vec.dat1.vel)
    test_ds['pang_dif'] = c.calc_phase_angle(dat_vec.dat3.vel, dat_vec.dat1.vel)
    
    # the rest
    test_ds['acov'] = c.calc_acov(dat_vec.dat1.vel)
    test_ds['xcov'] = c.calc_xcov(dat_vec.dat1.vel, dat_vec.dat2.vel)
    test_ds['tke_vec'] = c.calc_tke(dat_vec.dat1.vel)
    test_ds['stress_vec'] = c.calc_stress(dat_vec.dat1.vel)
    test_ds['S'] = c.calc_vel_psd(dat_vec.dat1.vel)
    test_ds['cspec'] = c.calc_vel_csd(dat_vec.dat1.vel)
    
    if make_data:
        save(test_ds, 'test_analysis.nc')
        return
    
    assert_allclose(test_ds, load('test_analysis'), atol=1e-6)


def test_calc_freq(make_data=False):
    dat_vec = adv_setup(tv)
    
    f = dat_vec.avg_tool.calc_freq(units='Hz')
    omega = dat_vec.avg_tool.calc_freq(units='rad/s')
    
    np.testing.assert_equal(f, np.arange(1, 17, 1, dtype='float'))
    np.testing.assert_equal(omega, np.arange(1, 17, 1, dtype='float')*(2*np.pi))
    
    
# test each of TurbBinner's functions on an ADV
def test_calc_turbulence(make_data=False):
    dat = tv.dat
    tdat = avm.calc_turbulence(dat, n_bin=20.0, fs=dat.fs)
    
    if make_data:
        save(tdat, 'turb_data.nc')
        return
    
    assert_equal(tdat, load('turb_data.nc'))
    
    
def test_turb_bin(make_data=False):
    dat = tv.dat
    bnr = avm.TurbBinner(n_bin=20.0, fs=dat.fs)
    tdat = bnr(dat)
    acov = bnr.calc_acov(dat.vel)
    
    tdat['LT83'] = bnr.calc_epsilon_LT83(tdat.S, tdat.Veldata.U_mag)
    tdat['SF'] = bnr.calc_epsilon_SF(dat.vel[0], tdat.Veldata.U_mag)
    tdat['TE01'] = bnr.calc_epsilon_TE01(dat, tdat)
    tdat['L'] = bnr.calc_L_int(acov, tdat.vel)
    
    if make_data:
        save(tdat, 'vector_data01_bin.nc')
        return
    
    assert_equal(tdat, load('vector_data01_bin.nc'))

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
    test_do_tke()
    test_calc_freq()
    test_calc_turbulence()
    test_turb_bin()
    
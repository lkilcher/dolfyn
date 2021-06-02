from dolfyn.test import test_adv as tv
from dolfyn.test.base import load_ncdata as load, save_ncdata as save
from xarray.testing import assert_allclose
import xarray as xr
import dolfyn.adv.api as avm

class adv_setup():
    def __init__(self, tv):
        self.dat = tv.dat
        self.tdat = avm.calc_turbulence(self.dat, n_bin=20.0, fs=self.dat.fs)
        
        short = xr.Dataset()
        short['u'] = self.tdat.Veldata.u
        short['v'] = self.tdat.Veldata.v
        short['w'] = self.tdat.Veldata.w
        short['U'] = self.tdat.Veldata.U
        short['U_mag'] = self.tdat.Veldata.U_mag
        short['U_dir'] = self.tdat.Veldata.U_dir
        short['tke'] = self.tdat.Veldata.tke
        short['I'] = self.tdat.Veldata.I
        short['tau_ij'] = self.tdat.Veldata.tau_ij
        short['E_coh'] = self.tdat.Veldata.E_coh
        short['I_tke'] = self.tdat.Veldata.I_tke
        short['k'] = self.tdat.Veldata.k
        self.short = short

def test_shortcuts(make_data=False):
    test_dat = adv_setup(tv)
    
    if make_data:
        save(test_dat.short, 'shortcuts')
        return
    saved_short = load('shortcuts.nc')
    
    assert_allclose(test_dat.short.u, saved_short.u, atol=1e-5)
    assert_allclose(test_dat.short.v, saved_short.v, atol=1e-5)
    assert_allclose(test_dat.short.w, saved_short.w, atol=1e-5)
    assert_allclose(test_dat.short.U, saved_short.U, atol=1e-5)
    assert_allclose(test_dat.short.U_mag, saved_short.U_mag, atol=1e-5)
    assert_allclose(test_dat.short.U_dir, saved_short.U_dir, atol=1e-5)
    assert_allclose(test_dat.short.tke, saved_short.tke, atol=1e-5)
    assert_allclose(test_dat.short.I, saved_short.I, atol=1e-5)
    assert_allclose(test_dat.short.tau_ij, saved_short.tau_ij, atol=1e-5)
    assert_allclose(test_dat.short.E_coh, saved_short.E_coh, atol=1e-5)
    assert_allclose(test_dat.short.I_tke, saved_short.I_tke, atol=1e-5)
    assert_allclose(test_dat.short.k, saved_short.k, atol=1e-5)
        
        
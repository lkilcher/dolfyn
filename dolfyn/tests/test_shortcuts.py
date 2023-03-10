from dolfyn.tests import test_read_adv as tv
from dolfyn.tests.base import load_netcdf as load, save_netcdf as save, rfnm
from dolfyn import rotate2
import dolfyn.adv.api as avm
from xarray.testing import assert_allclose
import xarray as xr
import os


class adv_setup():
    def __init__(self, tv):
        dat = tv.dat.copy(deep=True)
        self.dat = rotate2(dat, 'earth', inplace=False)
        self.tdat = avm.calc_turbulence(self.dat, n_bin=20.0, fs=self.dat.fs)

        short = xr.Dataset()
        short['u'] = self.tdat.velds.u
        short['v'] = self.tdat.velds.v
        short['w'] = self.tdat.velds.w
        short['U'] = self.tdat.velds.U
        short['U_mag'] = self.tdat.velds.U_mag
        short['U_dir'] = self.tdat.velds.U_dir
        short["upup_"] = self.tdat.velds.upup_
        short["vpvp_"] = self.tdat.velds.vpvp_
        short["wpwp_"] = self.tdat.velds.wpwp_
        short["upvp_"] = self.tdat.velds.upvp_
        short["upwp_"] = self.tdat.velds.upwp_
        short["vpwp_"] = self.tdat.velds.vpwp_
        short['tke'] = self.tdat.velds.tke
        short['I'] = self.tdat.velds.I
        short['E_coh'] = self.tdat.velds.E_coh
        short['I_tke'] = self.tdat.velds.I_tke
        self.short = short


def test_shortcuts(make_data=False):
    td = adv_setup(tv)

    if make_data:
        save(td.short, 'vector_data01_u.nc')
        return

    assert_allclose(td.short, load('vector_data01_u.nc'), atol=1e-6)


def test_save_complex_data():
    test_dat = adv_setup(tv)
    save(test_dat.short, 'test_save.nc')

    assert os.path.exists(rfnm('test_save.nc'))

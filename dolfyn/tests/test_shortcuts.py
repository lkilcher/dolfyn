from dolfyn.tests import test_read_adv as tv
from dolfyn.tests.base import load_ncdata as load, save_ncdata as save
from dolfyn import rotate2
from xarray.testing import assert_allclose
import xarray as xr
import dolfyn.adv.api as avm


class adv_setup():
    def __init__(self, tv):
        dat = tv.dat.copy(deep=True)
        self.dat = rotate2(dat, 'earth')
        self.tdat = avm.calc_turbulence(self.dat, n_bin=20.0, fs=self.dat.fs)

        short = xr.Dataset()
        short['u'] = self.tdat.Veldata.u
        short['v'] = self.tdat.Veldata.v
        short['w'] = self.tdat.Veldata.w
        short['U'] = self.tdat.Veldata.U
        short['U_mag'] = self.tdat.Veldata.U_mag
        short['U_dir'] = self.tdat.Veldata.U_dir
        short['U_dir_N'] = self.dat.Veldata.U_dir
        short["upup_"] = self.tdat.Veldata.upup_
        short["vpvp_"] = self.tdat.Veldata.vpvp_
        short["wpwp_"] = self.tdat.Veldata.wpwp_
        short["upvp_"] = self.tdat.Veldata.upvp_
        short["upwp_"] = self.tdat.Veldata.upwp_
        short["vpwp_"] = self.tdat.Veldata.vpwp_
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
        save(test_dat.short, 'vector_data01_u.nc')
        return

    assert_allclose(test_dat.short, load('vector_data01_u.nc'), atol=1e-6)


if __name__ == '__main__':
    test_shortcuts()

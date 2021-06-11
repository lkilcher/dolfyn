from dolfyn.test import test_read_adv as tv
import dolfyn.adv.api as avm
from dolfyn.test.base import load_ncdata as load, save_ncdata as save
from xarray.testing import assert_equal


def test_clean_adv(make_data=False):
    td = tv.dat_imu.copy(deep=True)
    
    mask = avm.clean.GN2002(td.vel, 20)
    td = avm.clean.cleanFill(td, mask, method='cubic')

    if make_data:
        save(td, 'vector_data01_uclean.nc')
        return

    assert_equal(td, load('vector_data01_uclean.nc'))
    
    
if __name__ == '__main__':
    test_clean_adv()
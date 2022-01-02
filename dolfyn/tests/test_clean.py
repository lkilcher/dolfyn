from dolfyn.tests import test_read_adv as tv
from dolfyn.tests import test_read_adp as tp
import dolfyn.adv.api as avm
import dolfyn.adp.api as apm
from dolfyn.tests.base import load_ncdata as load, save_ncdata as save
from xarray.testing import assert_allclose
import numpy as np


def test_GN2002(make_data=False):
    td = tv.dat.copy(deep=True)
    td_imu = tv.dat_imu.copy(deep=True)

    td.vel[0, 50:65] = np.nan  # fudge up some data
    mask = avm.clean.GN2002(td.vel, npt=20)
    td['vel'] = avm.clean.clean_fill(td.vel, mask, method='cubic')

    mask = avm.clean.GN2002(td_imu.vel, npt=20)
    td_imu['vel'] = avm.clean.clean_fill(td_imu.vel, mask, method='cubic')

    if make_data:
        save(td, 'vector_data01_GN.nc')
        save(td_imu, 'vector_data_imu01_GN.nc')
        return

    assert_allclose(td, load('vector_data01_GN.nc'), atol=1e-6)
    assert_allclose(td_imu, load('vector_data_imu01_GN.nc'), atol=1e-6)


def test_spike_thresh(make_data=False):
    td = tv.dat_imu.copy(deep=True)

    mask = avm.clean.spike_thresh(td.vel, thresh=10)
    td['vel'] = avm.clean.clean_fill(td.vel, mask, method='cubic')

    if make_data:
        save(td, 'vector_data01_sclean.nc')
        return

    assert_allclose(td, load('vector_data01_sclean.nc'), atol=1e-6)


def test_range_limit(make_data=False):
    td = tv.dat_imu.copy(deep=True)

    mask = avm.clean.range_limit(td.vel)
    td['vel'] = avm.clean.clean_fill(td.vel, mask, method='cubic')

    if make_data:
        save(td, 'vector_data01_rclean.nc')
        return

    assert_allclose(td, load('vector_data01_rclean.nc'), atol=1e-6)


def test_clean_upADCP(make_data=False):
    td = tp.dat_sig_tide.copy(deep=True)

    td = apm.clean.set_range_offset(td, 0.6)
    td = apm.clean.surface_from_P(td, salinity=31)
    td = apm.clean.nan_beyond_surface(td)
    td = apm.clean.correlation_filter(td, thresh=70)

    if make_data:
        save(td, 'Sig1000_tidal_clean.nc')
        return

    assert_allclose(td, load('Sig1000_tidal_clean.nc'), atol=1e-6)


def test_clean_downADCP(make_data=False):
    td = tp.dat_sig_ie.copy(deep=True)

    td = apm.clean.vel_exceeds_thresh(td, thresh=4)
    td = apm.clean.fillgaps_time(td)
    td = apm.clean.fillgaps_depth(td)

    td = apm.clean.set_range_offset(td, 0.5)
    td = apm.clean.find_surface(td, thresh=10, nfilt=3)
    td = apm.clean.nan_beyond_surface(td)

    if make_data:
        save(td, 'Sig500_Echo_clean.nc')
        return

    assert_allclose(td, load('Sig500_Echo_clean.nc'), atol=1e-6)


def test_orient_filter(make_data=False):
    td_sig = tp.dat_sig_i.copy(deep=True)
    td_sig = apm.clean.medfilt_orient(td_sig)
    td_sig = apm.rotate2(td_sig, 'earth')

    td_rdi = tp.dat_rdi.copy(deep=True)
    td_rdi = apm.clean.medfilt_orient(td_rdi)
    td_rdi = apm.rotate2(td_rdi, 'earth')

    if make_data:
        save(td_sig, 'Sig1000_IMU_ofilt.nc')
        save(td_rdi, 'RDI_test01_ofilt.nc')
        return

    assert_allclose(td_sig, load('Sig1000_IMU_ofilt.nc'), atol=1e-6)
    assert_allclose(td_rdi, load('RDI_test01_ofilt.nc'), atol=1e-6)


if __name__ == '__main__':
    test_GN2002()
    test_spike_thresh()
    test_range_limit()
    test_clean_upADCP()
    test_clean_downADCP()
    test_orient_filter()

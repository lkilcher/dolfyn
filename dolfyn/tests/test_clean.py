from dolfyn.tests import test_read_adv as tv
from dolfyn.tests import test_read_adp as tp
from dolfyn.tests.base import load_netcdf as load, save_netcdf as save, assert_allclose
import dolfyn.adv.api as avm
import dolfyn.adp.api as apm
import numpy as np


def test_GN2002(make_data=False):
    td = tv.dat.copy(deep=True)
    td_imu = tv.dat_imu.copy(deep=True)

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

    mask = avm.clean.spike_thresh(td.vel, thresh=1)
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
    td_awac = tp.dat_awac.copy(deep=True)
    td_sig = tp.dat_sig_tide.copy(deep=True)

    apm.clean.find_surface_from_P(td_awac, salinity=30)
    td_awac = apm.clean.nan_beyond_surface(td_awac)

    apm.clean.set_range_offset(td_sig, 0.6)
    apm.clean.find_surface_from_P(td_sig, salinity=31)
    td_sig = apm.clean.nan_beyond_surface(td_sig)
    td_sig = apm.clean.correlation_filter(td_sig, thresh=50)

    if make_data:
        save(td_awac, 'AWAC_test01_clean.nc')
        save(td_sig, 'Sig1000_tidal_clean.nc')
        return

    assert_allclose(td_awac, load('AWAC_test01_clean.nc'), atol=1e-6)
    assert_allclose(td_sig, load('Sig1000_tidal_clean.nc'), atol=1e-6)


def test_clean_downADCP(make_data=False):
    td = tp.dat_sig_ie.copy(deep=True)

    # First remove bad data
    td['vel'] = apm.clean.val_exceeds_thresh(td.vel, thresh=3)
    td['vel'] = apm.clean.fillgaps_time(td.vel)
    td['vel_b5'] = apm.clean.fillgaps_time(td.vel_b5)
    td['vel'] = apm.clean.fillgaps_depth(td.vel)
    td['vel_b5'] = apm.clean.fillgaps_depth(td.vel_b5)

    # Then clean below seabed
    apm.clean.set_range_offset(td, 0.5)
    apm.clean.find_surface(td, thresh=10, nfilt=3)
    td = apm.clean.nan_beyond_surface(td)

    if make_data:
        save(td, 'Sig500_Echo_clean.nc')
        return

    assert_allclose(td, load('Sig500_Echo_clean.nc'), atol=1e-6)


def test_orient_filter(make_data=False):
    td_sig = tp.dat_sig_i.copy(deep=True)
    td_sig = apm.clean.medfilt_orient(td_sig)
    apm.rotate2(td_sig, 'earth', inplace=True)

    td_rdi = tp.dat_rdi.copy(deep=True)
    td_rdi = apm.clean.medfilt_orient(td_rdi)
    apm.rotate2(td_rdi, 'earth', inplace=True)

    if make_data:
        save(td_sig, 'Sig1000_IMU_ofilt.nc')
        save(td_rdi, 'RDI_test01_ofilt.nc')
        return

    assert_allclose(td_sig, load('Sig1000_IMU_ofilt.nc'), atol=1e-6)
    assert_allclose(td_rdi, load('RDI_test01_ofilt.nc'), atol=1e-6)

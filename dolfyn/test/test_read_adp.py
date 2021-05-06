from dolfyn.io.api import read_example as read
import dolfyn.test.base as tb
#import sys
import warnings
import numpy as np
from xarray.testing import assert_identical
warnings.simplefilter('ignore', UserWarning)

load = tb.load
save = tb.save
load_h5 = tb.load_h5data

dat_rdi = load('data/RDI_test01.nc')
dat_rdi_bt = load('data/RDI_withBT.nc')
dat_rdi_i = load('data/RDI_test01_rotate_beam2inst.nc')
dat_awac = load('data/AWAC_test01.nc')
dat_awac_ud = load('data/AWAC_test01_ud.nc')
dat_sig = load('data/BenchFile01.nc')
dat_sig_i = load('data/Sig1000_IMU.nc')
dat_sig_i_ud = load('data/Sig1000_IMU_ud.nc')
dat_sig_ieb = load('data/VelEchoBT01.nc')
#dat_sig_ie = load('data/Sig500_Echo.nc')
#dat_sig_vm = load('data/SigVM1000.nc')
dat_wr1 = load('data/winriver01.nc')
dat_wr2 = load('data/winriver02.nc')

# h5_rdi_orientraw = load_h5('RDI_test01.h5')
# h5_rdi = dat_rdi_orientraw.copy()
# h5_rdi['orient'].pop('raw')
# h5_rdi_bt = load_h5('RDI_withBT.h5')
# h5_rdi_i = load_h5('RDI_test01_rotate_beam2inst.h5')
# h5_awac = load_h5('AWAC_test01.h5')
# h5_awac_ud = load_h5('AWAC_test01_ud.h5')
# h5_sig = load_h5('BenchFile01.h5')
# h5_sigi = load_h5('Sig1000_IMU.h5')
# h5_sigi_ud = load_h5('Sig1000_IMU_ud.h5')
# h5_sigi_echo_bt = load_h5('VelEchoBT01.h5')
# h5_wr1 = load_h5('winriver01.h5')
# h5_wr2 = load_h5('winriver02.h5')


def test_badtime():
    dat = read('Sig1000_BadTime01.ad2cp')
    assert np.isnan(dat.time[199]), \
    "A good timestamp was found where a bad value is expected."


def test_read(make_data=False):
    # This uses the built-in declination!
    td_rdi_orientraw = tb.drop_config(read('RDI_test01.000'))
    td_rdi = td_rdi_orientraw.copy()
    td_rdi_bt = tb.drop_config(read('RDI_withBT.000'))

    td_sig = tb.drop_config(read('BenchFile01.ad2cp'))
    td_sig_i = tb.drop_config(read('Sig1000_IMU.ad2cp', userdata=False))
    td_sig_i_ud = tb.drop_config(read('Sig1000_IMU.ad2cp'))
    td_sig_ieb = tb.drop_config(read('VelEchoBT01.ad2cp'))
    td_awac = tb.drop_config(read('AWAC_test01.wpr', userdata=False))
    td_awac_ud = tb.drop_config(read('AWAC_test01.wpr'))
    td_wr1 = tb.drop_config(read('winriver01.PD0'))
    td_wr2 = tb.drop_config(read('winriver02.PD0'))

    # # We don't need the raw orientation data for most tests.
    # td_rdi['orient'].pop('raw')
    # td_rdi_bt['orient'].pop('raw')
    # td_sig['orient'].pop('raw')
    # td_awac['orient'].pop('raw')
    # td_awac_ud['orient'].pop('raw')
    # td_wr1['orient'].pop('raw')
    # td_wr2['orient'].pop('raw')

    if make_data:
        #dlfn.save(dlfn.read_example('RDI_test01.000'),'data/RDI_test01.nc')
        save(td_rdi_orientraw, 'data/RDI_test01.nc')
        save(td_rdi_bt, 'data/RDI_withBT.nc')
        save(td_sig, 'data/BenchFile01.nc')
        save(td_sig_i, 'data/Sig1000_IMU.nc')
        save(td_sig_i_ud, 'data/Sig1000_IMU_ud.nc')
        save(td_sig_ieb, 'data/VelEchoBT01.nc')
        #save(td_sig_ie, 'data/Sig500_Echo.nc')
        #save(td_sig_vm, 'data/SigVM1000.nc')
        save(td_awac, 'data/AWAC_test01.nc')
        save(td_awac_ud, 'data/AWAC_test01_ud.nc')
        save(td_wr1, 'data/winriver01.nc')
        save(td_wr2, 'data/winriver02.nc')
        return
    
    assert_identical(td_rdi, dat_rdi)
    assert_identical(td_rdi_bt, dat_rdi_bt)
    assert_identical(td_sig, dat_sig)
    assert_identical(td_sig_i, dat_sig_i)
    assert_identical(td_sig_i_ud, dat_sig_i_ud)
    assert_identical(td_sig_ieb, dat_sig_ieb)
    #assert_identical(td_sig_ie, dat_sig_ie)
    #assert_identical(td_sig_vm, dat_sig_vm)
    assert_identical(td_awac, dat_awac)
    assert_identical(td_awac_ud, dat_awac_ud)
    assert_identical(td_wr1, dat_wr1)
    assert_identical(td_wr2, dat_wr2)
    

if __name__ == '__main__':
    test_read()

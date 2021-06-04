from dolfyn.io.api import read_example as read
import dolfyn.test.base as tb
#import sys
import warnings
from xarray.testing import assert_equal, assert_identical
warnings.simplefilter('ignore', UserWarning)
load = tb.load_ncdata
save = tb.save_ncdata


dat_rdi = load('RDI_test01.nc')
dat_rdi_bt = load('RDI_withBT.nc')
dat_rdi_i = load('RDI_test01_rotate_beam2inst.nc')
dat_rdi_vm = load('vmdas01.nc')
dat_wr1 = load('winriver01.nc')
dat_wr2 = load('winriver02.nc')

dat_awac = load('AWAC_test01.nc')
dat_awac_ud = load('AWAC_test01_ud.nc')
dat_sig = load('BenchFile01.nc')
dat_sig_i = load('Sig1000_IMU.nc')
dat_sig_i_ud = load('Sig1000_IMU_ud.nc')
dat_sig_ieb = load('VelEchoBT01.nc')
dat_sig_ie = load('Sig500_Echo.nc')


def test_badtime():
    dat = read('Sig1000_BadTime01.ad2cp')
    assert dat.time[199].isnull(), \
    "A good timestamp was found where a bad value is expected."


def test_io_rdi(make_data=False):
    td_rdi = tb.drop_config(read('RDI_test01.000'))
    td_rdi_bt = tb.drop_config(read('RDI_withBT.000'))
    td_vm = tb.drop_config(read('vmdas01.ENX'))
    td_wr1 = tb.drop_config(read('winriver01.PD0'))
    td_wr2 = tb.drop_config(read('winriver02.PD0'))
    
    if make_data:
        #dlfn.save(dlfn.read_example('RDI_test01.000'),'RDI_test01.nc')
        save(td_rdi, 'RDI_test01.nc')
        save(td_rdi_bt, 'RDI_withBT.nc')
        save(td_vm, 'vmdas01.nc')
        save(td_wr1, 'winriver01.nc')
        save(td_wr2, 'winriver02.nc')
        return
    
    assert_equal(td_rdi, dat_rdi)
    assert_equal(td_rdi_bt, dat_rdi_bt)
    assert_equal(td_vm, dat_rdi_vm)
    assert_equal(td_wr1, dat_wr1)
    assert_equal(td_wr2, dat_wr2)


def test_io_nortek(make_data=False):
    td_sig = tb.drop_config(read('BenchFile01.ad2cp'))
    td_sig_i = tb.drop_config(read('Sig1000_IMU.ad2cp', userdata=False))
    td_sig_i_ud = tb.drop_config(read('Sig1000_IMU.ad2cp'))
    td_sig_ieb = tb.drop_config(read('VelEchoBT01.ad2cp'))
    td_sig_ie = tb.drop_config(read('Sig500_Echo.ad2cp'))
    td_awac = tb.drop_config(read('AWAC_test01.wpr', userdata=False))
    td_awac_ud = tb.drop_config(read('AWAC_test01.wpr'))

    if make_data:
        save(td_sig, 'BenchFile01.nc')
        save(td_sig_i, 'Sig1000_IMU.nc')
        save(td_sig_i_ud, 'Sig1000_IMU_ud.nc')
        save(td_sig_ieb, 'VelEchoBT01.nc')
        save(td_sig_ie, 'Sig500_Echo.nc')
        save(td_awac, 'AWAC_test01.nc')
        save(td_awac_ud, 'AWAC_test01_ud.nc')
        return
    
    assert_equal(td_sig, dat_sig)
    assert_equal(td_sig_i, dat_sig_i)
    assert_equal(td_sig_i_ud, dat_sig_i_ud)
    assert_equal(td_sig_ieb, dat_sig_ieb)
    assert_equal(td_sig_ie, dat_sig_ie)
    assert_equal(td_awac, dat_awac)
    assert_equal(td_awac_ud, dat_awac_ud)
    
    
def test_matlab_io(make_data=False):
    mat_rdi_bt = tb.load_matlab('dat_rdi_bt')
    mat_sig_ieb = tb.load_matlab('dat_sig_ieb')
    
    if make_data:
        tb.save_matlab(dat_rdi_bt, 'dat_rdi_bt')
        tb.save_matlab(dat_sig_ieb, 'dat_sig_ieb')
        
    assert_identical(mat_rdi_bt, dat_rdi_bt)
    assert_identical(mat_sig_ieb, dat_sig_ieb)
    

if __name__ == '__main__':
    test_io_rdi()
    test_io_nortek()
    test_matlab_io()
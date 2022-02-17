import dolfyn.io.rdi as wh
import dolfyn.io.nortek as awac
import dolfyn.io.nortek2 as sig
from dolfyn.io.api import read_example as read
from dolfyn.tests.base import assert_allclose, save_netcdf, save_matlab, load_matlab, exdt, rfnm, drop_config
from dolfyn.tests import test_read_adp as tp
from dolfyn.tests import test_read_adv as tv
import contextlib
import filecmp
import unittest
import pytest
import os
import io


def test_save():
    save_netcdf(tv.dat, 'test_save')
    save_matlab(tv.dat, 'test_save')

    assert os.path.exists(rfnm('test_save.nc'))
    assert os.path.exists(rfnm('test_save.mat'))


def test_matlab_io(make_data=False):
    nens = 100
    td_vec = drop_config(read('vector_data_imu01.VEC', nens=nens))
    td_rdi_bt = drop_config(read('RDI_withBT.000', nens=nens))

    # This read should trigger a warning about the declination being
    # defined in two places (in the binary .ENX files), and in the
    # .userdata.json file. NOTE: DOLfYN defaults to using what is in
    # the .userdata.json file.
    with pytest.warns(UserWarning, match='magnetic_var_deg'):
        td_vm = drop_config(read('vmdas01.ENX', nens=nens))

    if make_data:
        save_matlab(td_vec, 'dat_vec')
        save_matlab(td_rdi_bt, 'dat_rdi_bt')
        save_matlab(td_vm, 'dat_vm')
        return

    mat_vec = load_matlab('dat_vec.mat')
    mat_rdi_bt = load_matlab('dat_rdi_bt.mat')
    mat_vm = load_matlab('dat_vm.mat')

    assert_allclose(td_vec, mat_vec, atol=1e-6)
    assert_allclose(td_rdi_bt, mat_rdi_bt, atol=1e-6)
    assert_allclose(td_vm, mat_vm, atol=1e-6)


def test_debugging(make_data=False):
    def rdi_debug_output(filename, data, nens):
        with open(rfnm(filename), 'w') as f:
            with contextlib.redirect_stdout(f):
                drop_config(wh.read_rdi(exdt(data),
                                        debug=11,
                                        nens=nens))

    def nortek_debug_output(filename, data, nens):
        with open(rfnm(filename), 'w') as f:
            with contextlib.redirect_stdout(f):
                drop_config(awac.read_nortek(exdt(data),
                                             debug=True,
                                             do_checksum=True,
                                             nens=nens))

    def nortek2_debug_output(filename, data, nens):
        with open(rfnm(filename), 'w') as f:
            with contextlib.redirect_stdout(f):
                drop_config(sig.read_signature(exdt(data),
                                               nens=nens,
                                               rebuild_index=True,
                                               debug=True))
        os.remove(exdt('Sig500_Echo.ad2cp.index'))

    nens = 100
    rdi_debug_output('rdi_debug_test.txt', 'RDI_withBT.000', nens)
    nortek_debug_output('awac_debug_test.txt', 'AWAC_test01.wpr', nens)
    nortek_debug_output('vec_debug_test.txt', 'vector_data_imu01.VEC', nens)
    nortek2_debug_output('sig_debug_test.txt', 'Sig500_Echo.ad2cp', nens)

    if make_data:
        rdi_debug_output('rdi_debug_check.txt', 'RDI_withBT.000', nens)
        nortek_debug_output('awac_debug_check.txt', 'AWAC_test01.wpr', nens)
        nortek_debug_output('vec_debug_check.txt',
                            'vector_data_imu01.VEC', nens)
        nortek2_debug_output('sig_debug_check.txt', 'Sig500_Echo.ad2cp', nens)
        return

    assert filecmp.cmp(rfnm('rdi_debug_test.txt'),
                       rfnm('rdi_debug_check.txt'))
    assert filecmp.cmp(rfnm('awac_debug_test.txt'),
                       rfnm('awac_debug_check.txt'))
    assert filecmp.cmp(rfnm('vec_debug_test.txt'),
                       rfnm('vec_debug_check.txt'))
    assert filecmp.cmp(rfnm('sig_debug_test.txt'),
                       rfnm('sig_debug_check.txt'))

    os.remove(rfnm('rdi_debug_test.txt'))
    os.remove(rfnm('awac_debug_test.txt'))
    os.remove(rfnm('vec_debug_test.txt'))
    os.remove(rfnm('sig_debug_test.txt'))


class warnings_testcase(unittest.TestCase):
    def test_read_warnings(self):
        with self.assertRaises(Exception):
            wh.read_rdi(exdt('H-AWAC_test01.wpr'))
        with self.assertRaises(Exception):
            awac.read_nortek(exdt('BenchFile01.ad2cp'))
        with self.assertRaises(Exception):
            sig.read_signature(exdt('AWAC_test01.wpr'))
        with self.assertRaises(IOError):
            read(rfnm('AWAC_test01.nc'))
        with self.assertRaises(Exception):
            save_netcdf(tp.dat_rdi, 'test_save.fail')

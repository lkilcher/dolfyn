import dolfyn.io.rdi as wh
import dolfyn.io.nortek as awac
import dolfyn.io.nortek2 as sig
from dolfyn.io.api import read_example as read
from dolfyn.tests.base import assert_allclose, save_netcdf, save_matlab
from dolfyn.tests import base as tb, test_read_adp as tp
from dolfyn.tests import test_read_adv as tv
import contextlib
import unittest
import pytest
import os
import io


def test_save():
    save_netcdf(tv.dat, 'test_save')
    save_matlab(tv.dat, 'test_save')

    assert os.path.exists(tb.rfnm('test_save.nc'))
    assert os.path.exists(tb.rfnm('test_save.mat'))


def test_matlab_io(make_data=False):
    nens = 100
    td_vec = tb.drop_config(read('vector_data_imu01.VEC', nens=nens))
    td_rdi_bt = tb.drop_config(read('RDI_withBT.000', nens=nens))

    # This read should trigger a warning about the declination being
    # defined in two places (in the binary .ENX files), and in the
    # .userdata.json file. NOTE: DOLfYN defaults to using what is in
    # the .userdata.json file.
    with pytest.warns(UserWarning, match='magnetic_var_deg'):
        td_vm = tb.drop_config(read('vmdas01.ENX', nens=nens))

    if make_data:
        save_matlab(td_vec, 'dat_vec')
        save_matlab(td_rdi_bt, 'dat_rdi_bt')
        save_matlab(td_vm, 'dat_vm')
        return

    mat_vec = tb.load_matlab('dat_vec.mat')
    mat_rdi_bt = tb.load_matlab('dat_rdi_bt.mat')
    mat_vm = tb.load_matlab('dat_vm.mat')

    assert_allclose(td_vec, mat_vec, atol=1e-6)
    assert_allclose(td_rdi_bt, mat_rdi_bt, atol=1e-6)
    assert_allclose(td_vm, mat_vm, atol=1e-6)


def test_debugging(make_data=False):
    def rdi_debug_output(f, data, nens):
        with contextlib.redirect_stdout(f):
            tb.drop_config(wh.read_rdi(tb.exdt(data),
                                       debug=11,
                                       nens=nens))

    def nortek_debug_output(f, data, nens):
        with contextlib.redirect_stdout(f):
            tb.drop_config(awac.read_nortek(tb.exdt(data),
                                            debug=True,
                                            do_checksum=True,
                                            nens=nens))

    def nortek2_debug_output(f, data, nens):
        with contextlib.redirect_stdout(f):
            tb.drop_config(sig.read_signature(tb.exdt(data),
                                              nens=nens,
                                              rebuild_index=True,
                                              debug=True))
        os.remove(tb.exdt('Sig500_Echo.ad2cp.index'))

    nens = 100
    db_rdi = io.StringIO()
    db_awac = io.StringIO()
    db_vec = io.StringIO()
    db_sig = io.StringIO()

    rdi_debug_output(db_rdi, 'RDI_withBT.000', nens)
    nortek_debug_output(db_awac, 'AWAC_test01.wpr', nens)
    nortek_debug_output(db_vec, 'vector_data_imu01.VEC', nens)
    nortek2_debug_output(db_sig, 'Sig500_Echo.ad2cp', nens)

    if make_data:
        with open(tb.rfnm('rdi_debug_out.txt'), 'w') as fn_rdi:
            rdi_debug_output(fn_rdi, 'RDI_withBT.000', nens)

        with open(tb.rfnm('awac_debug_out.txt'), 'w') as fn_awac:
            nortek_debug_output(fn_awac, 'AWAC_test01.wpr', nens)

        with open(tb.rfnm('vec_debug_out.txt'), 'w') as fn_vec:
            nortek_debug_output(fn_vec, 'vector_data_imu01.VEC', nens)

        with open(tb.rfnm('sig_debug_out.txt'), 'w') as fn_sig:
            nortek2_debug_output(fn_sig, 'Sig500_Echo.ad2cp', nens)
        return

    with open(tb.rfnm('rdi_debug_out.txt'), 'r') as fl:
        test_rdi = fl.read()
    with open(tb.rfnm('awac_debug_out.txt'), 'r') as fl:
        test_awac = fl.read()
    with open(tb.rfnm('vec_debug_out.txt'), 'r') as fl:
        test_vec = fl.read()
    with open(tb.rfnm('sig_debug_out.txt'), 'r') as fl:
        test_sig = fl.read()

    assert test_rdi.lower() == db_rdi.getvalue().lower()
    assert test_awac.lower() == db_awac.getvalue().lower()
    assert test_vec.lower() == db_vec.getvalue().lower()
    assert test_sig.lower() == db_sig.getvalue().lower()


class warnings_testcase(unittest.TestCase):
    def test_read_warnings(self):
        with self.assertRaises(Exception):
            wh.read_rdi(tb.exdt('H-AWAC_test01.wpr'))
        with self.assertRaises(Exception):
            awac.read_nortek(tb.exdt('BenchFile01.ad2cp'))
        with self.assertRaises(Exception):
            sig.read_signature(tb.exdt('AWAC_test01.wpr'))
        with self.assertRaises(IOError):
            read(tb.rfnm('AWAC_test01.nc'))
        with self.assertRaises(Exception):
            tb.save_netcdf(tp.dat_rdi, 'test_save.fail')

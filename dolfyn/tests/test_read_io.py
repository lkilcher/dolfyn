import dolfyn.io.rdi as wh
import dolfyn.io.nortek as awac
import dolfyn.io.nortek2 as sig
from dolfyn.io.api import read_example as read
from dolfyn.tests.base import assert_allclose, save_netcdf, save_matlab, load_matlab, exdt, rfnm, drop_config
from dolfyn.tests import test_read_adp as tp
from dolfyn.tests import test_read_adv as tv
import contextlib
import difflib
import unittest
import pytest
import os
import io


def test_save():
    save_netcdf(tv.dat, 'test_save')
    save_matlab(tv.dat, 'test_save')

    assert os.path.exists(rfnm('test_save.nc'))
    assert os.path.exists(rfnm('test_save.mat'))


def capture_stdout_decorator(func):
    # A decorator function for capturing stdout and redirecting it
    # to either: a string (returned by fn) or outfile
    def capture_stdout(*args, outfile=None, **kwargs):
        if outfile is None:
            output = io.StringIO
        else:
            output = lambda: open(rfnm(outfile), 'w')

        out = None
        with output() as f:
            with contextlib.redirect_stdout(f):
                func(*args, **kwargs)
            if outfile is None:
                out = f.getvalue()
        return out
    return capture_stdout

def compare_debug_output(string1, fname2):
    with open(fname2, 'r') as f2:
        string2 = f2.read()
    
    diff = difflib.ndiff(string1.splitlines(), string2.splitlines())

    # Note I tried using the linejunk= kwarg to difflib.ndiff, but for
    # some reason it wasn't working, so I'm doing the filtering myself
    
    filtered_diff = []
    for row in diff:
        if not (row.startswith('- ') or row.startswith('+ ')):
            continue
        _row = row[2:] # Drop the "+ " or "- ".
        if _row.startswith('Reading file '):
            continue
        if _row.startswith('Indexing '):
            continue
        filtered_diff.append(row)

    return len(filtered_diff) == 0


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

    @capture_stdout_decorator
    def rdi_debug_output(datafile, nens):
        wh.read_rdi(exdt(datafile), debug=11, nens=nens)

    @capture_stdout_decorator
    def nortek_debug_output(datafile, nens):
        awac.read_nortek(exdt(datafile),
                         debug=True,
                         do_checksum=True,
                         nens=nens)

    @capture_stdout_decorator
    def nortek2_debug_output(datafile, nens):
        sig.read_signature(exdt(datafile),
                           nens=nens,
                           rebuild_index=True,
                           debug=True)

        os.remove(exdt(datafile + '.index'))

    nens = 100

    if make_data:
        rdi_debug_output('RDI_withBT.000', outfile='rdi_debug_check.txt', nens=nens)
        nortek_debug_output('AWAC_test01.wpr', outfile='awac_debug_check.txt', nens=nens)
        nortek_debug_output('vector_data_imu01.VEC', outfile='vec_debug_check.txt', nens=nens)
        nortek2_debug_output('Sig500_Echo.ad2cp', outfile='sig_debug_check.txt', nens=nens)
        return
    
    assert compare_debug_output(
        rdi_debug_output('RDI_withBT.000', nens=nens),
        rfnm('rdi_debug_check.txt'))
    assert compare_debug_output(
        nortek_debug_output('AWAC_test01.wpr', nens),
        rfnm('awac_debug_check.txt'))
    assert compare_debug_output(
        nortek_debug_output('vector_data_imu01.VEC', nens),
        rfnm('vec_debug_check.txt'))
    assert compare_debug_output(
        nortek2_debug_output('Sig500_Echo.ad2cp', nens),
        rfnm('sig_debug_check.txt'))


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


if __name__ == '__main__':

    #test_debugging()
    tmp1 = compare_debug_output(rfnm('rdi_debug_test.txt'),
                                rfnm('rdi_debug_check.txt'))

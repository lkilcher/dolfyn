import dolfyn.adp.api as apm
import dolfyn.data.base
from os import path

dolfyn.data.base.debug_level = 1

try:
    test_root = path.realpath(__file__).replace("\\", "/").rsplit('/', 1)[0] + '/'
except:
    test_root = './'

pkg_root = test_root.rsplit('/', 2)[0] + "/"


dat_rdi = apm.load(test_root + 'data/RDI_test01.h5', 'ALL')
dat_rdi_i = apm.load(test_root + 'data/RDI_test01_rotate_beam2inst.h5', 'ALL')
dat_sig = apm.load(test_root + 'data/BenchFile01.h5', 'ALL')


def data_equiv(dat1, dat2, message=''):
    assert dat1 == dat2, message


def read_test(make_data=False):

    td_rdi = apm.read_rdi(pkg_root + 'example_data/RDI_test01.000')
    td_sig = apm.read_signature(pkg_root + 'example_data/BenchFile01.ad2cp')

    if make_data:
        td_rdi.save(test_root + 'data/RDI_test01.h5')
        td_sig.save(test_root + 'data/BenchFile01.h5')
        return

    msg_form = "The output of read_rdi('{}') does not match '{}'."
    for dat1, dat2, msg in [
            (td_rdi, dat_rdi,
             msg_form.format('RDI_test01.000', 'RDI_test01.h5')),
            (td_sig, dat_sig,
             msg_form.format('BenchFile01.ad2cp', 'BenchFile01.h5')),
    ]:
        yield data_equiv, dat1, dat2, msg


def rotate_beam2inst_test(make_data=False):

    td = dat_rdi.copy()
    apm.beam2inst(td)

    if make_data:
        td.save(test_root + 'data/RDI_test01_rotate_beam2inst.h5')
        return

    assert td == dat_rdi_i, "adp.rotate.beam2inst gives unexpected results!"


def rotate_inst2earth_test(make_data=False):

    td = dat_rdi_i.copy()
    apm.inst2earth(td)

    if make_data:
        td.save(test_root + 'data/RDI_test01_rotate_inst2earth.h5')
        return

    cd = apm.load(test_root + 'data/RDI_test01_rotate_inst2earth.h5', 'ALL')

    assert td == cd, "adp.rotate.inst2earth gives unexpected results!"


if __name__ == '__main__':

    pkg_root = '../'

    for func, dat1, dat2, msg in read_test():
        func(dat1, dat2, msg)

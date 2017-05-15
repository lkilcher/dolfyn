import dolfyn.adp.api as apm
import dolfyn.data.base
from os import path

dolfyn.data.base.debug_level = 1

try:
    test_root = path.realpath(__file__).replace("\\", "/").rsplit('/', 1)[0] + '/'
except:
    test_root = './'

pkg_root = test_root.rsplit('/', 2)[0] + "/"


dat = apm.load(test_root + 'data/RDI_test01.h5', 'ALL')
dati = apm.load(test_root + 'data/RDI_test01_rotate_beam2inst.h5', 'ALL')
dataw = apm.load(test_root + 'data/AWAC_test01.h5', 'ALL')


def data_equiv(dat1, dat2, message=''):
    assert dat1 == dat2, message


def read_test(make_data=False):

    td = apm.read_rdi(pkg_root + 'example_data/RDI_test01.000')
    awd = apm.read_nortek(pkg_root + 'example_data/AWAC_test01.wpr')

    if make_data:
        td.save(test_root + 'data/RDI_test01.h5')
        awd.save(test_root + 'data/AWAC_test01.h5')
        return

    msg_form = "The output of {} does not match {}."
    for dat1, dat2, msg in [
            (td, dat,
             msg_form.format("'read_rdi(RDI_test01.000)'", 'RDI_test01.h5')),
            (awd, dataw,
             msg_form.format("'read_nortek(AWAC_test01.wpr)'",
                             'AWAC_test01.h5')),
    ]:
        yield data_equiv, dat1, dat2, msg


def rotate_beam2inst_test(make_data=False):

    td = dat.copy()
    apm.beam2inst(td)

    if make_data:
        td.save(test_root + 'data/RDI_test01_rotate_beam2inst.h5')
        return

    assert td == dati, "adp.rotate.beam2inst gives unexpected results!"


def rotate_inst2earth_test(make_data=False):

    td = dati.copy()
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

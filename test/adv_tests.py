import dolfyn.adv.api as avm
import numpy as np
from os import path

test_root = path.realpath(__file__).replace("\\", "/").rsplit('/', 1)[0] + '/'
pkg_root = test_root.rsplit('/', 2)[0] + "/"

dat = avm.load(test_root + 'data/vector_data01.h5', 'ALL')
dat_imu = avm.load(test_root + 'data/vector_data_imu01.h5', 'ALL')


def read_test(make_data=False):

    td = avm.read_nortek(pkg_root + 'example_data/vector_data01.VEC')
    tdm = avm.read_nortek(pkg_root + 'example_data/vector_data_imu01.VEC')
    # These values are not correct for this data but I'm adding them for
    # test purposes only.
    tdm.props['body2head_rotmat'] = np.eye(3)
    tdm.props['body2head_vec'] = np.array([-1.0, 0.5, 0.2])

    if make_data:
        td.save(test_root + 'data/vector_data01.h5')
        tdm.save(test_root + 'data/vector_data_imu01.h5')
        return

    err_str = ("The output of read_nortek('vector_data01.VEC') "
               "does not match 'vector_data01.h5'.")
    assert td == dat, err_str
    err_str = ("The output of read_nortek('vector_data_imu01.VEC') "
               "does not match 'vector_data_imu01.h5'.")
    assert tdm == dat_imu, err_str


def motion_test(make_data=False):
    mc = avm.motion.CorrectMotion()
    tdm = dat_imu.copy()
    mc(tdm)

    if make_data:
        tdm.save(test_root + 'data/vector_data_imu01_mc.h5')
        return

    cdm = avm.load(test_root + 'data/vector_data_imu01_mc.h5', 'ALL')

    assert tdm == cdm, "Motion correction does not match expectations."


def heading_test(make_data=False):
    td = dat_imu.copy()

    pitch, roll, head = avm.rotate.orient2euler(td)
    td.add_data('pitch', pitch, 'orient')
    td.add_data('roll', roll, 'orient')
    td.add_data('heading', head, 'orient')

    if make_data:
        td.save(test_root + 'data/vector_data_imu01_head_pitch_roll.h5')
        return

    cd = avm.load(test_root + 'data/vector_data_imu01_head_pitch_roll.h5', 'ALL')

    assert td == cd, "adv.rotate.orient2euler gives unexpected results!"


def turbulence_test(make_data=False):
    tmp = dat.copy()
    bnr = avm.TurbBinner(4096, tmp.fs)
    td = bnr(tmp)

    if make_data:
        td.save(test_root + 'data/vector_data01_bin.h5')
        return

    cd = avm.load(test_root + 'data/vector_data01_bin.h5', 'ALL')

    assert cd == td, "TurbBinner gives unexpected results!"


def clean_test(make_data=False):
    td = dat.copy()
    avm.clean.GN2002(td.u)

    if make_data:
        td.save(test_root + 'data/vector_data01_uclean.h5')
        return

    cd = avm.load(test_root + 'data/vector_data01_uclean.h5', 'ALL')

    assert cd == td, "adv.clean.GN2002 gives unexpected results!"

import dolfyn.adv.api as avm
import dolfyn.data.base
import numpy as np
from os import path
import pycoda as pcd


dolfyn.data.base.debug_level = 1

try:
    test_root = path.realpath(__file__).replace("\\", "/").rsplit('/', 1)[0] + '/'
except:
    test_root = './'

pkg_root = test_root.rsplit('/', 2)[0] + "/"

dat = avm.load(test_root + 'data/vector_data01.h5')
dat_imu = avm.load(test_root + 'data/vector_data_imu01.h5')


def read_test(make_data=False):

    td = avm.read_nortek(pkg_root + 'example_data/vector_data01.VEC')

    if make_data:
        td.to_hdf5(test_root + 'data/vector_data01.h5')
        return td

    err_str = ("The output of read_nortek('vector_data01.VEC') "
               "does not match 'vector_data01.h5'.")
    assert td == dat, err_str


def read_test_imu(make_data=False):

    td = avm.read_nortek(pkg_root + 'example_data/vector_data_imu01.VEC')
    # These values are not correct for this data but I'm adding them for
    # test purposes only.
    td.props['body2head_rotmat'] = np.eye(3)
    td.props['body2head_vec'] = np.array([-1.0, 0.5, 0.2])

    if make_data:
        td.to_hdf5(test_root + 'data/vector_data_imu01.h5')
        return td

    err_str = ("The output of read_nortek('vector_data_imu01.VEC') "
               "does not match 'vector_data_imu01.h5'.")
    assert td == dat_imu, err_str


# For non-IMU advs:
def inst2earth_test(make_data=False):
    td = dat.copy()
    avm.rotate.inst2earth(td)
    # only compare the 'vel' data.
    td = pcd.data(vel=td['vel'])

    if make_data:
        td.to_hdf5(test_root + 'data/vector_data_imu01_inst2earth.h5')
        return td

    cd = avm.load(test_root + 'data/vector_data_imu01_inst2earth.h5')

    assert td == cd, "Rotation to earth does not match expectations."


def subset_test(make_data=False):
    td = dat.copy()
    td = td.subset[..., 100:1000]
    

def motion_test(make_data=False):
    td = dat_imu.copy()
    avm.motion.correct_motion(td)

    if make_data:
        td.to_hdf5(test_root + 'data/vector_data_imu01_mc.h5')
        return td

    cd = avm.load(test_root + 'data/vector_data_imu01_mc.h5')

    assert td == cd, "Motion correction does not match expectations."


def earth2principal_test(make_data=False):
    td = avm.load(test_root + 'data/vector_data_imu01_mc.h5')
    avm.rotate.earth2principal(td)
    td = pcd.data(vel=td['vel'], orient=td['orient'], props=td['props'])

    if make_data:
        td.to_hdf5(test_root + 'data/vector_data_imu01_principal.h5')
        return td

    cd = avm.load(test_root + 'data/vector_data_imu01_principal.h5')

    assert td == cd, "Rotation to principal axes does not match expectations."


def declination_test(make_data=False):
    td = dat_imu.copy()
    td.props['declination'] = 14.3
    avm.motion.correct_motion(td)
    td = pcd.data(vel=td['vel'], props=td['props'])

    if make_data:
        td.to_hdf5(test_root + 'data/vector_data_imu01_declination.h5')
        return td

    cd = avm.load(test_root + 'data/vector_data_imu01_declination.h5')

    assert td == cd, "Motion correction does not match expectations."


def heading_test(make_data=False):
    td = dat_imu.copy()

    o = td['orient']
    o['pitch'], o['roll'], o['heading'] = avm.rotate.orient2euler(td)
    td = o

    if make_data:
        td.to_hdf5(test_root + 'data/vector_data_imu01_head_pitch_roll.h5')
        return td

    cd = avm.load(test_root + 'data/vector_data_imu01_head_pitch_roll.h5')

    assert td == cd, "adv.rotate.orient2euler gives unexpected results!"


def turbulence_test(make_data=False):
    td = avm.calc_turbulence(dat.copy(), 4096)

    if make_data:
        td.to_hdf5(test_root + 'data/vector_data01_bin.h5')
        return td

    cd = avm.load(test_root + 'data/vector_data01_bin.h5')

    assert cd == td, "TurbBinner gives unexpected results!"


def clean_test(make_data=False):
    td = dat.copy()
    avm.clean.GN2002(td['vel'][0])
    # only compare the 'vel' data.
    td = pcd.data(vel=td['vel'])

    if make_data:
        td.to_hdf5(test_root + 'data/vector_data01_uclean.h5')
        return td

    cd = avm.load(test_root + 'data/vector_data01_uclean.h5')

    assert cd == td, "adv.clean.GN2002 gives unexpected results!"

import dolfyn.adv.api as avm
import dolfyn.data.base
import numpy as np
from os import path

dolfyn.data.base.debug_level = 1

try:
    test_root = path.realpath(__file__).replace("\\", "/").rsplit('/', 1)[0] + '/'
except:
    test_root = './'

pkg_root = test_root.rsplit('/', 2)[0] + "/"

dat = avm.load(test_root + 'data/vector_data01.h5', 'ALL')
dat_imu = avm.load(test_root + 'data/vector_data_imu01.h5', 'ALL')
dat_imu_json = avm.load(test_root + 'data/vector_data_imu01-json.h5', 'ALL')
dat_burst = avm.load(test_root + 'data/burst_mode01.h5', 'ALL')


def data_equiv(dat1, dat2, message=''):
    assert dat1 == dat2, message


def assert_close(dat1, dat2, message='', *args):
    assert np.allclose(dat1, dat2, *args), message


def check_except(fn, args, errors=Exception, message=''):
    try:
        fn(args)
    except errors:
        pass
    else:
        raise Exception(message)


def read_test(make_data=False):

    td = avm.read_nortek(pkg_root + 'example_data/vector_data01.VEC',
                         npings=100)
    tdm = avm.read_nortek(pkg_root + 'example_data/vector_data_imu01.VEC',
                          read_userdata=False,
                          npings=100)
    tdb = avm.read_nortek(pkg_root + 'example_data/burst_mode01.VEC',
                          npings=100)
    tdm2 = avm.read_nortek(pkg_root + 'example_data/vector_data_imu01.VEC',
                           npings=100)
    # These values are not correct for this data but I'm adding them for
    # test purposes only.
    tdm.props['body2head_rotmat'] = np.eye(3)
    tdm.props['body2head_vec'] = np.array([-1.0, 0.5, 0.2])

    if make_data:
        td.save(test_root + 'data/vector_data01.h5')
        tdm.save(test_root + 'data/vector_data_imu01.h5')
        tdb.save(test_root + 'data/burst_mode01.h5')
        tdm2.save(test_root + 'data/vector_data_imu01-json.h5')
        return

    msg_form = "The output of read_nortek('{}.VEC') does not match '{}.h5'."
    for dat1, dat2, msg in [
            (td, dat,
             msg_form.format('vector_data01', 'vector_data01')),
            (tdm, dat_imu,
             msg_form.format('vector_data_imu01', 'vector_data_imu01')),
            (tdb, dat_burst,
             msg_form.format('burst_mode01', 'burst_mode01')),
            (tdm2, dat_imu_json,
             msg_form.format('vector_data_imu01-json',
                             'vector_data_imu01-json')),
    ]:
        yield data_equiv, dat1, dat2, msg


def motion_test(make_data=False):
    tdm = dat_imu.copy()
    avm.motion.correct_motion(tdm)
    tdm10 = dat_imu.copy()
    # Include the declination.
    tdm10.props['declination'] = 10.0
    avm.motion.correct_motion(tdm10)
    tdm0 = dat_imu.copy()
    # Include the declination.
    tdm0.props['declination'] = 0.0
    avm.motion.correct_motion(tdm0)
    tdmj = dat_imu_json.copy()
    avm.motion.correct_motion(tdmj)

    if make_data:
        tdm.save(test_root + 'data/vector_data_imu01_mc.h5')
        tdm10.save(test_root + 'data/vector_data_imu01_mcDeclin10.h5')
        tdmj.save(test_root + 'data/vector_data_imu01-json_mc.h5')
        return

    msg_form = "Motion correction {}does not match expectations."

    for dat1, dat2, msg in [
            (tdm,
             avm.load(test_root + 'data/vector_data_imu01_mc.h5', 'ALL'),
             ''),
            (tdm10,
             avm.load(test_root + 'data/vector_data_imu01_mcDeclin10.h5', 'ALL'),
             'with declination=10 '),
            (tdmj,
             avm.load(test_root + 'data/vector_data_imu01-json_mc.h5', 'ALL'),
             'with reading userdata.json '),
    ]:
        yield data_equiv, dat1, dat2, msg_form.format(msg)

    yield data_equiv, tdm10, tdmj, \
        ".userdata.json motion correction does not match explicit expectations."

    tdm0.props.pop('declination')
    tdm0.props.pop('declination_in_orientmat')
    tdm0.props.pop('declination_in_heading')
    yield data_equiv, tdm0, tdm, \
        "The data changes when declination is specified as 0!"


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
    bnr = avm.TurbBinner(20, tmp.fs)
    td = bnr(tmp)

    if make_data:
        td.save(test_root + 'data/vector_data01_bin.h5')
        return

    cd = avm.load(test_root + 'data/vector_data01_bin.h5', 'ALL')

    assert cd == td, "TurbBinner gives unexpected results!"


def clean_test(make_data=False):
    td = dat.copy()
    avm.clean.GN2002(td.u, 20)

    if make_data:
        td.save(test_root + 'data/vector_data01_uclean.h5')
        return

    cd = avm.load(test_root + 'data/vector_data01_uclean.h5', 'ALL')

    assert cd == td, "adv.clean.GN2002 gives unexpected results!"


def subset_test(make_data=False):
    td = dat.copy().subset(slice(10, 20))

    if make_data:
        td.save(test_root + 'data/vector_data01_subset.h5')
        return

    cd = avm.load(test_root + 'data/vector_data01_subset.h5', 'ALL')

    # First check that subsetting works correctly
    yield data_equiv, cd, td, "ADV data object `subset` method gives unexpected results."

    # Now check that empty subsetting raises an error
    for index in [slice(0),
                  td.mpltime < 0,
                  slice(td.mpltime.shape[0] + 5, td.mpltime.shape[0] + 100)]:
        yield (check_except, td.subset, index, IndexError,
               "Attempts to subset to an empty data-object should raise an error.")

import numpy as np
import dolfyn.adv.api as avm
from dolfyn import read_example as read
import dolfyn.test.base as tb

load = tb.load_tdata
save = tb.save_tdata

dat = load('vector_data01.h5')
dat_imu = load('vector_data_imu01.h5')
dat_imu_json = load('vector_data_imu01-json.h5')
dat_burst = load('burst_mode01.h5')


def data_equiv(dat1, dat2, message=''):
    if 'props' in dat1 and 'principal_angle' in dat1['props']:
        pa1 = dat1['props'].pop('principal_angle')
        pa2 = dat2['props'].pop('principal_angle')
        assert np.abs(pa1 - pa2) < 1e-4
    assert dat1 == dat2, message


def check_except(fn, args, errors=Exception, message=''):
    try:
        fn(args)
    except errors:
        pass
    else:
        raise Exception(message)


def test_read(make_data=False):

    td = read('vector_data01.VEC', nens=100)
    tdm = read('vector_data_imu01.VEC',
               userdata=False,
               nens=100)
    tdb = read('burst_mode01.VEC',
               nens=100)
    tdm2 = read('vector_data_imu01.VEC',
                userdata=tb.exdt('vector_data_imu01.userdata.json'),
                nens=100)
    # These values are not correct for this data but I'm adding them for
    # test purposes only.
    tdm.props['body2head_rotmat'] = np.eye(3)
    tdm.props['body2head_vec'] = np.array([-1.0, 0.5, 0.2])

    if make_data:
        save(td, 'vector_data01.h5')
        save(tdm, 'vector_data_imu01.h5')
        save(tdb, 'burst_mode01.h5')
        save(tdm2, 'vector_data_imu01-json.h5')
        return

    msg_form = "The output of read('{}.VEC') does not match '{}.h5'."
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


def test_motion(make_data=False):
    mc = avm.motion.CorrectMotion()
    tdm = dat_imu.copy()
    mc(tdm)
    tdm10 = dat_imu.copy()
    # Include the declination.
    tdm10.props['declination'] = 10.0
    mc(tdm10)
    tdm0 = dat_imu.copy()
    # Include the declination.
    tdm0.props['declination'] = 0.0
    mc(tdm0)
    tdmj = dat_imu_json.copy()
    mc(tdmj)

    tdmE = dat_imu.copy()
    # Include declination
    tdmE.props['declination'] = 10.0
    tdmE.rotate2('earth', inplace=True)
    mc(tdmE)

    if make_data:
        save(tdm, 'vector_data_imu01_mc.h5')
        save(tdm10, 'vector_data_imu01_mcDeclin10.h5')
        save(tdmj, 'vector_data_imu01-json_mc.h5')
        return

    msg_form = "Motion correction '{}' does not match expectations."

    cdm10 = load('vector_data_imu01_mcDeclin10.h5')

    for dat1, dat2, msg in [
            (tdm,
             load('vector_data_imu01_mc.h5'),
             'basic motion correction'),
            (tdm10,
             cdm10,
             'with declination=10'),
            (tdmE,
             cdm10,
             'earth-rotation first, with declination=10'),
            (tdmj,
             load('vector_data_imu01-json_mc.h5'),
             'with reading userdata.json'),
    ]:
        yield data_equiv, dat1, dat2, msg_form.format(msg)

    yield data_equiv, tdm10, tdmj, \
        ".userdata.json motion correction does not match explicit expectations."

    tdm0.props.pop('declination')
    tdm0.props.pop('declination_in_orientmat')
    tdm0.props.pop('declination_in_heading')
    yield data_equiv, tdm0, tdm, \
        "The data changes when declination is specified as 0!"


def test_heading(make_data=False):
    td = dat_imu.copy()

    head, pitch, roll = avm.rotate.orient2euler(td)
    od = td['orient']
    od['pitch'] = pitch
    od['roll'] = roll
    od['heading'] = head

    if make_data:
        save(td, 'vector_data_imu01_head_pitch_roll.h5')
        return

    cd = load('vector_data_imu01_head_pitch_roll.h5')

    assert td == cd, "adv.rotate.orient2euler gives unexpected results!"


def test_turbulence(make_data=False):
    tmp = dat.copy()
    bnr = avm.TurbBinner(20.0, float(tmp['props']['fs']))
    td = bnr(tmp)

    if make_data:
        save(td, 'vector_data01_bin.h5')
        return

    cd = load('vector_data01_bin.h5')

    assert cd == td, "TurbBinner gives unexpected results!"


def test_clean(make_data=False):
    td = dat.copy()
    avm.clean.GN2002(td.u, 20)

    if make_data:
        save(td, 'vector_data01_uclean.h5')
        return

    cd = load('vector_data01_uclean.h5')

    assert cd == td, "adv.clean.GN2002 gives unexpected results!"


def test_subset(make_data=False):
    td = dat.copy().subset[10:20]

    if make_data:
        save(td, 'vector_data01_subset.h5')
        return

    cd = load('vector_data01_subset.h5')

    # First check that subsetting works correctly
    yield data_equiv, cd, td, "ADV data object `subset` method gives unexpected results."

    # Now check that empty subsetting raises an error
    for index in [slice(0),
                  td.mpltime < 0,
                  slice(td.mpltime.shape[0] + 5, td.mpltime.shape[0] + 100)]:
        yield (check_except, td._subset, index, IndexError,
               "Attempts to subset to an empty data-object should raise an error.")


if __name__ == '__main__':

    from base import rungen

    rungen(test_read())
    rungen(test_motion())
    test_heading()
    test_turbulence()
    test_clean()
    rungen(test_subset())

from dolfyn.test import test_adv as tr
from dolfyn import rotate2 as rotate, calc_principal_heading
from dolfyn.test.base import load_tdata as load, save_tdata as save
from dolfyn.rotate.base import euler2orient
import numpy as np    

data_equiv = tr.data_equiv


def test_inst2head_rotmat():
    # Validated test
    td = tr.dat.copy()

    #Swap x,y, reverse z
    td.set_inst2head_rotmat([[0, 1, 0],
                             [1, 0, 0],
                             [0, 0, -1]])

    assert ((td.u == tr.dat.v).all() and
            (td.v == tr.dat.u).all() and
            (td.w == -tr.dat.w).all()
            ), "head->inst rotations give unexpeced results."

    # Validation for non-symmetric rotations
    td = tr.dat.copy()
    R = euler2orient(20, 30, 60, units='degrees') # arbitrary angles
    td.set_inst2head_rotmat(R)
    vel1 = td.vel
    # validate that a head->inst rotation occurs (transpose of inst2head_rotmat)
    vel2 = np.dot(R.T, tr.dat.vel)
    assert (vel1 == vel2).all(), "head->inst rotations give unexpeced results."

def test_rotate_inst2earth(make_data=False):
    td = tr.dat.copy()
    rotate(td, 'earth', inplace=True)
    tdm = tr.dat_imu.copy()
    rotate(tdm, 'earth', inplace=True)

    if make_data:
        save(td, 'vector_data01_rotate_inst2earth.h5')
        save(tdm, 'vector_data_imu01_rotate_inst2earth.h5')
        return

    cd = load('vector_data01_rotate_inst2earth.h5')
    cdm = load('vector_data_imu01_rotate_inst2earth.h5')

    msg = "adv.rotate.inst2earth gives unexpected results for {}"
    for t, c, msg in (
            (td, cd, msg.format('vector_data01')),
            (tdm, cdm, msg.format('vector_data_imu01')),
    ):
        yield data_equiv, t, c, msg


def test_rotate_earth2inst():
    td = load('vector_data01_rotate_inst2earth.h5')
    rotate(td, 'inst', inplace=True)
    tdm = load('vector_data_imu01_rotate_inst2earth.h5')
    rotate(tdm, 'inst', inplace=True)

    cd = tr.dat.copy()
    cdm = tr.dat_imu.copy()
    # The heading/pitch/roll data gets modified during rotation, so it
    # doesn't go back to what it was.
    cdm.pop('orient')
    tdm.pop('orient')

    msg = "adv.rotate.inst2earth gives unexpected REVERSE results for {}"
    for t, c, msg in (
            (td, cd, msg.format('vector_data01')),
            (tdm, cdm, msg.format('vector_data_imu01')),
    ):
        yield data_equiv, t, c, msg


def test_rotate_inst2beam(make_data=False):
    td = tr.dat.copy()
    rotate(td, 'beam', inplace=True)
    tdm = tr.dat_imu.copy()
    rotate(tdm, 'beam', inplace=True)

    if make_data:
        save(td, 'vector_data01_rotate_inst2beam.h5')
        save(tdm, 'vector_data_imu01_rotate_inst2beam.h5')
        return

    cd = load('vector_data01_rotate_inst2beam.h5')
    cdm = load('vector_data_imu01_rotate_inst2beam.h5')

    msg = "adv.rotate.beam2inst gives unexpected REVERSE results for {}"
    for t, c, msg in (
            (td, cd, msg.format('vector_data01')),
            (tdm, cdm, msg.format('vector_data_imu01')),
    ):
        yield data_equiv, t, c, msg


def test_rotate_beam2inst():
    td = load('vector_data01_rotate_inst2beam.h5')
    rotate(td, 'inst', inplace=True)
    tdm = load('vector_data_imu01_rotate_inst2beam.h5')
    rotate(tdm, 'inst', inplace=True)

    cd = tr.dat.copy()
    cdm = tr.dat_imu.copy()

    msg = "adv.rotate.beam2inst gives unexpected results for {}"
    for t, c, msg in (
            (td, cd, msg.format('vector_data01')),
            (tdm, cdm, msg.format('vector_data_imu01')),
    ):
        yield data_equiv, t, c, msg


def test_rotate_earth2principal(make_data=False):
    td = load('vector_data01_rotate_inst2earth.h5')
    td['props']['principal_heading'] = calc_principal_heading(td['vel'])
    rotate(td, 'principal', inplace=True)
    tdm = load('vector_data_imu01_rotate_inst2earth.h5')
    tdm['props']['principal_heading'] = calc_principal_heading(tdm['vel'])
    rotate(tdm, 'principal', inplace=True)

    if make_data:
        save(td, 'vector_data01_rotate_earth2principal.h5')
        save(tdm, 'vector_data_imu01_rotate_earth2principal.h5')
        return

    cd = load('vector_data01_rotate_earth2principal.h5')
    cdm = load('vector_data_imu01_rotate_earth2principal.h5')

    msg = "adv.rotate.earth2principal gives unexpected results for {}"
    for t, c, msg in (
            (td, cd, msg.format('vector_data01')),
            (tdm, cdm, msg.format('vector_data_imu01')),
    ):
        yield data_equiv, t, c, msg


def test_rotate_earth2principal_set_declination():

    declin = 3.875
    td = load('vector_data01_rotate_inst2earth.h5')
    td0 = td.copy()
    td['props']['principal_heading'] = calc_principal_heading(td['vel'])

    td.rotate2('principal', inplace=True)
    td.set_declination(declin)
    td.rotate2('earth', inplace=True)

    td0.set_declination(declin)
    td0['props']['principal_heading'] = calc_principal_heading(td0['vel'])

    data_equiv(td0, td,
               "Something is wrong with declination "
               "handling w/r/t principal_heading.")

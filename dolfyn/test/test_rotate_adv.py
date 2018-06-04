from dolfyn.test import test_adv as tr
from dolfyn.rotate import rotate2 as rotate
from .base import load_tdata as load, save_tdata as save

data_equiv = tr.data_equiv


def test_rotate_inst2earth(make_data=False):
    td = tr.dat.copy()
    rotate(td, 'earth', inplace=True)
    tdm = tr.dat_imu.copy()
    rotate(tdm, 'earth', inplace=True)

    if make_data:
        td.to_hdf5('vector_data01_rotate_inst2earth.h5')
        tdm.to_hdf5('vector_data_imu01_rotate_inst2earth.h5')
        return

    cd = load('vector_data01_rotate_inst2earth.h5')
    cdm = load('vector_data_imu01_rotate_inst2earth.h5')

    msg = "adv.rotate.inst2earth gives unexpected results for {}"
    for t, c, msg in (
            (td, cd, msg.format('vector_data01')),
            (tdm, cdm, msg.format('vector_data_imu01')),
    ):
        yield data_equiv, t, c, msg


def test_rotate_earth2inst(make_data=False):
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


def test_rotate_beam2inst(make_data=False):
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
    rotate(td, 'principal', inplace=True)
    tdm = load('vector_data_imu01_rotate_inst2earth.h5')
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

from dolfyn.test import test_adv as tr
import dolfyn.adv.api as avm
from dolfyn.io.hdf5 import load

rfnm = tr.rfnm
data_equiv = tr.data_equiv


def test_rotate_inst2earth(make_data=False):
    td = tr.dat.copy()
    avm.rotate.inst2earth(td)
    tdm = tr.dat_imu.copy()
    avm.rotate.inst2earth(tdm)

    if make_data:
        td.to_hdf5(rfnm('data/vector_data01_rotate_inst2earth.h5'))
        tdm.to_hdf5(rfnm('data/vector_data_imu01_rotate_inst2earth.h5'))
        return

    cd = load(rfnm('data/vector_data01_rotate_inst2earth.h5'))
    cdm = load(rfnm('data/vector_data_imu01_rotate_inst2earth.h5'))

    msg = "adv.rotate.inst2earth gives unexpected results for {}"
    for t, c, msg in (
            (td, cd, msg.format('vector_data01')),
            (tdm, cdm, msg.format('vector_data_imu01')),
    ):
        yield data_equiv, t, c, msg


def test_rotate_earth2inst(make_data=False):
    td = load(rfnm('data/vector_data01_rotate_inst2earth.h5'))
    avm.rotate.inst2earth(td, reverse=True)
    tdm = load(rfnm('data/vector_data_imu01_rotate_inst2earth.h5'))
    avm.rotate.inst2earth(tdm, reverse=True)

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
    avm.rotate.beam2inst(td, reverse=True)
    tdm = tr.dat_imu.copy()
    avm.rotate.beam2inst(tdm, reverse=True)

    if make_data:
        td.to_hdf5(rfnm('data/vector_data01_rotate_inst2beam.h5'))
        tdm.to_hdf5(rfnm('data/vector_data_imu01_rotate_inst2beam.h5'))
        return

    cd = load(rfnm('data/vector_data01_rotate_inst2beam.h5'))
    cdm = load(rfnm('data/vector_data_imu01_rotate_inst2beam.h5'))

    msg = "adv.rotate.beam2inst gives unexpected REVERSE results for {}"
    for t, c, msg in (
            (td, cd, msg.format('vector_data01')),
            (tdm, cdm, msg.format('vector_data_imu01')),
    ):
        yield data_equiv, t, c, msg


def test_rotate_beam2inst(make_data=False):
    td = load(rfnm('data/vector_data01_rotate_inst2beam.h5'))
    avm.rotate.beam2inst(td)
    tdm = load(rfnm('data/vector_data_imu01_rotate_inst2beam.h5'))
    avm.rotate.beam2inst(tdm)

    cd = tr.dat.copy()
    cdm = tr.dat_imu.copy()

    msg = "adv.rotate.beam2inst gives unexpected results for {}"
    for t, c, msg in (
            (td, cd, msg.format('vector_data01')),
            (tdm, cdm, msg.format('vector_data_imu01')),
    ):
        yield data_equiv, t, c, msg


def test_rotate_earth2principal(make_data=False):
    td = load(rfnm('data/vector_data01_rotate_inst2earth.h5'))
    avm.rotate.earth2principal(td)
    tdm = load(rfnm('data/vector_data_imu01_rotate_inst2earth.h5'))
    avm.rotate.earth2principal(tdm)

    if make_data:
        td.to_hdf5(rfnm('data/vector_data01_rotate_earth2principal.h5'))
        tdm.to_hdf5(rfnm('data/vector_data_imu01_rotate_earth2principal.h5'))
        return

    cd = load(rfnm('data/vector_data01_rotate_earth2principal.h5'))
    cdm = load(rfnm('data/vector_data_imu01_rotate_earth2principal.h5'))

    msg = "adv.rotate.earth2principal gives unexpected results for {}"
    for t, c, msg in (
            (td, cd, msg.format('vector_data01')),
            (tdm, cdm, msg.format('vector_data_imu01')),
    ):
        yield data_equiv, t, c, msg

from dolfyn.test import test_adv as tr
import dolfyn.adv.api as avm
from dolfyn.io.hdf5 import load

rfnm = tr.rfnm
data_equiv = tr.data_equiv


def test_rotate_inst2earth(make_data=False):
    td = tr.dat.copy()
    avm.rotate.inst2earth(td)

    if make_data:
        td.to_hdf5(rfnm('data/vector_data01_rotate_inst2earth.h5'))
        return

    cd = load(rfnm('data/vector_data01_rotate_inst2earth.h5'))

    msg = "adv.rotate.inst2earth gives unexpected results for {}"
    for t, c, msg in (
            (td, cd, msg.format('vector_data01')),
    ):
        yield data_equiv, t, c, msg


def test_rotate_earth2inst(make_data=False):
    td = load(rfnm('data/vector_data01_rotate_inst2earth.h5'))
    avm.rotate.inst2earth(td, reverse=True)

    cd = tr.dat.copy()

    msg = "adv.rotate.inst2earth gives unexpected REVERSE results for {}"
    for t, c, msg in (
            (td, cd, msg.format('vector_data01')),
    ):
        yield data_equiv, t, c, msg


# def test_rotate_inst2beam(make_data=False):
#     td = tr.dat.copy()
#     avm.rotate.beam2inst(td, reverse=True)

#     if make_data:
#         td.to_hdf5(rfnm('data/vector_data01_rotate_inst2beam.h5'))
#         return

#     cd = load(rfnm('data/vector_data01_rotate_inst2beam.h5'))

#     msg = "adv.rotate.beam2inst gives unexpected REVERSE results for {}"
#     for t, c, msg in (
#             (td, cd, msg.format('vector_data01')),
#     ):
#         yield data_equiv, t, c, msg

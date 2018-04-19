from dolfyn.test import test_read_adp as tr
import dolfyn.adp.api as apm
from dolfyn.io.hdf5 import load

rfnm = tr.rfnm
data_equiv = tr.data_equiv


def test_rotate_beam2inst(make_data=False):

    td = tr.dat_rdi.copy()
    apm.beam2inst(td)
    td_sig = tr.dat_sig.copy()
    apm.beam2inst(td_sig)
    td_sigi = tr.dat_sigi.copy()
    apm.beam2inst(td_sigi)

    if make_data:
        td.to_hdf5(rfnm('data/RDI_test01_rotate_beam2inst.h5'))
        td_sig.to_hdf5(rfnm('data/BenchFile01_rotate_beam2inst.h5'))
        td_sigi.to_hdf5(rfnm('data/Sig1000_IMU_rotate_beam2inst.h5'))
        return

    cd_sig = load(rfnm('data/BenchFile01_rotate_beam2inst.h5'))
    cd_sigi = load(rfnm('data/Sig1000_IMU_rotate_beam2inst.h5'))

    msg = "adp.rotate.beam2inst gives unexpected results for {}"
    for t, c, msg in (
            (td, tr.dat_rdi_i, msg.format('RDI_test01')),
            (td_sig, cd_sig, msg.format('BenchFile01')),
            (td_sigi, cd_sigi, msg.format('Sig1000_IMU')),
    ):
        yield data_equiv, t, c, msg


def test_rotate_inst2beam(make_data=False):

    # # The reverse RDI rotation doesn't work b/c of NaN's in one beam
    # # that propagate to others.
    # td = load(rfnm('data/RDI_test01_rotate_beam2inst.h5'))
    # apm.beam2inst(td, reverse=True)
    td_awac = load(rfnm('data/AWAC_test01_earth2inst.h5'))
    apm.beam2inst(td_awac, reverse=True)

    if make_data:
        td_awac.to_hdf5(rfnm('data/AWAC_test01_inst2beam.h5'))
        return

    cd_awac = load(rfnm('data/AWAC_test01_inst2beam.h5'))

    msg = "adp.rotate.beam2inst gives unexpected REVERSE results for {}"
    for t, c, msg in (
            # (td, dat_rdi, msg.format('RDI_test01')),
            (td_awac, cd_awac, msg.format('AWAC_test01')),
    ):
        yield data_equiv, t, c, msg


def test_rotate_earth2inst(make_data=False):
    td = load(rfnm('data/RDI_test01_rotate_inst2earth.h5'))
    apm.inst2earth(td, reverse=True)
    # tdwr2 = load(rfnm('data/winriver02_rotate_ship2earth.h5'))
    # apm.inst2earth(tdwr2, reverse=True)
    # This AWAC is in earth coords.
    td_awac = tr.dat_awac.copy()
    apm.inst2earth(td_awac, reverse=True)

    if make_data:
        td_awac.to_hdf5(rfnm('data/AWAC_test01_earth2inst.h5'))
        return

    cd_awac = load(rfnm('data/AWAC_test01_earth2inst.h5'))

    msg = "adp.rotate.inst2earth gives unexpected REVERSE results for {}"
    for t, c, msg in (
            (td, tr.dat_rdi_i, msg.format('RDI_test01')),
            #(tdwr2, dat_wr2, msg.format('winriver02')),
            (td_awac, cd_awac, msg.format('AWAC_test01')),
    ):
        yield data_equiv, t, c, msg


def test_rotate_inst2earth(make_data=False):

    td = tr.dat_rdi_i.copy()
    apm.inst2earth(td)
    tdwr2 = tr.dat_wr2.copy()
    apm.inst2earth(tdwr2)
    td_sig = load(rfnm('data/BenchFile01_rotate_beam2inst.h5'))
    apm.inst2earth(td_sig)
    td_sigi = load(rfnm('data/Sig1000_IMU_rotate_beam2inst.h5'))
    apm.inst2earth(td_sigi)
    td_awac = load(rfnm('data/AWAC_test01_earth2inst.h5'))
    apm.inst2earth(td_awac)

    if make_data:
        td.to_hdf5(rfnm('data/RDI_test01_rotate_inst2earth.h5'))
        td_sig.to_hdf5(rfnm('data/BenchFile01_rotate_inst2earth.h5'))
        td_sigi.to_hdf5(rfnm('data/Sig1000_IMU_rotate_inst2earth.h5'))
        tdwr2.to_hdf5(rfnm('data/winriver02_rotate_ship2earth.h5'))
        return

    cd = load(rfnm('data/RDI_test01_rotate_inst2earth.h5'))
    cdwr2 = load(rfnm('data/winriver02_rotate_ship2earth.h5'))
    cd_sig = load(rfnm('data/BenchFile01_rotate_inst2earth.h5'))
    cd_sigi = load(rfnm('data/Sig1000_IMU_rotate_inst2earth.h5'))
    cd_awac = tr.dat_awac

    msg = "adp.rotate.inst2earth gives unexpected results for {}"
    for t, c, msg in (
            (td, cd, msg.format('RDI_test01')),
            (tdwr2, cdwr2, msg.format('winriver02')),
            (td_awac, cd_awac, msg.format('AWAC_test01')),
            (td_sig, cd_sig, msg.format('BenchFile01')),
            (td_sigi, cd_sigi, msg.format('Sig1000_IMU')),
    ):
        yield data_equiv, t, c, msg

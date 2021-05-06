from dolfyn.h5.test import test_read_adp as tr
from dolfyn.h5.test.base import load_tdata as load, save_tdata as save, data_equiv
from dolfyn.h5 import calc_principal_heading
import numpy as np


def test_rotate_beam2inst(make_data=False):

    td = tr.dat_rdi.rotate2('inst')
    td_sig = tr.dat_sig.rotate2('inst')
    td_sigi = tr.dat_sigi.rotate2('inst')
    td_sigi_echo_bt = tr.dat_sigi_echo_bt.rotate2('inst')

    if make_data:
        save(td, 'RDI_test01_rotate_beam2inst.h5')
        save(td_sig, 'BenchFile01_rotate_beam2inst.h5')
        save(td_sigi, 'Sig1000_IMU_rotate_beam2inst.h5')
        save(td_sigi_echo_bt, 'VelEchoBT01_rotate_beam2inst.h5')
        return

    cd_sig = load('BenchFile01_rotate_beam2inst.h5')
    cd_sigi = load('Sig1000_IMU_rotate_beam2inst.h5')
    cd_sigi_echo_bt = load('VelEchoBT01_rotate_beam2inst.h5')

    msg = "adp.rotate.beam2inst gives unexpected results for {}"
    for t, c, msg in (
            (td, tr.dat_rdi_i, msg.format('RDI_test01')),
            (td_sig, cd_sig, msg.format('BenchFile01')),
            (td_sigi, cd_sigi, msg.format('Sig1000_IMU')),
            (td_sigi_echo_bt, cd_sigi_echo_bt, msg.format('VelEchoBT01')),
    ):
        yield data_equiv, t, c, msg


def test_rotate_inst2beam(make_data=False):

    td = load('RDI_test01_rotate_beam2inst.h5')
    td.rotate2('beam', inplace=True)
    td_awac = load('AWAC_test01_earth2inst.h5')
    td_awac.rotate2('beam', inplace=True)
    td_sig = load('BenchFile01_rotate_beam2inst.h5')
    td_sig.rotate2('beam', inplace=True)
    td_sigi = load('Sig1000_IMU_rotate_beam2inst.h5')
    td_sigi.rotate2('beam', inplace=True)

    if make_data:
        save(td_awac, 'AWAC_test01_inst2beam.h5')
        return

    cd_td = tr.dat_rdi.copy()
    cd_awac = load('AWAC_test01_inst2beam.h5')
    cd_sig = tr.dat_sig.copy()
    cd_sigi = tr.dat_sigi.copy()

    # # The reverse RDI rotation doesn't work b/c of NaN's in one beam
    # # that propagate to others, so we impose that here.
    cd_td['vel'][:, np.isnan(cd_td['vel']).any(0)] = np.NaN

    msg = "adp.rotate.beam2inst gives unexpected REVERSE results for {}"
    for t, c, msg in (
            (td, cd_td, msg.format('RDI_test01')),
            (td_awac, cd_awac, msg.format('AWAC_test01')),
            (td_sig, cd_sig, msg.format('BenchFile01')),
            (td_sigi, cd_sigi, msg.format('Sig1000_IMU')),
    ):
        yield data_equiv, t, c, msg


def test_rotate_inst2earth(make_data=False):

    td = tr.dat_rdi_i.rotate2('earth')
    tdwr2 = tr.dat_wr2.rotate2('earth')
    td_sig = load('BenchFile01_rotate_beam2inst.h5')
    td_sig.rotate2('earth', inplace=True)
    td_sigi = load('Sig1000_IMU_rotate_beam2inst.h5')
    td_sigi.rotate2('earth', inplace=True)
    td_awac = tr.dat_awac.rotate2('inst')

    if make_data:
        save(td, 'RDI_test01_rotate_inst2earth.h5')
        save(td_sig, 'BenchFile01_rotate_inst2earth.h5')
        save(td_sigi, 'Sig1000_IMU_rotate_inst2earth.h5')
        save(tdwr2, 'winriver02_rotate_ship2earth.h5')
        save(td_awac, 'AWAC_test01_earth2inst.h5')
        return
    td_awac.rotate2('earth', inplace=True)

    cd = load('RDI_test01_rotate_inst2earth.h5')
    cdwr2 = load('winriver02_rotate_ship2earth.h5')
    cd_sig = load('BenchFile01_rotate_inst2earth.h5')
    cd_sigi = load('Sig1000_IMU_rotate_inst2earth.h5')
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


def test_rotate_earth2inst():
    td = (load('RDI_test01_rotate_inst2earth.h5')
          .rotate2('inst', inplace=True))
    # tdwr2 = load('winriver02_rotate_ship2earth.h5')
    # tdwr2.rotate2('inst', inplace=True)
    # This AWAC is in earth coords.
    td_awac = tr.dat_awac.rotate2('inst')
    td_sig = load('BenchFile01_rotate_inst2earth.h5')
    td_sig.rotate2('inst', inplace=True)
    td_sigi = load('Sig1000_IMU_rotate_inst2earth.h5')
    td_sigi.rotate2('inst', inplace=True)

    cd_awac = load('AWAC_test01_earth2inst.h5')
    cd_sig = load('BenchFile01_rotate_beam2inst.h5')
    cd_sigi = load('Sig1000_IMU_rotate_beam2inst.h5')

    assert (np.abs(cd_sigi['orient'].pop('accel') - \
                   td_sigi['orient'].pop('accel')) < 1e-3).all(), \
                  "adp.rotate.inst2earth gives unexpected ACCEL results for 'Sig1000_IMU_rotate_beam2inst.h5'"

    assert (np.abs(cd_sigi['orient'].pop('accel_b5') - \
                   td_sigi['orient'].pop('accel_b5')) < 1e-3).all(), \
                   "adp.rotate.inst2earth gives unexpected ACCEL results for 'Sig1000_IMU_rotate_beam2inst.h5'"


    msg = "adp.rotate.inst2earth gives unexpected REVERSE results for {}"
    for t, c, msg in (
            (td, tr.dat_rdi_i, msg.format('RDI_test01')),
            #(tdwr2, dat_wr2, msg.format('winriver02')),
            (td_awac, cd_awac, msg.format('AWAC_test01')),
            (td_sig, cd_sig, msg.format('BenchFile01')),
            (td_sigi, cd_sigi, msg.format('Sig1000_IMU')),
    ):
        yield data_equiv, t, c, msg


# def test_rotate_earth2principal(make_data=False):

#     td_rdi = load('RDI_test01_rotate_inst2earth.h5')
#     td_sig = load('BenchFile01_rotate_inst2earth.h5')
#     td_awac = tr.dat_awac.copy()

#     td_rdi.props['principal_heading'] = calc_principal_heading(
#         td_rdi.vel.mean(1))
#     td_sig.props['principal_heading'] = calc_principal_heading(
#         td_sig.vel.mean(1))
#     td_awac.props['principal_heading'] = calc_principal_heading(
#         td_sig.vel.mean(1), tidal_mode=False)

#     td_rdi.rotate2('principal', inplace=True)
#     td_sig.rotate2('principal', inplace=True)
#     td_awac.rotate2('principal', inplace=True)

#     if make_data:
#         save(td_rdi, 'RDI_test01_rotate_earth2principal.h5')
#         save(td_sig, 'BenchFile01_rotate_earth2principal.h5')
#         save(td_awac, 'AWAC_test01_earth2principal.h5')
#         return

#     cd_rdi = load('RDI_test01_rotate_earth2principal.h5')
#     cd_sig = load('BenchFile01_rotate_earth2principal.h5')
#     cd_awac = load('AWAC_test01_earth2principal.h5')
    

#     msg = "adp.rotate.earth2principal gives unexpected results for {}"
#     for t, c, msg in (
#             (td_rdi, cd_rdi, msg.format('RDI_test01')),
#             (td_awac, cd_awac, msg.format('AWAC_test01')),
#             (td_sig, cd_sig, msg.format('BenchFile01')),
#     ):
#         yield data_equiv, t, c, msg

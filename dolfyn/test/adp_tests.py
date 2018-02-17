import dolfyn.adp.api as apm
import dolfyn.data.base
from base import ResourceFilename
from dolfyn.io.hdf5 import load

rfnm = ResourceFilename('dolfyn.test')
exdt = ResourceFilename('dolfyn')

dat_rdi = load(rfnm('data/RDI_test01.h5'))
dat_rdi_i = load(rfnm('data/RDI_test01_rotate_beam2inst.h5'))
dat_awac = load(rfnm('data/AWAC_test01.h5'))
dat_sig = load(rfnm('data/BenchFile01.h5'))
dat_sigi = load(rfnm('data/Sig1000_IMU.h5'))
dat_wr1 = load(rfnm('data/winriver01.h5'))
dat_wr2 = load(rfnm('data/winriver02.h5'))


def data_equiv(dat1, dat2, message=''):
    assert dat1 == dat2, message


def read_test(make_data=False):

    td_rdi = apm.read(exdt('example_data/RDI_test01.000'))
    td_sig = apm.read(exdt('example_data/BenchFile01.ad2cp'))
    td_sigi = apm.read(exdt('example_data/Sig1000_IMU.ad2cp'))
    td_awac = apm.read(exdt('example_data/AWAC_test01.wpr'))
    td_wr1 = apm.read(exdt('example_data/winriver01.PD0'))
    td_wr2 = apm.read(exdt('example_data/winriver02.PD0'))

    if make_data:
        td_rdi.to_hdf5(rfnm('data/RDI_test01.h5'))
        td_sig.to_hdf5(rfnm('data/BenchFile01.h5'))
        td_sigi.to_hdf5(rfnm('data/Sig1000_IMU.h5'))
        td_awac.to_hdf5(rfnm('data/AWAC_test01.h5'))
        td_wr1.to_hdf5(rfnm('data/winriver01.h5'))
        td_wr2.to_hdf5(rfnm('data/winriver02.h5'))
        return

    def msg(infile):
        testfile = infile.split('.')[0] + '.h5'
        return ("The output of read('{}') does not match '{}'."
                .format(infile, testfile))
    for dat1, dat2, msg in [
            (td_rdi, dat_rdi,
             msg('RDI_test01.000')),
            (td_sig, dat_sig,
             msg('BenchFile01.ad2cp')),
            (td_sigi, dat_sigi,
             msg('Sig1000_IMU.ad2cp')),
            (td_awac, dat_awac,
             msg('AWAC_test01.wpr')),
            (td_wr1, dat_wr1,
             msg('winriver01.PD0')),
            (td_wr2, dat_wr2,
             msg('winriver02.PD0')),
    ]:
        yield data_equiv, dat1, dat2, msg


def rotate_beam2inst_test(make_data=False):

    td = dat_rdi.copy()
    apm.beam2inst(td)

    if make_data:
        td.to_hdf5(rfnm('data/RDI_test01_rotate_beam2inst.h5'))
        return

    assert td == dat_rdi_i, "adp.rotate.beam2inst gives unexpected results!"


def rotate_earth2inst_test(make_data=False):
    td = load(rfnm('data/RDI_test01_rotate_inst2earth.h5'))
    apm.inst2earth(td, reverse=True)
    # tdwr2 = load(rfnm('data/winriver02_rotate_ship2earth.h5'))
    # apm.inst2earth(tdwr2, reverse=True)
    # This AWAC is in earth coords.
    td_awac = dat_awac.copy()
    apm.inst2earth(td_awac, reverse=True)

    if make_data:
        td_awac.to_hdf5(rfnm('data/AWAC_test01_earth2inst.h5'))

    cd_awac = load(rfnm('data/AWAC_test01_earth2inst.h5'))

    msg = "adp.rotate.earth2inst gives unexpected results for {}"
    for t, c, msg in (
            (td, dat_rdi_i, msg.format('RDI_test01')),
            #(tdwr2, dat_wr2, msg.format('winriver02')),
            (td_awac, cd_awac, msg.format('AWAC_test01')),
    ):
        yield data_equiv, t, c, msg


def rotate_inst2earth_test(make_data=False):

    td = dat_rdi_i.copy()
    apm.inst2earth(td)
    tdwr2 = dat_wr2.copy()
    apm.inst2earth(tdwr2)
    td_awac = load(rfnm('data/AWAC_test01_earth2inst.h5'))
    apm.inst2earth(td_awac)

    if make_data:
        td.to_hdf5(rfnm('data/RDI_test01_rotate_inst2earth.h5'))
        tdwr2.to_hdf5(rfnm('data/winriver02_rotate_ship2earth.h5'))
        return

    cd = load(rfnm('data/RDI_test01_rotate_inst2earth.h5'))
    cdwr2 = load(rfnm('data/winriver02_rotate_ship2earth.h5'))
    cd_awac = dat_awac

    msg = "adp.rotate.inst2earth gives unexpected results for {}"
    for t, c, msg in (
            (td, cd, msg.format('RDI_test01')),
            (tdwr2, cdwr2, msg.format('winriver02')),
            (td_awac, cd_awac, msg.format('AWAC_test01-reverse')),
    ):
        yield data_equiv, t, c, msg


if __name__ == '__main__':

    for func, dat1, dat2, msg in rotate_earth2inst_test():
        func(dat1, dat2, msg)

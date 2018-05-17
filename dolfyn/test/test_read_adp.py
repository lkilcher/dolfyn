import dolfyn.adp.api as apm
try:
    from .base import ResourceFilename
except (ValueError, ImportError):
    from base import ResourceFilename
from dolfyn.io.hdf5 import load
import pyDictH5.base as pdh5_base

rfnm = ResourceFilename('dolfyn.test')
exdt = ResourceFilename('dolfyn')

pdh5_base.debug_level = 1

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


if __name__ == '__main__':

    for func, dat1, dat2, msg in read_test():
        func(dat1, dat2, msg)

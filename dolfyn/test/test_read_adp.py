from dolfyn.main import read_example as read
import dolfyn.test.base as tb

load = tb.load_tdata
save = tb.save_tdata

dat_rdi = load('RDI_test01.h5')
dat_rdi_i = load('RDI_test01_rotate_beam2inst.h5')
dat_awac = load('AWAC_test01.h5')
dat_sig = load('BenchFile01.h5')
dat_sigi = load('Sig1000_IMU.h5')
dat_wr1 = load('winriver01.h5')
dat_wr2 = load('winriver02.h5')


def test_read(make_data=False):

    td_rdi = read('RDI_test01.000')
    td_sig = read('BenchFile01.ad2cp')
    td_sigi = read('Sig1000_IMU.ad2cp')
    td_awac = read('AWAC_test01.wpr')
    td_wr1 = read('winriver01.PD0')
    td_wr2 = read('winriver02.PD0')

    if make_data:
        save(td_rdi, 'RDI_test01.h5')
        save(td_sig, 'BenchFile01.h5')
        save(td_sigi, 'Sig1000_IMU.h5')
        save(td_awac, 'AWAC_test01.h5')
        save(td_wr1, 'winriver01.h5')
        save(td_wr2, 'winriver02.h5')
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
        yield tb.data_equiv, dat1, dat2, msg


if __name__ == '__main__':

    for func, dat1, dat2, msg in test_read():
        func(dat1, dat2, msg)

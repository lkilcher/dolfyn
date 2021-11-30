from dolfyn.main import read_example as read
import dolfyn.test.base as tb
import sys
import warnings
import numpy as np
warnings.simplefilter('ignore', UserWarning)

load = tb.load_tdata
save = tb.save_tdata

dat_rdi_orientraw = load('RDI_test01.h5')
dat_rdi = dat_rdi_orientraw.copy()
dat_rdi['orient'].pop('raw')
dat_rdi_bt = load('RDI_withBT.h5')
dat_rdi_i = load('RDI_test01_rotate_beam2inst.h5')
dat_awac = load('AWAC_test01.h5')
dat_awac_ud = load('AWAC_test01_ud.h5')
dat_sig = load('BenchFile01.h5')
dat_sigi = load('Sig1000_IMU.h5')
dat_sigi_ud = load('Sig1000_IMU_ud.h5')
dat_sigi_echo_bt = load('VelEchoBT01.h5')
dat_sig5_leiw = load('Sig500_last_ensemble_is_whole.h5')
dat_wr1 = load('winriver01.h5')
dat_wr2 = load('winriver02.h5')


def test_badtime():

    dat = read('Sig1000_BadTime01.ad2cp')

    assert np.isnan(dat.mpltime[199]), "A good timestamp was found where a bad value is expected."


def test_read(make_data=False):

    # This uses the built-in declination!
    td_rdi_orientraw = read('RDI_test01.000')
    td_rdi = td_rdi_orientraw.copy()
    td_rdi_bt = read('RDI_withBT.000')

    td_sig = read('BenchFile01.ad2cp')
    td_sigi = read('Sig1000_IMU.ad2cp', userdata=False)
    td_sigi_ud = read('Sig1000_IMU.ad2cp')
    td_sigi_echo_bt = read('VelEchoBT01.ad2cp')

    # Make sure we read all the way to the end of the file.
    # This file ends exactly at the end of an ensemble.
    td_sig5_leiw = read('Sig500_last_ensemble_is_whole.ad2cp')
    
    td_awac = read('AWAC_test01.wpr', userdata=False)
    td_awac_ud = read('AWAC_test01.wpr')
    td_wr1 = read('winriver01.PD0')
    td_wr2 = read('winriver02.PD0')

    # We don't need the raw orientation data for most tests.
    td_rdi['orient'].pop('raw')
    td_rdi_bt['orient'].pop('raw')
    td_sig['orient'].pop('raw')
    td_awac['orient'].pop('raw')
    td_awac_ud['orient'].pop('raw')
    td_wr1['orient'].pop('raw')
    td_wr2['orient'].pop('raw')

    if make_data:
        save(td_rdi_orientraw, 'RDI_test01.h5')
        save(td_rdi_bt, 'RDI_withBT.h5')
        save(td_sig, 'BenchFile01.h5')
        save(td_sigi, 'Sig1000_IMU.h5')
        save(td_sigi_ud, 'Sig1000_IMU_ud.h5')
        save(td_sigi_echo_bt, 'VelEchoBT01.h5')
        save(td_sig5_leiw, 'Sig500_last_ensemble_is_whole.h5')
        save(td_awac, 'AWAC_test01.h5')
        save(td_awac_ud, 'AWAC_test01_ud.h5')
        save(td_wr1, 'winriver01.h5')
        save(td_wr2, 'winriver02.h5')
        return

    if sys.version_info.major == 2:
        # This is a HACK for Py2
        # for some reason a very small numer of the values in temp_mag
        # are not the same for py2?
        # !CLEANUP!
        # BUG that's loading different data??!
        td_sigi['sys']['temp_mag'] = dat_sigi['sys']['temp_mag'].copy()
        td_sigi_ud['sys']['temp_mag'] = dat_sigi_ud['sys']['temp_mag'].copy()
        td_sigi_echo_bt['sys']['temp_mag'] = dat_sigi_echo_bt['sys']['temp_mag'].copy()

    def msg(infile):
        testfile = infile.split('.')[0] + '.h5'
        return ("The output of read('{}') does not match '{}'."
                .format(infile, testfile))
    for dat1, dat2, msg in [
            (td_rdi, dat_rdi,
             msg('RDI_test01.000')),
            (td_rdi_bt, dat_rdi_bt,
             msg('RDI_withBT.000')),
            (td_rdi_orientraw, dat_rdi_orientraw,
             msg('RDI_test01.000+orientraw')),
            (td_sig, dat_sig,
             msg('BenchFile01.ad2cp')),
            (td_sigi, dat_sigi,
             msg('Sig1000_IMU.ad2cp')),
            (td_sigi_ud, dat_sigi_ud,
             msg('Sig1000_IMU_ud.ad2cp')),
            (td_sigi_echo_bt, dat_sigi_echo_bt,
             msg('VelEchoBT01.ad2cp')),
            (td_sig5_leiw, dat_sig5_leiw,
             msg('Sig500_last_ensemble_is_whole.ad2cp')),
            (td_awac, dat_awac,
             msg('AWAC_test01.wpr')),
            (td_awac_ud, dat_awac_ud,
             msg('AWAC_test01.wpr+userdata')),
            (td_wr1, dat_wr1,
             msg('winriver01.PD0')),
            (td_wr2, dat_wr2,
             msg('winriver02.PD0')),
    ]:
        yield tb.data_equiv, dat1, dat2, msg


if __name__ == '__main__':

    for func, dat1, dat2, msg in test_read():
        func(dat1, dat2, msg)

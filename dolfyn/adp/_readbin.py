#import scipy.io as io
import numpy as np
import datetime
from ..data.time import date2num
from os.path import getsize
from .base import adcp_header, adcp_config, adcp_raw
from ._read_bin import eofException, bin_reader
from scipy import nanmean
import warnings

# Four pound symbols ("####"), indicate a duplication of a comment from
# Rich Pawlawicz' rdadcp routines.

### This causes the time information to be returned in python's
### datenum format.  See pylab's date2num and num2date functions for
### more information.
# matlab or python date format:
time_offset = 0

# time_offset=366 ### Uncommenting this line puts the data in "Matlab's
# datenum" format.

#century=1900
century = 2000

data_defs = {'number': ([], 'index', 'uint32'),
             'rtc': ([7], 'index', 'uint16'),
             'BIT': ([], 'index', 'bool'),
             'ssp': ([], 'index', 'uint16'),
             'depth_m': ([], 'main', 'float32'),
             'pitch_deg': ([], 'orient', 'float32'),
             'roll_deg': ([], 'orient', 'float32'),
             'heading_deg': ([], 'orient', 'float32'),
             'temperature_C': ([], 'envir', 'float32'),
             'salinity': ([], 'envir', 'float32'),
             'mpt_sec': ([], 'index', 'float32'),
             'heading_std': ([], 'orient', 'float32'),
             'pitch_std': ([], 'orient', 'float32'),
             'roll_std': ([], 'orient', 'float32'),
             'adc': ([8], 'index', 'uint16'),
             'error_status_wd': ([], 'signal', 'float32'),
             'pressure': ([], 'main', 'float32'),
             'pressure_std': ([], 'main', 'float32'),
             '_u': (['nc', 4], 'main', 'float32'),
             #'v':(['nc',],'main','float32'),
             #'w':(['nc',],'main','float32'),
             #'err_vel':(['nc',],'main','float32'),
             #'beam1vel': (['nc', ], 'beam', 'float32'),
             #'beam2vel': (['nc', ], 'beam', 'float32'),
             #'beam3vel': (['nc', ], 'beam', 'float32'),
             #'beam4vel': (['nc', ], 'beam', 'float32'),
             'echo': (['nc', 4], 'signal', 'uint8'),
             'corr': (['nc', 4], 'signal', 'uint8'),
             'prcnt_gd': (['nc', 4], 'signal', 'uint8'),
             'status': (['nc', 4], 'signal', 'float32'),
             'bt_range': ([4], 'main', 'float32'),
             'bt_vel': ([4], 'main', 'float32'),
             'bt_corr': ([4], 'signal', 'uint8'),
             'bt_ampl': ([4], 'signal', 'uint8'),
             'bt_perc_gd': ([4], 'signal', 'uint8'),
             'stime': ([], 'main', 'float64'),
             'etime': ([], 'main', 'float64'),
             'mpltime': ([], '_essential', 'float64'),
             'slatitude': ([], 'orient', 'float64'),
             'slongitude': ([], 'orient', 'float64'),
             'elatitude': ([], 'orient', 'float64'),
             'elongitude': ([], 'orient', 'float64'),
             'ntime': ([], 'main', 'float64'),
             'flags': ([], 'signal', 'float32'),
             }


class ADCPWarning(UserWarning):
    pass


class ADCPWarningNoCode(ADCPWarning):

    def __init__(self, code):
        self.code = code


class variable_setlist(set):

    def __iadd__(self, vals):
        if vals[0] not in self:
            self |= set(vals)
        return self


def get_size(name, n=None, ncell=0):
    sz = data_defs[name][0]
    if 'nc' in sz:
        sz.insert(sz.index('nc'), ncell)
        sz.remove('nc')
    if n is None:
        return tuple(sz)
    return tuple(sz + [n])


class ensemble(object):

    n_avg = 1
    k = -1  # This is the counter for filling the ensemble object

    def __getitem__(self, nm):
        return getattr(self, nm)

    def __init__(self, navg, n_cells):
        if navg is None or navg == 0:
            navg = 1
        self.n_avg = navg
        for nm in data_defs:
            setattr(self, nm, np.empty(get_size(nm, n=navg, ncell=n_cells)))

    def clean_data(self,):
        self._u[self._u == -32.768] = np.NaN


class adcp_loader(object):
    _n_beams = 4  # Placeholder for 5-beam adcp, not currently used.
    _pos = 0
    progress = 0
    _cfgnames = dict.fromkeys([4, 5], 'bb-adcp')
    _cfgnames.update(dict.fromkeys([8, 9, 16], 'wh-adcp'))
    _cfgnames.update(dict.fromkeys([14, 23], 'os-adcp'))
    _cfac = 180 / 2 ** 31
    _source = 0
    _fixoffset = 0
    _nbyte = 0
    _winrivprob = False
    _search_num = 3000  # Maximum distance? to search
    __debug = False
    _verbose = False
    vars_read = variable_setlist(['mpltime'])

    def mean(self, dat):
        if self.n_avg == 1:
            return dat[..., 0]
        if np.isnan(dat).any():
            return nanmean(dat, axis=-1)
        return np.mean(dat, axis=-1)

    def print_progress(self,):
        if (self.f.tell() - self.progress) < 1048576:
            return
        self.progress = self.f.tell()
        print('pos %0.0fmb/%0.0fmb\r' %
              (self.f.tell() / 1048576., self._filesize / 1048576.))

    def print_pos(self, byte_offset=-1):
        """
        Print the position in the file, used for debugging.
        """
        if hasattr(self, 'ensemble'):
            k = self.ensemble.k
        else:
            k = 0
        print('pos: %d, pos_: %d, nbyte: %d, k: %d, byte_offset: %d' %
              (self.f.tell(), self._pos, self._nbyte, k, byte_offset))

    def read_dat(self, id):

        function_map = {0: (self.read_fixed, []),   # 0000
                        128: (self.read_var, []),     # 0080
                        256: (self.read_vel, []),     # 0100
                        512: (self.read_corr, []),    # 0200
                        768: (self.read_echo, []),    # 0300
                        1024: (self.read_prcnt_gd, []),  # 0400
                        1280: (self.read_status, []),  # 0500
                        1536: (self.read_bottom, []),  # 0600
                        8192: (self.read_vmdas, []),   # 2000
                        8448: (self.read_winriver, [38]),  # 2100
                        8449: (self.read_winriver, [97]),  # 2101
                        8450: (self.read_winriver, [45]),  # 2102
                        8451: (self.read_winriver, [60]),  # 2103
                        8452: (self.read_winriver, [38]),  # 2104
                        # Loading of these data is currently not implemented:
                        1793: (self.skip_Ncol, [4]),  # 0701 number of pings
                        1794: (self.skip_Ncol, [4]),  # 0702 sum of squared vel
                        1795: (self.skip_Ncol, [4]),  # 0703 sum of velocities
                        2560: (self.skip_Ncol, []),  # 0A00 Beam 5 velocity
                        769: (self.skip_Ncol, []),  # 0301 Beam 5 Number of good pings
                        770: (self.skip_Ncol, []),  # 0302 Beam 5 Sum of squared velocities
                        771: (self.skip_Ncol, []),  # 0303 Beam 5 Sum of velocities
                        524: (self.skip_Nbyte, [4]),  # 020C Ambient sound profile
                        12288: (self.skip_Nbyte, [32]),
                        # 3000 Fixed attitude data format for OS-ADCPs
                        # #### This is pretty idiotic - for OS-ADCPs
                        # (phase 2) they suddenly decided to code the
                        # number of bytes into the header ID word. And
                        # then they don't really document what they
                        # did! So, this is cruft of a high order, and
                        # although it works on the one example I have
                        # - caveat emptor....
                        }
        ## Call the correct function:
        if id in function_map:
            function_map.get(id)[0](*function_map[id][1])
        else:
            self.read_nocode(id)

    def read_nocode(self, id):
        #### There appear to be codes 0340-03FC to deal with. I am not
        #### going to decode them, but I am going to try to figure out
        #### how many bytes to skip.
        # Does he mean "3040-30FC", or is the code wrong?  Hopefully the
        # former.
        if hex(id)[2:4] == '30':
            # I want to count the number of 1s in the middle 4 bits of the 2nd
            # two bytes.
            # 60 is a 0b00111100 mask
            nflds = bin(id[3] & 60).count('1') + bin(id[4] & 60).count('1')
            # I want to count the number of 1s in the highest 2 bits of byte 3
            dfac = bin(id[3] & 3).count('1')  # 3 is a 0b00000011 mask
            self.skip_Nbyte(12 * nflds * dfac)
        else:
            print('Unrecognized ID code: %0.4X\n' % id)

    def read_fixed(self,):
        if hasattr(self, 'configsize'):  # and False:
            # Skipping the cfgseg was something I added,
            # because it seemed unnecessary to read it every
            # time, so I just skip it after the first read.
            # If this causes problems I may need to remove this.
            # The other option may be that if a problem is encountered, I could
            # come back here and re-read the header.
            self.f.seek(self.configsize, 1)
            self._nbyte = self.configsize
        else:
            self.read_cfgseg()
        if self.__debug == 1:
            print(self._pos)
        self._nbyte += 2

    def read_var(self,):
        """ Read variable leader """
        fd = self.f
        self.ensemble.k += 1  # Increment k.
        ens = self.ensemble
        k = ens.k
        self.vars_read += ['number',
                           'rtc',
                           'number',
                           'BIT',
                           'ssp',
                           'depth_m',
                           'heading_deg',
                           'pitch_deg',
                           'roll_deg',
                           'salinity',
                           'temperature_C',
                           'mpt_sec',
                           'heading_std',
                           'pitch_std',
                           'roll_std',
                           'adc']
        ens.number[k] = fd.read_ui16(1)
        ens.rtc[:, k] = fd.read_ui8(7)
        ens.number[k] += 65535 * fd.read_ui8(1)
        ens.BIT[k] = fd.read_ui16(1)
        ens.ssp[k] = fd.read_ui16(1)
        ens.depth_m[k] = fd.read_ui16(1) * 0.1
        ens.heading_deg[k] = fd.read_ui16(1) * 0.01
        ens.pitch_deg[k] = fd.read_i16(1) * 0.01
        ens.roll_deg[k] = fd.read_i16(1) * 0.01
        ens.salinity[k] = fd.read_i16(1)
        ens.temperature_C[k] = fd.read_i16(1) * 0.01
        ens.mpt_sec[k] = (fd.read_ui8(3) * np.array([60, 1, .01])).sum()
        ens.heading_std[k] = fd.read_ui8(1)
        ens.pitch_std[k] = fd.read_i8(1) * 0.1
        ens.roll_std[k] = fd.read_i8(1) * 0.1
        ens.adc[:, k] = fd.read_ui8(8)
        self._nbyte = 2 + 40
        cfg = self.cfg

        if cfg['name'] == 'bb-adcp':
            if cfg['prog_ver'] >= 5.55:
                fd.seek(15, 1)
                cent = fd.read_ui8(1)
                ens.rtc[:, k] = fd.read_ui8(7)
                ens.rtc[0, k] = ens.rtc[0, k] + cent * 100
                self._nbyte += 23
        elif cfg['name'] == 'wh-adcp':
            ens.error_status_wd[k] = fd.read_ui32(1)
            self.vars_read += ['error_status_wd', 'pressure', 'pressure_std', ]
            self._nbyte += 4
            if (np.fix(cfg['prog_ver']) == [8, 16]).any():
                if cfg['prog_ver'] >= 8.13:  # Added pressure sensor stuff in 8.13
                    fd.seek(2, 1)
                    ens.pressure[k] = fd.read_ui32(1)
                    ens.pressure_std[k] = fd.read_ui32(1)
                    self._nbyte += 10
                if cfg['prog_ver'] >= 8.24:  # Spare byte added 8.24
                    fd.seek(1, 1)
                    self._nbyte += 1
                if cfg['prog_ver'] >= 16.05:  # Added more fields with century in clock
                    cent = fd.read_ui8(1)
                    ens.rtc[:, k] = fd.read_ui8(7)
                    ens.rtc[0, k] = ens.rtc[0, k] + cent * 100
                    self._nbyte += 8
            elif np.fix(cfg['prog_ver']) == 9:
                fd.seek(2, 1)
                ens.pressure[k] = fd.read_ui32(1)
                ens.pressure_std[k] = fd.read_ui32(1)
                self._nbyte += 10
                if cfg['prog_ver'] >= 9.10:  # Spare byte added...
                    fd.seek(1, 1)
                    self._nbyte += 1
        elif cfg['name'] == 'os-adcp':
            fd.seek(16, 1)  # 30 bytes all set to zero, 14 read above
            self._nbyte += 16
            if cfg['prog_ver'] > 23:
                fd.seek(2, 1)
                self._nbyte += 2

    def read_vel(self,):
        ens = self.ensemble
        ## if self.cfg['coord_sys'] == 'beam':
        ##     var_nms = ['beam1vel', 'beam2vel', 'beam3vel', 'beam4vel']
        ## else:
        ##     var_nms = ['u', 'v', 'w', 'err_vel']
        self.vars_read += ['_u']
        k = ens.k
        ens._u[:, :, k] = np.array(self.f.read_i16(4 * self.cfg['n_cells'])
                                   ).reshape((self.cfg['n_cells'], 4)) * .001
        self._nbyte = 2 + 4 * self.cfg['n_cells'] * 2

    def read_corr(self,):
        k = self.ensemble.k
        self.vars_read += ['corr']
        self.ensemble.corr[:, :, k] = np.array(self.f.read_ui8(4 * self.cfg['n_cells'])
                                               ).reshape((self.cfg['n_cells'], 4))
        self._nbyte = 2 + 4 * self.cfg['n_cells']

    def read_echo(self,):
        k = self.ensemble.k
        self.vars_read += ['echo']
        self.ensemble.echo[:, :, k] = np.array(self.f.read_ui8(4 * self.cfg['n_cells'])
                                              ).reshape((self.cfg['n_cells'], 4))
        self._nbyte = 2 + 4 * self.cfg['n_cells']

    def read_prcnt_gd(self,):
        self.vars_read += ['prcnt_gd']
        self.ensemble.prcnt_gd[:, :, self.ensemble.k] = np.array(
            self.f.read_ui8(4 * self.cfg['n_cells'])).reshape((self.cfg['n_cells'], 4))
        self._nbyte = 2 + 4 * self.cfg['n_cells']

    def read_status(self,):
        self.vars_read += ['status']
        self.ensemble.status[:, :, self.ensemble.k] = np.array(
            self.f.read_ui8(4 * self.cfg['n_cells'])).reshape((self.cfg['n_cells'], 4))
        self._nbyte = 2 + 4 * self.cfg['n_cells']

    def read_bottom(self,):
        self.vars_read += ['bt_range', 'bt_vel', 'bt_corr', 'bt_ampl', 'bt_perc_gd']
        fd = self.f
        ens = self.ensemble
        k = ens.k
        cfg = self.cfg
        if self._source == 2:
            self.vars_read += ['slatitude', 'slongitude']
            fd.seek(2, 1)
            long1 = fd.read_ui16(1)
            fd.seek(6, 1)
            ens.slatitude[k] = fd.read_i32(1) * self._cfac
            if ens.slatitude[k] == 0:
                ens.slatitude[k] = np.NaN
        else:
            fd.seek(14, 1)
        ens.bt_range[:, k] = fd.read_ui16(4) * .01
        ens.bt_vel[:, k] = fd.read_i16(4)
        ens.bt_corr[:, k] = fd.read_ui8(4)
        ens.bt_ampl[:, k] = fd.read_ui8(4)
        ens.bt_perc_gd[:, k] = fd.read_ui8(4)
        if self._source == 2:
            fd.seek(2, 1)
            ens.slongitude[k] = (long1 + 65536 * fd.read_ui16(1)) * self._cfac
            if ens.slongitude[k] > 180:
                ens.slongitude[k] = ens.slongitude[k] - 360
            if ens.slongitude[k] == 0:
                ens.slongitude[k] = np.NaN
            fd.seek(16, 1)
            qual = fd.read_ui8(1)
            if qual == 0:
                print('qual==%d,%f %f' % (qual, ens.slatitude[k], ens.slongitude[k]))
                ens.slatitude[k] = np.NaN
                ens.slongitude[k] = np.NaN
            fd.seek(71 - 45 - 16 - 17, 1)
            self._nbyte = 2 + 68
        else:
            fd.seek(71 - 45, 1)
            self._nbyte = 2 + 68
        if cfg['prog_ver'] >= 5.3:
            fd.seek(78 - 71, 1)
            ens.bt_range[:, k] = ens.bt_range[:, k] + fd.read_ui8(4) * 655.36
            self._nbyte += 11
            if cfg['name'] == 'wh-adcp':
                if cfg['prog_ver'] >= 16.20:
                    # RDI documentation claims these extra bytes were added in
                    # v8.17, but they don't appear in my 8.33 data -
                    # conversation with Egil suggests they were added in 16.20
                    fd.seek(4, 1)
                    self._nbyte += 4

    def read_vmdas(self,):
        """ Read something from VMDAS """
        fd = self.f
        # The raw files produced by VMDAS contain a binary navigation data
        # block.
        self.cfg['sourceprog'] = 'VMDAS'
        ens = self.ensemble
        k = ens.k
        if self._source != 1:
            print('\n***** Apparently a VMDAS file \n\n')
        self._source = 1
        self.vars_read += ['etime',
                           'slatitude',
                           'slongitude',
                           'stime',
                           'elatitude',
                           'elongitude',
                           'flags',
                           'ntime', ]
        utim = fd.read_ui8(4)
        date = datetime.datetime(utim[2] + utim[3] * 256, utim[1], utim[0])
        # This byte is in hundredths of seconds (10s of milliseconds):
        time = datetime.timedelta(milliseconds=(int(fd.read_ui32(1)[0] * 10)))
        ens.stime[k] = date2num(date + time) + time_offset
        fd.seek(4, 1)  # "PC clock offset from UTC"
        ens.slatitude[k] = fd.read_i32(1) * self._cfac
        ens.slatitude[k] = fd.read_ui32(1) * self._cfac
        ens.etime[k] = date2num(date + datetime.timedelta(
            milliseconds=int(fd.read_ui32(1)[0] * 10))) + time_offset
        ens.elatitude[k] = fd.read_i32(1) * self._cfac
        ens.elongitude[k] = fd.read_i32(1) * self._cfac
        fd.seek(12, 1)
        ens.flags[k] = fd.read_ui16(1)
        fd.seek(6, 1)
        utim = fd.read_ui8(4)
        date = datetime.datetime(utim[0] + utim[1] * 256, utim[3], utim[2])
        ens.ntime[k] = date2num(date + datetime.timedelta(
            milliseconds=int(fd.read_ui32(1)[0] * 10))) + time_offset
        fd.seek(16, 1)
        self._nbyte = 2 + 76

    def read_winriver(self, nbt):
        self._winrivprob = True
        self.cfg['sourceprog'] = 'WINRIVER'
        if self._source != 2:
            print('\n***** Apparently a WINRIVER file - '
                  'Raw NMEA data handler not yet implemented\n\n')
        self._source = 2
        self._nbyte = 2 + nbt
        # Below is Pawlowicz' $xxGGA code...
        if nbt == 97:
            strng = self.f.read_array('uchar', nbt)
            l = strng.find('$GPGGA')
            k = self.ensemble.k
            if l != -1:
                self.vars_read += ['stime']
                self.ensemble.stime[k] = (int(strng[l + 7:l + 8])
                                          + (int(strng[l + 9:l + 10])
                                             + int(str[l + 11:l + 12]) / 60) / 60) / 24
                # MATLAB CODE:
                # (sscanf(str(l + 7:l + 8), '%d')
                #  + (sscanf(str(l + 9:l + 10),'%d')
                #     + sscanf(str(l + 11:l + 12), '%d') / 60) / 60) / 24;

    def skip_Ncol(self, n_skip=1):
        self.f.seek(n_skip * self.cfg['n_cells'])
        self._nbyte = 2 + n_skip * self.cfg['n_cells']

    def skip_Nbyte(self, n_skip):
        self.f.seek(n_skip, 1)
        self._nbyte = self._nbyte = 2 + n_skip

    def read_hdr(self,):
        fd = self.f
        cfgid = list(fd.read_ui8(2))
        nread = 0
        while (cfgid[0] != 127 | cfgid[1] != 127) | (not self.checkheader()):
            nextbyte = fd.read_ui8(1)
            pos = fd.tell()
            nread += 1
            ### SKIPPED some EOF stuff here ###
            cfgid[1] = cfgid[0]
            cfgid[0] = nextbyte
            if np.mod(pos, 1000) == 0:
                print('Still looking for valid cfgid at file position %d ...' % pos)
        self._pos = self.f.tell() - 2
        if nread > 0:
            print('Junk found at BOF... skipping %d bytes until\ncfgid= (%x,%x) at file pos %d'
                  % (self._pos, cfgid[0], cfgid[1], nread))
        if self.__debug:
            print(fd.tell())
        self.read_hdrseg()

    def read_cfg(self,):
        cfgid = self.f.read_ui16(1)
        ### SKIPPED SOME DEBUGGING STUFF HERE ###
        self.read_cfgseg()

    def read_cfgseg(self,):
        cfgstart = self.f.tell()
        cfg = self.cfg
        fd = self.f
        tmp = fd.read_ui8(5)
        prog_ver0 = tmp[0]
        cfg['prog_ver'] = tmp[0] + tmp[1] / 100.
        cfg['name'] = self._cfgnames.get(tmp[0], 'unrecognized firmware version')
        config = tmp[2:4]
        cfg['config'] = np.binary_repr(config[1], 8) + '-' + np.binary_repr(config[0], 8)
        cfg['beam_angle'] = [15, 20, 30][(config[1] & 3)]
        cfg['numbeams'] = [4, 5][(config[1] & 16) == 16]
        cfg['beam_freq_khz'] = [75, 150, 300, 600, 1200, 2400, 38][(config[0] & 7)]
        cfg['beam_pattern'] = ['concave', 'convex'][(config[0] & 8) == 8]
        cfg['orientation'] = ['down', 'up'][(config[0] & 128) == 128]
        cfg['simflag'] = ['real', 'simulated'][tmp[4]]
        fd.seek(1, 1)
        cfg['n_beam'] = fd.read_ui8(1)
        cfg['n_cells'] = fd.read_ui8(1)
        cfg['pings_per_ensemble'] = fd.read_ui16(1)
        cfg['cell_size_m'] = fd.read_ui16(1) * .01
        cfg['blank_m'] = fd.read_ui16(1) * .01
        cfg['prof_mode'] = fd.read_ui8(1)
        cfg['corr_threshold'] = fd.read_ui8(1)
        cfg['prof_codereps'] = fd.read_ui8(1)
        cfg['min_pgood'] = fd.read_ui8(1)
        cfg['evel_threshold'] = fd.read_ui16(1)
        cfg['sec_between_ping_groups'] = np.sum(np.array(fd.read_ui8(3)) * np.array([60., 1., .01]))
        coord_sys = fd.read_ui8(1)
        cfg['coord'] = np.binary_repr(coord_sys, 8)
        cfg['coord_sys'] = ['beam', 'instrument', 'ship', 'earth'][((coord_sys >> 3) & 3)]
        cfg['use_pitchroll'] = ['no', 'yes'][(coord_sys & 4) == 4]
        cfg['use_3beam'] = ['no', 'yes'][(coord_sys & 2) == 2]
        cfg['bin_mapping'] = ['no', 'yes'][(coord_sys & 1) == 1]
        cfg['xducer_misalign_deg'] = fd.read_i16(1) * .01
        cfg['magnetic_var_deg'] = fd.read_i16(1) * .01
        cfg['sensors_src'] = np.binary_repr(fd.read_ui8(1), 8)
        cfg['sensors_avail'] = np.binary_repr(fd.read_ui8(1), 8)
        cfg['bin1_dist_m'] = fd.read_ui16(1) * .01
        cfg['xmit_pulse'] = fd.read_ui16(1) * .01
        cfg['water_ref_cells'] = fd.read_ui8(2)
        cfg['fls_target_threshold'] = fd.read_ui8(1)
        fd.seek(1, 1)
        cfg['xmit_lag_m'] = fd.read_ui16(1) * .01
        self._nbyte = 40

        if prog_ver0 in [8, 16]:
            if cfg['prog_ver'] >= 8.14:
                cfg['serialnum'] = fd.read_ui8(8)
                self._nbyte += 8
            if cfg['prog_ver'] >= 8.24:
                cfg['sysbandwidth'] = fd.read_ui8(2)
                self._nbyte += 2
            if cfg['prog_ver'] >= 16.05:
                cfg['syspower'] = fd.read_ui8(1)
                self._nbyte += 1
            if cfg['prog_ver'] >= 16.27:
                cfg['navigator_basefreqindex'] = fd.read_ui8(1)
                cfg['remus_serialnum'] = fd.reaadcpd('uint8', 4)
                cfg['h_adcp_beam_angle'] = fd.read_ui8(1)
                self._nbyte += 6
        elif prog_ver0 == 9:
            if cfg['prog_ver'] >= 9.10:
                cfg['serialnum'] = fd.read_ui8(8)
                cfg['sysbandwidth'] = fd.read_ui8(2)
                self._nbyte += 10
        elif prog_ver0 in [14, 23]:
            cfg['serialnum'] = fd.read_ui8(8)
            self._nbyte += 8
        self.configsize = self.f.tell() - cfgstart

    def read_hdrseg(self,):
        fd = self.f
        self.hdr.nbyte = fd.read_i16(1)
        if self.__debug:
            print(fd.tell())
        fd.seek(1, 1)
        ndat = fd.read_i8(1)
        self.hdr.dat_offsets = fd.read_i16(ndat)
        self._nbyte = 4 + ndat * 2

    def __exit__(self, type, value, traceback):
        self.f.close()

    def __enter__(self,):
        return self

    def __init__(self, fname, navg=1, nens=None, avg_func='mean'):
        self.fname = fname
        self.cfg = adcp_config()
        self.hdr = adcp_header()
        #self.f=io.npfile(fname,'r','l')
        self.f = bin_reader(fname)
        self.read_hdr()
        self.read_cfg()
        # Seek back to the beginning of the file:
        self.f.seek(self._pos, 0)
        self.n_avg = navg
        self.ensemble = ensemble(self.n_avg, self.cfg['n_cells'])
        self._filesize = getsize(fname)
        extrabytes = 0
        self._npings = int(self._filesize / (self.hdr.nbyte + 2 + extrabytes))
        print('%d pings estimated in this file' % self._npings)
        if nens is None:
            self._nens = int(self._npings / self.n_avg)
            self._ens_range = (0, self._nens)
        elif (nens.__class__ is tuple or nens.__class__ is list) and len(nens) == 2:
            nens = list(nens)
            if nens[1] == -1:
                nens[1] = self._npings
            self._nens = int((nens[1] - nens[0]) / self.n_avg)
            self._ens_range = nens
            self.f.seek((self.hdr.nbyte + 2 + extrabytes) * self._ens_range[0], 1)
        else:
            self._nens = nens
            self._ens_range = (0, nens)
        print('taking data from pings %d - %d' % tuple(self._ens_range))
        print('%d ensembles will be produced.' % self._nens)
        self.init_data()
        self.outd.add_data('ranges',
                           self.cfg['bin1_dist_m'] +
                           np.arange(self.cfg['n_cells']) * self.cfg['cell_size_m'],
                           '_essential')
        self.outd.add_data('config', self.cfg, '_essential')
        if self.cfg['orientation'] == 1:
            self.outd.ranges *= -1
        self.avg_func = getattr(self, avg_func)

    def init_data(self,):
        outd = adcp_raw()
        for nm in data_defs:
            outd.add_data(nm,
                          np.empty(get_size(nm, self._nens, self.cfg['n_cells']),
                                   dtype=data_defs[nm][2]),
                          group=data_defs[nm][1])
        self.outd = outd

    def load_data(self,):
        for iens in range(self._nens):
            try:
                self.read_buffer()
            except eofException:
                self.remove_end(iens)
                self.clean_up()
                return self.outd
            #if iens==5000:
            #    return self.outd
            self.ensemble.clean_data()
            if self.ensemble.rtc[0, 0] < 100:
                self.ensemble.rtc[0, :] += century
            dats = date2num(datetime.datetime(self.ensemble.rtc[0, :],
                                              self.ensemble.rtc[1, :],
                                              self.ensemble.rtc[2, :],
                                              self.ensemble.rtc[3, :],
                                              self.ensemble.rtc[4, :],
                                              self.ensemble.rtc[5, :],
                                              1e4 * self.ensemble.rtc[6, :]))
            #print( self.ensemble.bt_range )
            for nm in self.vars_read:
                getattr(self.outd, nm)[..., iens] = self.avg_func(self.ensemble[nm])
            self.outd.mpltime[iens] = np.median(dats)
        self.clean_up()
        return self.outd

    def clean_up(self,):
        """
        Remove the attributes from the data that were never loaded.
        """
        for nm in set(data_defs.keys()) - self.vars_read:
            self.outd.pop_data(nm)
        self.outd.config = self.cfg

    def remove_end(self, iens):
        if iens < self.outd.shape[-1]:
            print('Encountered end of file.  Cleaning up data.')
            for nm in self.vars_read:
                setattr(self.outd, nm, self.outd[nm][..., :iens])

    def search_buffer(self):
        """
        Check to see if the next bytes indicate the beginning of a
        data block.  If not, search for the next data block, up to
        _search_num times.
        """
        id1 = list(self.f.read_ui8(2))
        search_cnt = 0
        fd = self.f
        while search_cnt < self._search_num and ((id1[0] != 127 or id1[1] != 127)
                                                 or not self.checkheader()):
            search_cnt += 1
            nextbyte = fd.read_ui8(1)
            id1[1] = id1[0]
            id1[0] = nextbyte
        if search_cnt == self._search_num:
            warnings.warn('Searched %d entries... Not a workhorse/broadband'
                          ' file or bad data encountered: -> %x' %
                          (search_cnt, id1), ADCPWarning, )  # MAKE THIS AN ERROR/EXCEPTION?
        elif search_cnt > 0:
            warnings.warn('Searched %d bytes to find next valid ensemble start' %
                          search_cnt, ADCPWarning)

    def read_buffer(self,):
        fd = self.f
        self.ensemble.k = -1  # so that k+=1 gives 0 on the first loop.
        self.print_progress()
        while self.ensemble.k < self.ensemble.n_avg - 1:
            self.search_buffer()
            startpos = fd.tell() - 2
            self.read_hdrseg()
            byte_offset = self._nbyte + 2
            for n in range(len(self.hdr.dat_offsets)):
                id = fd.read_ui16(1)
                self._winrivprob = False
                #print( "%0.4X" % id )
                #self.print_pos()
                ##### Read the data for header "id"g
                self.read_dat(id)
                byte_offset += self._nbyte
                if n < (len(self.hdr.dat_offsets) - 1):
                    oset = self.hdr.dat_offsets[n + 1] - byte_offset
                    if oset != 0:
                        if self._verbose:
                            print('%s: Adjust location by %d\n' % (id, oset))
                        fd.seek(oset, 1)
                    byte_offset = self.hdr.dat_offsets[n + 1]
                else:
                    if self.hdr.nbyte - 2 != byte_offset:
                        if not self._winrivprob:
                            if self._verbose:
                                print('{:s}: Adjust location by {:d}\n'
                                      .format(id, self.hdr.nbyte - 2 - byte_offset))
                            self.f.seek(self.hdr.nbyte - 2 - byte_offset, 1)
                    byte_offset = self.hdr.nbyte - 2
            readbytes = fd.tell() - startpos
            #### The 2 is for the checksum:
            offset = self.hdr.nbyte + 2 - byte_offset
            self.check_offset(offset, readbytes)
            #self.print_pos(byte_offset=byte_offset)

    def check_offset(self, offset, readbytes):
        fd = self.f
        if offset != 4 and self._fixoffset == 0:
            print('\n******************************************************\n')
            if fd.tell() == self._filesize:
                print(' EOF reached unexpectedly - discaring this last ensemble\n')
            else:
                print('Adjust location by {:d} (readbytes={:d},hdr.nbyte={:d}\n'
                      .format(offset, self.readbytes, self.hdr.nbyte))
                print("""
                NOTE - If this appears at the beginning of the read, it is
                       a program problem, possibly fixed by a fudge
                       PLEASE REPORT TO levi.kilcher@nrel.gov WITH DETAILS
                       
                     - If this appears at the end of the file it means
                       The file is corrupted and only a partial record
                       has been read\n
                """)
            print('******************************************************\n')
            self._fixoffset = offset - 4
        fd.seek(4 + self._fixoffset, 1)

    def checkheader(self,):
        fd = self.f
        valid = 0
        numbytes = fd.read_i16(1)
        if numbytes > 0:
            fd.seek(numbytes - 2, 1)
            cfgid = fd.read_ui8(2)
            #### sloppy code:
            if len(cfgid) == 2:
                fd.seek(-numbytes - 2, 1)
                if cfgid[0] == 127 & cfgid[1] == 127:
                    valid = 1
        else:
            fd.seek(-2, 1)
        return valid


if __name__ == '__main__':

    import tools as tbx
    madcp = tbx.mload('/home/lkilcher/data/cr05/adcp1200/enxRaw/cr05024000ENX.mat')['adcp']
    mcfg = madcp.cfg

    #with adcp_loader("/home/lkilcher/data/cr05/adcp1200/bin/cr05024_000_000000.ENX") as ldr:
    #    adcpd=ldr.load_data()

    ldr = adcp_loader("/home/lkilcher/data/pnnl/adcp/raw/From_Instrument/_RDI_000.001")
    # with
    # adcp_loader("/home/lkilcher/data/pnnl/adcp/raw/From_Instrument/_RDI_000.001")
    # as ldr:
    adcpd = ldr.load_data()

"""
This module provides the routines for reading data from Nortek data
files.
"""

import numpy as np
from ..adv import base as adv_base
from ..adp import base as adp_base
from ..tools import misc as tbx
from struct import unpack
from ..data.base import ma
from . import nortek_defs
from ..data import time
from .base import WrongFileType, read_userdata
import warnings
from ..rotate.vector import calc_omat as _calc_omat
from ..data.base import TimeData
from ..data.base import config


def recatenate(obj):
    out = obj[0].__class__(_type=obj[0]['_type'])
    for ky in list(obj[0].keys()):
        if ky in ['__data_groups__', '_type']:
            continue
        val0 = obj[0][ky]
        if isinstance(val0, np.ndarray) and val0.size > 1:
            out[ky] = np.concatenate([val[ky][..., None] for val in obj],
                                     axis=-1)
        else:
            out[ky] = np.array([val[ky] for val in obj])
    return out


def int2binarray(val, n):
    out = np.zeros(n, dtype='bool')
    for idx, n in enumerate(range(n)):
        out[idx] = val & (2 ** n)
    return out


def read_nortek(filename,
                userdata=True,
                do_checksum=False,
                nens=None,
                keep_orient_raw=False):
    """
    Read a nortek file.

    Parameters
    ----------
    filename : string
               Filename of Nortek file to read.

    userdata : True, False, or string of userdata.json filename
               (default ``True``) Whether to read the
               '<base-filename>.userdata.json' file.

    do_checksum : bool (default False)
        Whether to perform the checksum of each data block.

    nens : None (default: read entire file), int, or
           2-element tuple (start, stop)
              Number of pings to read from the file

    keep_orient_raw : bool (default: False)
        If this is set to True, the raw orientation heading/pitch/roll
        data is retained in the returned data structure in the
        ``dat['orient']['raw']`` data group. This data is exactly as
        it was found in the binary data file, and obeys the instrument
        manufacturers definitions not DOLfYN's.

    Returns
    -------
    dat : :class:`<~dolfyn.data.velocity.Velocity>`
      A DOLfYN Velocity data object.

    """
    user_data = read_userdata(filename, userdata)

    with NortekReader(filename, do_checksum=do_checksum, nens=nens) as rdr:
        rdr.readfile()
    rdr.dat2sci()
    dat = rdr.data

    od = dat['orient']
    if 'orient.orientmat' not in dat:
        od['orientmat'] = _calc_omat(od['heading'], od['pitch'], od['roll'],
                                     od.get('orientation_down', None))

    if keep_orient_raw:
        odr = od['raw'] = TimeData()
    for ky in ['heading', 'pitch', 'roll', 'orientation_down']:
        val = od.pop(ky, None)
        if keep_orient_raw and val is not None:
            odr[ky] = val

    dat.props.update(user_data)

    declin = dat['props'].pop('declination', None)
    if declin is not None:
        dat.set_declination(declin)

    return dat


def _bcd2char(cBCD):
    """
    Taken from the Nortek System Integrator
    Manual "Example Program" Chapter.
    """
    cBCD = min(cBCD, 153)
    c = (cBCD & 15)
    c += 10 * (cBCD >> 4)
    return c


def _bitshift8(val):
    return val >> 8


class NortekReader(object):

    """
    A class for reading reading nortek binary files.

    This reader currently only supports AWAC and Vector data formats.

    Parameters
    ----------
    fname : string
            Nortek file filename to read.
    endian : {'<','>'} (optional)
             Specifies if the file is in 'little' or 'big' endian
             format. By default the reader will attempt to determine
             this.
    debug : {True, False*} (optional)
            Print debug/progress information?
    do_checksum : {True*, False} (optional)
                  Specifies whether to perform the checksum.
    bufsize : int (default 100000)
              The size of the read buffer to use.
    nens : None (default: None, read all files), int,
           or 2-element tuple (start, stop).
             The number of pings to read from the file. By default,
    the entire file is read.


    """
    _lastread = [None, None, None, None, None]

    fun_map = {'0x00': 'read_user_cfg',
               '0x04': 'read_head_cfg',
               '0x05': 'read_hw_cfg',
               '0x07': 'read_vec_checkdata',
               '0x10': 'read_vec_data',
               '0x11': 'read_vec_sysdata',
               '0x12': 'read_vec_hdr',
               '0x71': 'read_microstrain',
               '0x20': 'read_awac_profile',
               }

    def __init__(self, fname, endian=None, debug=False,
                 do_checksum=True, bufsize=100000, nens=None):
        self.fname = fname
        self._bufsize = bufsize
        self.f = open(fname, 'rb', 1000)
        self.do_checksum = do_checksum
        self.filesize  # initialize the filesize.
        self.debug = debug
        self.c = 0
        self._dtypes = []
        self._n_start = 0
        try:
            len(nens)
        except TypeError:
            # not a tuple, so we assume None or int
            self._npings = nens
        else:
            # TODO: add a check that nens is len(2)
            # passes: nens is tuple
            warnings.warn("a 'start ensemble' is not yet supported "
                          "for the Nortek reader. This function will read "
                          "the entire file, then crop the beginning at "
                          "nens[0].")
            self._npings = nens[1]
            self._n_start = nens[0]
        if endian is None:
            if unpack('<HH', self.read(4)) == (1445, 24):
                endian = '<'
            elif unpack('>HH', self.read(4)) == (1445, 24):
                endian = '>'
            else:
                raise WrongFileType("I/O error: could not determine the \
                'endianness' of the file.  Are you sure this is a Nortek \
                file?")
        self.endian = endian
        self.f.seek(0, 0)
        # print( unpack(self.endian+'HH',self.read(4)) )
        # This is the configuration data:
        self.config = config(_type='NORTEK Header Data')
        # Now read the header:
        err_msg = ("I/O error: The file does not "
                   "appear to be a Nortek data file.")
        if self.read_id() == 5:
            self.read_hw_cfg()
        else:
            raise Exception()
        if self.read_id() == 4:
            self.read_head_cfg()
        else:
            raise Exception(err_msg)
        if self.read_id() == 0:
            self.read_user_cfg()
        else:
            raise Exception(err_msg)
        if self.config.hardware.serialNum[0:3].upper() == 'WPR':
            self.config['config_type'] = 'AWAC'
        elif self.config.hardware.serialNum[0:3].upper() == 'VEC':
            self.config['config_type'] = 'ADV'
        # Initialize the instrument type:
        self._inst = self.config.pop('config_type')
        # This is the position after reading the 'hardware',
        # 'head', and 'user' configuration.
        pnow = self.pos
        # Run the appropriate initialization routine (e.g. init_ADV).
        getattr(self, 'init_' + self._inst)()
        self.f.close()  # This has a small buffer, so close it.
        self.f = open(fname, 'rb', bufsize)  # This has a large buffer...
        self.close = self.f.close
        if self._npings is not None:
            self.n_samp_guess = self._npings + 1
        self.f.seek(pnow, 0)  # Seek to the previous position.
        props = self.data.props
        if self.config.user.NBurst > 0:
            props['DutyCycle_NBurst'] = self.config.user.NBurst
            props['DutyCycle_NCycle'] = (self.config.user.MeasInterval *
                                         self.config.fs)
        self.burst_start = np.zeros(self.n_samp_guess, dtype='bool')
        props['fs'] = self.config.fs
        props['coord_sys'] = {'XYZ': 'inst',
                              'ENU': 'earth',
                              'BEAM': 'beam'}[self.config.user.CoordSystem]
        # This just initializes it; this gets overwritten in read_microstrain
        props['has imu'] = False

    def read(self, nbyte):
        byts = self.f.read(nbyte)
        if not (len(byts) == nbyte):
            raise EOFError('Reached the end of the file')
        return byts

    def _sci_data(self, vardict):
        """Convert the data to scientific units accordint to vardict.

        Parameters
        ----------
        vardict : (dict of :class:`<VarAttrs>`)
          The variable definitions in the :class:`<VarAttrs>` specify
          how to scale each data variable.

        """
        for nm, vd in list(vardict.items()):
            if vd.group is None:
                dat = self.data
            else:
                dat = self.data[vd.group]
            retval = vd.sci_func(dat[nm])
            # This checks whether a new data object was created:
            # sci_func returns None if it modifies the existing data.
            if retval is not None:
                dat[nm] = retval

    def _init_data(self, vardict):
        """Initialize the data object according to vardict.

        Parameters
        ----------
        vardict : (dict of :class:`<VarAttrs>`)
          The variable definitions in the :class:`<VarAttrs>` specify
          how to initialize each data variable.

        """
        shape_args = {'n': self.n_samp_guess}
        try:
            shape_args['nbins'] = self.config['user']['NBins']
        except KeyError:
            pass
        for nm, va in list(vardict.items()):
            if va.group is None:
                # These have to stay separated.
                if nm not in self.data:
                    self.data[nm] = va._empty_array(**shape_args)
            else:
                if nm not in self.data[va.group]:
                    self.data[va.group][nm] = va._empty_array(**shape_args)

    def checksum(self, byts):
        """
        Perform a checksum on `byts` and read the checksum value.
        """
        if self.do_checksum:
            if not np.sum(unpack(self.endian + (1 + len(byts) / 2) * 'H',
                                 self._thisid_bytes + byts)) + \
                    46476 - unpack(self.endian + 'H', self.read(2)):

                # !!!FIXTHIS error message.
                raise adv_base.db.CheckSumError('CheckSum Failed at ...')

        else:
            self.f.seek(2, 1)

    def read_id(self,):
        """
        Read the next 'ID' from the file.
        """
        self._thisid_bytes = bts = self.read(2)
        tmp = unpack(self.endian + 'BB', bts)
        if self.debug == 2:
            print('Positon: {}, codes: {}'.format(self.f.tell(), tmp))
        if tmp[0] != 165:  # This catches a corrupted data block.
            if self.debug:
                print("Corrupted data block sync code (%d, %d) found "
                      "in ping %d. Searching for next valid code..." %
                      (tmp[0], tmp[1], self.c))
            val = int(self.findnext(do_cs=False), 0)
            self.f.seek(2, 1)
            if self.debug:
                print(' ...FOUND {} at position: {}.'.format(val, self.pos))
            return val
        # if self.debug:
        #    print( tmp[1] )
        return tmp[1]

    def read_user_cfg(self,):
        # ID: '0x00 = 00
        if self.debug:
            print('Reading user configuration (0x00) ping #{} @ {}...'
                  .format(self.c, self.pos))
        cfg_u = self.config['user'] = config(_type='USER')
        byts = self.read(508)
        tmp = unpack(self.endian +
                     '2x5H13H6s4HI8H2x90H180s6H4xH2x2H2xH30x8H',
                     byts)
        # the first two are the size.
        cfg_u['Transmit'] = {
            'pulse length': tmp[0],
            'blank distance': tmp[1],
            'receive length': tmp[2],
            'time_between_pings': tmp[3],
            'time_between_bursts': tmp[4],
        }
        cfg_u['Npings'] = tmp[5]
        cfg_u['AvgInterval'] = tmp[6]
        cfg_u['NBeams'] = tmp[7]
        cfg_u['TimCtrlReg'] = int2binarray(tmp[8], 16)
        # From the nortek system integrator manual
        # (note: bit numbering is zero-based)
        treg = cfg_u.TimCtrlReg
        cfg_u['Profile Timing'] = ['single', 'continuous'][treg[1]]
        cfg_u['Burst Mode'] = ~treg[2]
        # How is this different from the power level in PwrCtrlReg?
        #cfg_u['Power Level']= treg[5] + 2 * treg[6] + 1
        cfg_u['sync-out'] = ['middle', 'end', ][treg[7]]
        cfg_u['Sample on Sync'] = treg[8]
        cfg_u['Start on Sync'] = treg[9]
        cfg_u['PwrCtrlReg'] = int2binarray(tmp[9], 16)
        cfg_u['A1'] = tmp[10]
        cfg_u['B0'] = tmp[11]
        cfg_u['B1'] = tmp[12]
        cfg_u['CompassUpdRate'] = tmp[13]
        cfg_u['CoordSystem'] = ['ENU', 'XYZ', 'BEAM'][tmp[14]]
        cfg_u['NBins'] = tmp[15]
        cfg_u['BinLength'] = tmp[16]
        cfg_u['MeasInterval'] = tmp[17]
        cfg_u['DeployName'] = tmp[18].partition(b'\x00')[0].decode('utf-8')
        cfg_u['WrapMode'] = tmp[19]
        cfg_u['ClockDeploy'] = np.array(tmp[20:23])
        cfg_u['DiagInterval'] = tmp[23]
        cfg_u['Mode0'] = int2binarray(tmp[24], 16)
        cfg_u['AdjSoundSpeed'] = tmp[25]
        cfg_u['NSampDiag'] = tmp[26]
        cfg_u['NBeamsCellDiag'] = tmp[27]
        cfg_u['NPingsDiag'] = tmp[28]
        cfg_u['ModeTest'] = int2binarray(tmp[29], 16)
        cfg_u['AnaInAddr'] = tmp[30]
        cfg_u['SWVersion'] = tmp[31]
        cfg_u['VelAdjTable'] = np.array(tmp[32:122])
        cfg_u['Comments'] = tmp[122].partition(b'\x00')[0].decode('utf-8')
        cfg_u['Mode1'] = int2binarray(tmp[123], 16)
        cfg_u['DynPercPos'] = tmp[124]
        cfg_u['T1w'] = tmp[125]
        cfg_u['T2w'] = tmp[126]
        cfg_u['T3w'] = tmp[127]
        cfg_u['NSamp'] = tmp[128]
        cfg_u['NBurst'] = tmp[129]
        cfg_u['AnaOutScale'] = tmp[130]
        cfg_u['CorrThresh'] = tmp[131]
        cfg_u['TiLag2'] = tmp[132]
        cfg_u['QualConst'] = np.array(tmp[133:141])
        self.checksum(byts)
        cfg_u['mode'] = {}
        cfg_u['mode']['user_sound'] = cfg_u['Mode0'][0]
        cfg_u['mode']['diagnostics_mode'] = cfg_u['Mode0'][1]
        cfg_u['mode']['analog_output_mode'] = cfg_u['Mode0'][2]
        cfg_u['mode']['output_format'] = ['Vector', 'ADV'][cfg_u['Mode0'][3]]  # noqa
        cfg_u['mode']['vel_scale'] = [1, 0.1][cfg_u['Mode0'][4]]
        cfg_u['mode']['serial_output'] = cfg_u['Mode0'][5]
        cfg_u['mode']['reserved_EasyQ'] = cfg_u['Mode0'][6]
        cfg_u['mode']['stage'] = cfg_u['Mode0'][7]
        cfg_u['mode']['output_power'] = cfg_u['Mode0'][8]
        cfg_u['mode']['mode_test_use_DSP'] = cfg_u['ModeTest'][0]
        cfg_u['mode']['mode_test_filter_output'] = ['total', 'correction_only'][cfg_u['ModeTest'][1]]  # noqa
        cfg_u['mode']['rate'] = ['1hz', '2hz'][cfg_u['Mode1'][0]]
        cfg_u['mode']['cell_position'] = ['fixed', 'dynamic'][cfg_u['Mode1'][1]]  # noqa
        cfg_u['mode']['dynamic_pos_type'] = ['pct of mean press', 'pct of min re'][cfg_u['Mode1'][2]]  # noqa

    def read_head_cfg(self,):
        # ID: '0x04 = 04
        cfg = self.config
        if self.debug:
            print('Reading head configuration (0x04) ping #{} @ {}...'
                  .format(self.c, self.pos))
        cfg_hd = cfg['head'] = config(_type='HEAD')
        byts = self.read(220)
        tmp = unpack(self.endian + '2x3H12s176s22sH', byts)
        cfg_hd['config'] = tmp[0]
        cfg_hd['freq'] = tmp[1]
        cfg_hd['type'] = tmp[2]
        cfg_hd['serialNum'] = tmp[3].decode('utf-8')
        cfg_hd['system'] = tmp[4]
        cfg_hd['TransMatrix'] = np.array(
            unpack(self.endian + '9h', tmp[4][8:26])).reshape(3, 3) / 4096.
        cfg_hd['spare'] = tmp[5].decode('utf-8')
        cfg_hd['NBeams'] = tmp[6]
        self.checksum(byts)

    def read_hw_cfg(self,):
        # ID 0x05 = 05
        cfg = self.config
        if self.debug:
            print('Reading hardware configuration (0x05) ping #{} @ {}...'
                  .format(self.c, self.pos))
        cfg_hw = cfg['hardware'] = config(_type='HARDWARE')
        byts = self.read(44)
        tmp = unpack(self.endian + '2x14s6H12xI', byts)
        cfg_hw['serialNum'] = tmp[0][:8].decode('utf-8')
        cfg_hw['ProLogID'] = unpack('B', tmp[0][8:9])[0]
        cfg_hw['ProLogFWver'] = tmp[0][10:].decode('utf-8')
        cfg_hw['config'] = tmp[1]
        cfg_hw['freq'] = tmp[2]
        cfg_hw['PICversion'] = tmp[3]
        cfg_hw['HWrevision'] = tmp[4]
        cfg_hw['recSize'] = tmp[5] * 65536
        cfg_hw['status'] = tmp[6]
        cfg_hw['FWversion'] = tmp[7]
        self.checksum(byts)

    def read_vec_checkdata(self,):
        # ID: 0x07 = 07
        if self.debug:
            print('Reading vector check data (0x07) ping #{} @ {}...'
                  .format(self.c, self.pos))
        byts0 = self.read(6)
        checknow = config(_type='CHECKDATA')
        tmp = unpack(self.endian + '2x2H', byts0)  # The first two are size.
        checknow['Samples'] = tmp[0]
        n = checknow.Samples
        checknow['First_samp'] = tmp[1]
        # checknow['Amp1']= tbx.nans(n, dtype=np.uint8) + 8
        # checknow['Amp2']= tbx.nans(n, dtype=np.uint8) + 8
        # checknow['Amp3']= tbx.nans(n, dtype=np.uint8) + 8
        byts1 = self.read(3 * n)
        tmp = unpack(self.endian + (3 * n * 'B'), byts1)
        for idx, nm in enumerate(['Amp1', 'Amp2', 'Amp3']):
            checknow[nm] = np.array(tmp[idx * n:(idx + 1) * n], dtype=np.uint8)
        self.checksum(byts0 + byts1)
        if 'checkdata' not in self.config:
            self.config['checkdata'] = checknow
        else:
            if not isinstance(self.config.checkdata, list):
                self.config.checkdata = [self.config.checkdata, ]
            self.config.checkdata = self.config.checkdata + [checknow]

    def sci_vec_data(self,):
        self._sci_data(nortek_defs.vec_data)
        dat = self.data

        dat.env['pressure'] = (
            dat.env.PressureMSB.astype('float32') * 65536 +
            dat.env.PressureLSW.astype('float32')) / 1000.

        dat.env.pressure = ma.marray(
            dat.env.pressure,
            ma.varMeta('P', ma.unitsDict({'dbar': 1}), ['time'])
        )

        dat.env.pop('PressureMSB')
        dat.env.pop('PressureLSW')

        # # I must be able to calculate this here, right?
        # # Answer: NO. Nortek can't tell me how to do that. :(
        # dat.props['doppler_noise'] = [0, 0, 0]
        # Apply velocity scaling (1 or 0.1)
        dat['vel'] *= self.config['user']['mode']['vel_scale']

    def read_vec_data(self,):
        """
        Read vector data.
        """
        # ID: 0x10 = 16
        # if 'vec_sysdata' not in self._lastread:
        #     print('Warning: First "vector data" block '
        #           'is before first "vector system data" block.')
        c = self.c
        dat = self.data
        if self.debug:
            print('Reading vector data (0x10) ping #{} @ {}...'
                  .format(self.c, self.pos))

        if 'vel' not in dat:
            self._init_data(nortek_defs.vec_data)
            self._dtypes += ['vec_data']

        byts = self.read(20)
        sig = dat['signal']
        (dat._extra['AnaIn2LSB'][c],
         dat._extra['Count'][c],
         dat.env['PressureMSB'][c],
         dat._extra['AnaIn2MSB'][c],
         dat.env['PressureLSW'][c],
         dat._extra['AnaIn1'][c],
         dat['vel'][0, c],
         dat['vel'][1, c],
         dat['vel'][2, c],
         sig['amp'][0, c],
         sig['amp'][1, c],
         sig['amp'][2, c],
         sig['corr'][0, c],
         sig['corr'][1, c],
         sig['corr'][2, c]) = unpack(self.endian + '4B2H3h6B', byts)

        self.checksum(byts)
        self.c += 1

    def sci_vec_sysdata(self,):
        """
        Turn the data in the vec_sysdata structure into scientific units.
        """
        dat = self.data
        fs = dat.config.fs
        self._sci_data(nortek_defs.vec_sysdata)
        dat['_sysi'] = ~np.isnan(dat.mpltime)
        # These are the indices in the sysdata variables
        # that are not interpolated.
        #pdb.set_trace()
        nburst = self.config.user.NBurst
        dat.orient['orientation_down'] = tbx.nans(len(dat.mpltime),
                                                  dtype='bool')
        if nburst == 0:
            num_bursts = 1
            nburst = len(dat.mpltime)
        else:
            num_bursts = int(len(dat.mpltime) // nburst + 1)
        for nb in range(num_bursts):
            iburst = slice(nb * nburst, (nb + 1) * nburst)
            sysi = dat._sysi[iburst]
            if len(sysi) == 0:
                break
            # Skip the first entry for the interpolation process
            inds = np.nonzero(sysi)[0][1:]
            arng = np.arange(len(dat.mpltime[iburst]), dtype=np.float64)
            if len(inds) >= 2:
                p = np.poly1d(np.polyfit(inds, dat.mpltime[iburst][inds], 1))
                dat.mpltime[iburst] = p(arng)
            elif len(inds) == 1:
                dat.mpltime[iburst] = ((arng - inds[0]) / (fs * 3600 * 24) +
                                       dat.mpltime[iburst][inds[0]])
            else:
                dat.mpltime[iburst] = (dat.mpltime[iburst][0] +
                                       arng / (fs * 24 * 3600))

            tmpd = tbx.nans_like(dat.orient.heading[iburst])
            # The first status bit should be the orientation.
            tmpd[sysi] = dat.sys.status[iburst][sysi] & 1
            tbx.fillgaps(tmpd, extrapFlg=True)
            slope = np.diff(tmpd)
            tmpd[1:][slope < 0] = 1
            tmpd[:-1][slope > 0] = 0
            dat.orient.orientation_down[iburst] = tmpd.astype('bool')
        tbx.interpgaps(dat.sys.batt, dat.mpltime)
        tbx.interpgaps(dat.env.c_sound, dat.mpltime)
        tbx.interpgaps(dat.orient.heading, dat.mpltime)
        tbx.interpgaps(dat.orient.pitch, dat.mpltime)
        tbx.interpgaps(dat.orient.roll, dat.mpltime)
        tbx.interpgaps(dat.env.temp, dat.mpltime)
        dat.mpltime = dat.mpltime.view(time.time_array)

    def read_vec_sysdata(self,):
        """
        Read vector system data.
        """
        # ID: 0x11 = 17
        c = self.c
        # Need to make this a vector...
        if self.debug:
            print('Reading vector system data (0x11) ping #{} @ {}...'
                  .format(self.c, self.pos))
        dat = self.data
        if self._lastread[:2] == ['vec_checkdata', 'vec_hdr', ]:
            self.burst_start[c] = True
        if not hasattr(dat, 'mpltime'):
            self._init_data(nortek_defs.vec_sysdata)
            self._dtypes += ['vec_sysdata']
        byts = self.read(24)
        # The first two are size (skip them).
        dat.mpltime[c] = self.rd_time(byts[2:8])
        (dat.sys.batt[c],
         dat.env.c_sound[c],
         dat.orient.heading[c],
         dat.orient.pitch[c],
         dat.orient.roll[c],
         dat.env.temp[c],
         dat.sys.error[c],
         dat.sys.status[c],
         dat._extra.AnaIn[c]) = unpack(self.endian + '2H3hH2BH', byts[8:])
        self.checksum(byts)

    def sci_microstrain(self,):
        """
        Rotate orientation data into ADV coordinate system.
        """
        # MS = MicroStrain
        dat_o = self.data.orient
        for nm in self._orient_dnames:
            # Rotate the MS orientation data (in MS coordinate system)
            # to be consistent with the ADV coordinate system.
            # (x,y,-z)_ms = (z,y,x)_adv
            (dat_o[nm][2],
             dat_o[nm][0]) = (dat_o[nm][0],
                              -dat_o[nm][2].copy())
            # tmp=dat_o[nm][2].copy()
            # dat_o[nm][2]=dat_o[nm][0]
            # dat_o[nm][0]=tmp
            # dat_o[nm][2]*=-1
            # dat_o[nm]=np.roll(dat_o[nm],-1,axis=0) # I think this is
            # wrong.
        if 'orientmat' in self._orient_dnames:
            # MS coordinate system is in North-East-Down (NED),
            # we want East-North-Up (ENU)
            dat_o.orientmat[:, 2] *= -1
            (dat_o.orientmat[:, 0],
             dat_o.orientmat[:, 1]) = (dat_o.orientmat[:, 1],
                                       dat_o.orientmat[:, 0].copy())
        if 'accel' in dat_o:
            # This value comes from the MS 3DM-GX3 MIP manual.
            dat_o.accel *= 9.80665
            dat_o.accel = ma.marray(dat_o.accel, ma.varMeta(
                'accel', units={'m': 1, 's': -2}, dim_names=['xyz', 'time'],))
            dat_o.angrt = ma.marray(dat_o.angrt, ma.varMeta(
                'angRt', units={'s': -1}, dim_names=['xyz', 'time'],))
        if self._ahrsid in [195, 211]:
            # These are DAng and DVel, so we convert them to angrt, accel here
            dat_o.angrt *= self.config.fs
            dat_o.accel *= self.config.fs

    def read_microstrain(self,):
        """
        Read microstrain sensor data.
        """
        # 0x71 = 113
        if self.c == 0:
            print('Warning: First "microstrain data" block '
                  'is before first "vector system data" block.')
        else:
            self.c -= 1
        if self.debug:
            print('Reading vector microstrain data (0x71) ping #{} @ {}...'
                  .format(self.c, self.pos))
        byts0 = self.read(4)
        # The first 2 are the size, 3rd is count, 4th is the id.
        ahrsid = unpack(self.endian + '3xB', byts0)[0]
        if hasattr(self, '_ahrsid') and self._ahrsid != ahrsid:
            print('Warning: AHRSID Changes mid-file!')
            #raise Exception("AHRSID Changes mid-file!")
        if ahrsid in [195, 204, 210, 211]:
            self._ahrsid = ahrsid
        #print(byts0)
        c = self.c
        dat = self.data
        dat_o = dat['orient']
        dat.props['has imu'] = True
        if not (hasattr(dat_o, 'accel')):
            self._dtypes += ['microstrain']
            if ahrsid == 195:
                self._orient_dnames = ['accel', 'angrt', 'orientmat']
                dat_o['accel'] = tbx.nans((3, self.n_samp_guess),
                                          dtype=np.float32)
                dat_o['angrt'] = tbx.nans((3, self.n_samp_guess),
                                          dtype=np.float32)
                dat_o['orientmat'] = tbx.nans((3, 3, self.n_samp_guess),
                                              dtype=np.float32)
                dat.props['rotate_vars'].update({'orient.accel',
                                                 'orient.angrt', })
            if ahrsid in [204, 210]:
                self._orient_dnames = ['accel', 'angrt', 'mag', 'orientmat']
                dat_o['accel'] = tbx.nans((3, self.n_samp_guess),
                                          dtype=np.float32)
                dat_o['angrt'] = tbx.nans((3, self.n_samp_guess),
                                          dtype=np.float32)
                dat_o['mag'] = tbx.nans((3, self.n_samp_guess),
                                        dtype=np.float32)
                dat.props['rotate_vars'].update(
                    {'orient.accel', 'orient.angrt', 'orient.mag'})
                if ahrsid == 204:
                    dat_o['orientmat'] = tbx.nans((3, 3, self.n_samp_guess),
                                                  dtype=np.float32)
            elif ahrsid == 211:
                self._orient_dnames = ['angrt', 'accel', 'mag']
                dat_o['angrt'] = tbx.nans((3, self.n_samp_guess),
                                          dtype=np.float32)
                dat_o['accel'] = tbx.nans((3, self.n_samp_guess),
                                          dtype=np.float32)
                dat_o['mag'] = tbx.nans((3, self.n_samp_guess),
                                        dtype=np.float32)
                dat.props['rotate_vars'].update(
                    {'orient.angrt', 'orient.accel', 'orient.mag'})
        byts = ''
        if ahrsid == 195:  # 0xc3
            byts = self.read(64)
            dt = unpack(self.endian + '6f9f4x', byts)
            (dat_o.angrt[:, c],
             dat_o.accel[:, c]) = (dt[0:3], dt[3:6],)
            dat_o.orientmat[:, :, c] = ((dt[6:9], dt[9:12], dt[12:15]))
        elif ahrsid == 204:  # 0xcc
            byts = self.read(78)
            # This skips the "DWORD" (4 bytes) and the AHRS checksum
            # (2 bytes)
            dt = unpack(self.endian + '18f6x', byts)
            (dat_o.accel[:, c],
             dat_o.angrt[:, c],
             dat_o.mag[:, c]) = (dt[0:3], dt[3:6], dt[6:9],)
            dat_o.orientmat[:, :, c] = ((dt[9:12], dt[12:15], dt[15:18]))
        elif ahrsid == 211:
            byts = self.read(42)
            dt = unpack(self.endian + '9f6x', byts)
            (dat_o.angrt[:, c],
             dat_o.accel[:, c],
             dat_o.mag[:, c]) = (dt[0:3], dt[3:6], dt[6:9],)
        else:
            print('Unrecognized IMU identifier: ' + str(ahrsid))
            self.f.seek(-2, 1)
            return 10
        self.checksum(byts0 + byts)
        self.c += 1  # reset the increment

    def read_vec_hdr(self,):
        # ID: '0x12 = 18
        if self.debug:
            print('Reading vector header data (0x12) ping #{} @ {}...'
                  .format(self.c, self.pos))
        byts = self.read(38)
        # The first two are size, the next 6 are time.
        tmp = unpack(self.endian + '8xH7B21x', byts)
        hdrnow = config(_type='DATA HEADER')
        hdrnow['time'] = self.rd_time(byts[2:8])
        hdrnow['NRecords'] = tmp[0]
        hdrnow['Noise1'] = tmp[1]
        hdrnow['Noise2'] = tmp[2]
        hdrnow['Noise3'] = tmp[3]
        hdrnow['Spare0'] = byts[13:14].decode('utf-8')
        hdrnow['Corr1'] = tmp[5]
        hdrnow['Corr2'] = tmp[6]
        hdrnow['Corr3'] = tmp[7]
        hdrnow['Spare1'] = byts[17:].decode('utf-8')
        self.checksum(byts)
        if 'data_header' not in self.config:
            self.config['data_header'] = hdrnow
        else:
            if not isinstance(self.config.data_header, list):
                self.config.data_header = [self.config.data_header, ]
            self.config.data_header = self.config.data_header + [hdrnow]

    def read_awac_profile(self,):
        # ID: '0x20' = 32
        dat = self.data
        if self.debug:
            print('Reading AWAC velocity data (0x20) ping #{} @ {}...'
                  .format(self.c, self.pos))
        nbins = self.config.user.NBins
        if not hasattr(dat['env'], 'temp'):
            self._init_data(nortek_defs.awac_profile)
            self._dtypes += ['awac_profile']

        # There is a 'fill' byte at the end, if nbins is odd.
        byts = self.read(116 + 9 * nbins + np.mod(nbins, 2))
        c = self.c
        dat.mpltime[c] = self.rd_time(byts[2:8])
        (dat.sys.Error[c],
         dat._extra.AnaIn1[c],
         dat.sys.batt[c],
         dat.env.c_sound[c],
         dat.orient.heading[c],
         dat.orient.pitch[c],
         dat.orient.roll[c],
         p_msb,
         dat.sys.status[c],
         p_lsw,
         dat.env.temp[c],) = unpack(self.endian + '7HBB2H', byts[8:28])
        dat.env.pressure[c] = (65536 * p_msb + p_lsw)
        # The nortek system integrator manual specifies an 88byte 'spare'
        # field, therefore we start at 116.
        tmp = unpack(self.endian + str(3 * nbins) + 'h' +
                     str(3 * nbins) + 'B', byts[116:116 + 9 * nbins])
        for idx in range(3):
            dat['vel'][idx, :, c] = tmp[idx * nbins: (idx + 1) * nbins]
            dat['signal']['amp'][idx, :, c] = tmp[(idx + 3) * nbins:
                                                  (idx + 4) * nbins]
        self.checksum(byts)
        self.c += 1

    def sci_awac_profile(self,):
        self._sci_data(nortek_defs.awac_profile)
        # Calculate the ranges.
        # This information comes from the nortek knowledgebase:
        # http://www.nortekusa.com/en/knowledge-center/forum/hr-profilers/736804717
        cs_coefs = {2000: 0.0239,
                    1000: 0.0478,
                    600: 0.0797,
                    400: 0.1195}
        h_ang = 25 * np.pi / 180  # The head angle is 25 degrees for all awacs.
        cs = np.float(self.config.user.BinLength) / 256. * \
            cs_coefs[self.config.head.freq] * np.cos(h_ang)
        bd = self.config.user.Transmit['blank distance'] * \
            0.0229 * np.cos(h_ang) - cs

        # These are the centers of the cells:
        self.data['range'] = ma.marray(
            np.float32(np.arange(self.config.user.NBins) + cs / 2 + bd),
            ma.varMeta('range', {'m': 1}, ['depth']))
        self.config['cell_size'] = cs
        self.config['blank_dist'] = bd

    def code_spacing(self, searchcode, iternum=50):
        """
        Find the spacing, in bytes, between a specific hardware code.
        Repeat this * iternum * times(default 50).
        Returns the average spacing, in bytes, between the code.
        """
        p0 = self.findnextid(searchcode)
        for i in range(iternum):
            try:
                self.findnextid(searchcode)
            except EOFError:
                break
        if self.debug:
            print('p0={}, pos={}, i={}'.format(p0, self.pos, i))
        # Compute the average of the data size:
        return (self.pos - p0) / (i + 1)

    def init_ADV(self,):
        dat = self.data = adv_base.ADVdata()
        dat['orient'] = TimeData()
        dat['signal'] = TimeData()
        dat['sys'] = TimeData()
        dat['env'] = TimeData()
        dat['_extra'] = TimeData()
        dat['config'] = self.config
        dat.props = {}
        dat.props['inst_make'] = 'Nortek'
        dat.props['inst_model'] = 'VECTOR'
        dat.props['inst_type'] = 'ADV'
        dat.props['rotate_vars'] = {'vel', }
        # Question to Nortek: How do they determine how many samples are in a
        # file, in order to initialize arrays?
        dlta = self.code_spacing('0x11')
        self.config['fs'] = 512 / self.config.user.AvgInterval
        self.n_samp_guess = int(self.filesize / dlta + 1)
        self.n_samp_guess *= int(self.config['fs'])

    def init_AWAC(self,):
        dat = self.data = adp_base.ADPdata()
        dat['orient'] = TimeData()
        dat['signal'] = TimeData()
        dat['sys'] = TimeData()
        dat['env'] = TimeData()
        dat['_extra'] = TimeData()
        dat['config'] = self.config
        dat.props = {}
        dat.props['inst_make'] = 'Nortek'
        dat.props['inst_model'] = 'AWAC'
        dat.props['inst_type'] = 'ADP'
        dat.props['rotate_vars'] = {'vel', }
        self.n_samp_guess = int(self.filesize / self.code_spacing('0x20') + 1)
        self.config['fs'] = 1. / self.config.user.AvgInterval

    @property
    def filesize(self,):
        if not hasattr(self, '_filesz'):
            pos = self.pos
            self.f.seek(0, 2)
            # Seek to the end of the file to determine the
            # filesize.
            self._filesz = self.pos
            self.f.seek(pos, 0)  # Return to the initial position.
        return self._filesz

    @property
    def pos(self,):
        return self.f.tell()

    def rd_time(self, strng):
        """
        Read the time from the first 6bytes of the input string.
        """
        min, sec, day, hour, year, month = unpack('BBBBBB', strng[:6])
        try:
            return time.date2num(time.datetime(
                time._fullyear(_bcd2char(year)),
                _bcd2char(month),
                _bcd2char(day),
                _bcd2char(hour),
                _bcd2char(min),
                _bcd2char(sec)
            ))
        except ValueError:
            return np.NaN

    def findnext(self, do_cs=True):
        """
        Find the next data block by checking the checksum,
        and the sync byte(0xa5).
        """
        # I may want to use fd.cs for this,
        # but right now I'm not going to worry about it.
        # cstmp=self.fd.cs._cs # reset this at the end of the script
        # eb=self.fd.cs._error_behavior # reset this at the end of the script
        # self.fd.cs.init(46476,2,'silent')
        sum = np.uint16(int('0xb58c', 0))  # Initialize the sum
        cs = 0
        func = _bitshift8
        func2 = np.uint8
        if self.endian == '<':
            func = np.uint8
            func2 = _bitshift8
        while True:
            val = unpack(self.endian + 'H', self.read(2))[0]
            if func(val) == 165 and (not do_cs or cs == np.uint16(sum)):
                self.f.seek(-2, 1)
                return hex(func2(val))
            sum += cs
            cs = val

    def findnextid(self, id):
        if id.__class__ is str:
            id = int(id, 0)
        nowid = None
        while nowid != id:
            nowid = self.read_id()
            if nowid == 16:
                # Vector velocity data doesn't have a 'size' field. !?
                # sz = 24
                # We already read(2) for id, so we shift by sz-2
                shift = 22
            else:
                sz = 2 * unpack(self.endian + 'H', self.read(2))[0]
                # We already read(2) for id, and read(2) for size, so
                # we shift by sz-4
                shift = sz - 4
            #print 'nowid = {}, size = {}'.format(nowid, sz)
            self.f.seek(shift, 1)
        return self.pos

    def readnext(self,):
        id = '0x%02x' % self.read_id()
        if id in self.fun_map:
            func_name = self.fun_map[id]
            out = getattr(self, func_name)()
            self._lastread = [func_name[5:]] + self._lastread[:-1]
            return out
        else:
            print('Unrecognized identifier: ' + id)
            self.f.seek(-2, 1)
            return 10

    def readfile(self, nlines=None):
        print('Reading file %s ...' % self.fname)
        # self.progbar=db.progress_bar(self.filesz)
        # self.progbar.init()
        retval = None
        try:
            while not retval:
                if self.c == nlines:
                    break
                retval = self.readnext()
                if retval == 10:
                    self.findnext()
                    retval = None
                if self._npings is not None and self.c >= self._npings:
                    if 'microstrain' in self._dtypes:
                        try:
                            self.readnext()
                        except:
                            pass
                    break
        except EOFError:
            print(' end of file at {} bytes.'.format(self.pos))
        else:
            print(' stopped at {} bytes.'.format(self.pos))
        self.c -= 1
        crop_data(self.data, slice(0, self.c), self.n_samp_guess)

    def dat2sci(self,):
        for nm in self._dtypes:
            getattr(self, 'sci_' + nm)()
        for nm in ['data_header', 'checkdata']:
            if nm in self.config and isinstance(self.config[nm], list):
                self.config[nm] = recatenate(self.config[nm])

    def __exit__(self, type, value, trace,):
        self.close()

    def __enter__(self,):
        return self


def crop_data(obj, range, n_lastdim):
    for nm, dat in obj.items():
        if isinstance(dat, np.ndarray) and \
           (dat.shape[-1] == n_lastdim):
            obj[nm] = dat[..., range]
        if isinstance(dat, TimeData):
            crop_data(dat, range, n_lastdim)

"""This is the top-level module for reading Nortek Signature (.ad2cp)
files. It relies heavily on the `nortek2_defs` and `nortek2lib`
modules.
"""
from struct import unpack
from . import nortek2_defs as defs
from . import nortek2lib as lib
from ..adp import base as apb
import numpy as np
from .base import WrongFileType, read_userdata
from ..data import base as db
import warnings
from ..rotate.vector import _euler2orient
from ..data.base import TimeData


def split_to_hdf(infile, nens_per_file, outfile=None,
                 ens_start=0, ens_stop=None,
                 start_file_num=0):
    """Split a Nortek .ad2cp file into multiple hdf5 format files.

    Parameters
    ==========
    infile : string
        The input .ad2cp filename.
    nens_per_file : int
        number of ensembles to include in each output file.
    outfile : string
        The output file format. This should include a '{:d}' format
        specifier. By default, this is the input file path and prefix,
        but with the ending '{:03d}.h5'.
    ens_start : int
        The ensemble number to start with.
    ens_stop : int
        The ensemble number to stop at.
    start_file_num : int
        The number to start the file-count with (default: 0).
    """
    if not infile.lower().endswith('.ad2cp'):
        raise Exception("This function only works on "
                        "Nortek '.ad2cp' format files.")
    idx = lib.get_index(infile)
    if ens_stop is None:
        ens_stop = idx['ens'][-1]
    ens_now = ens_start
    file_count = start_file_num
    if outfile is None:
        outfile = infile.rsplit('.')[0] + '.{:03d}.h5'
    elif '{' not in outfile and 'd}' not in outfile:
        raise Exception("The output file must include a "
                        "integer format specifier.")
    while ens_now < ens_stop:
        dat = read_signature(infile, nens=(ens_now,
                                           min(ens_now + nens_per_file,
                                               ens_stop)))
        dat.to_hdf5(outfile.format(file_count))
        file_count += 1
        ens_now += nens_per_file


def read_signature(filename, userdata=True, nens=None, keep_orient_raw=False):
    """Read a Nortek Signature (.ad2cp) file.

    Parameters
    ==========
    filename : string
        The filename of the file to load.

    userdata : filename
        <<currently unused, just a placeholder.>>

    nens : int, or tuple of 2 ints
        The number of ensembles to read, if int (starting at the
        beginning); or the range of ensembles to read, if tuple.

    keep_orient_raw : bool (default: False)
        If this is set to True, the raw orientation heading/pitch/roll
        data is retained in the returned data structure in the
        ``dat['orient']['raw']`` data group. This data is exactly as
        it was found in the binary data file, and obeys the instrument
        manufacturers definitions not DOLfYN's.

    Returns
    =======
    dat : :class:`dolfyn.ADPdata` object
        An ADCP data object containing the loaded data.
    """
    if nens is None:
        nens = [0, None]
    else:
        try:
            n = len(nens)
        except TypeError:
            nens = [0, nens]
        else:
            # passes: it's a list/tuple/array
            if n != 2:
                raise TypeError('nens must be: None (), int, or len 2')

    userdata = read_userdata(filename, userdata)

    rdr = Ad2cpReader(filename)
    d = rdr.readfile(nens[0], nens[1])
    rdr.sci_data(d)
    out = reorg(d)
    reduce(out)

    od = out['orient']
    if 'orient.orientmat' not in out:
        od['orientmat'] = _euler2orient(od['heading'], od['pitch'], od['roll'])

    if 'heading' in od:
        h, p, r = od.pop('heading'), od.pop('pitch'), od.pop('roll')
        if keep_orient_raw:
            odr = od['raw'] = TimeData()
            odr['heading'], odr['pitch'], odr['roll'] = h, p, r        

    out['props'].update(userdata)

    declin = out['props'].pop('declination', None)
    if declin is not None:
        out.set_declination(declin)

    return out


class Ad2cpReader(object):
    """This is the reader-object for reading AD2CP files.

    This should only be used explicitly for debugging
    purposes. Instead, a user should generally rely on the
    `read_signature` function.
    """
    debug = False

    def __init__(self, fname, endian=None, bufsize=None, rebuild_index=False):

        self.fname = fname
        self._check_nortek(endian)
        self._index = lib.get_index(fname,
                                    reload=rebuild_index)
        self.reopen(bufsize)
        self.filehead_config = self.read_filehead_config_string()
        self._ens_pos = lib.index2ens_pos(self._index)
        self._config = lib.calc_config(self._index)
        self._init_burst_readers()
        self.unknown_ID_count = {}

    def _init_burst_readers(self, ):
        self._burst_readers = {}
        for rdr_id, cfg in self._config.items():
            self._burst_readers[rdr_id] = defs.calc_burst_struct(
                cfg['_config'], cfg['nbeams'], cfg['ncells'])

    def init_data(self, ens_start, ens_stop):
        outdat = {}
        nens = int(ens_stop - ens_start)
        n26 = ((self._index['ID'] == 26) &
               (self._index['ens'] >= ens_start) &
               (self._index['ens'] < ens_stop)).sum()
        for ky in self._burst_readers:
            if ky == 26:
                n = n26
                ens = np.zeros(n, dtype='uint32')
            else:
                ens = np.arange(ens_start,
                                ens_stop).astype('uint32')
                n = nens
            outdat[ky] = self._burst_readers[ky].init_data(n)
            outdat[ky]['ensemble'] = ens
        return outdat

    def read_hdr(self, do_cs=False):
        res = defs._header.read2dict(self.f, cs=do_cs)
        if res['sync'] != 165:
            raise Exception("Out of sync!")
        return res

    def _check_nortek(self, endian):
        self.reopen(10)
        byts = self.f.read(2)
        if endian is None:
            if unpack('<' + 'BB', byts) == (165, 10):
                endian = '<'
            elif unpack('>' + 'BB', byts) == (165, 10):
                endian = '>'
            else:
                raise WrongFileType(
                    "I/O error: could not determine the 'endianness' "
                    "of the file.  Are you sure this is a Nortek "
                    "AD2CP file?")
        self.endian = endian

    def reopen(self, bufsize=None):
        if bufsize is None:
            bufsize = 1000000
        try:
            self.f.close()
        except AttributeError:
            pass
        self.f = open(self.fname, 'rb', bufsize)

    def read_filehead_config_string(self, ):
        hdr = self.read_hdr()
        # This is the instrument config string.
        out = {}
        s_id, string = self.read_string(hdr['sz'])
        string = string.decode('utf-8')
        for ln in string.splitlines():
            ky, val = ln.split(',', 1)
            if ky in out:
                # There are more than one of this key
                if not isinstance(out[ky], list):
                    tmp = out[ky]
                    out[ky] = []
                    out[ky].append(tmp)
                out[ky].append(val)
            else:
                out[ky] = val
        out2 = {}
        for ky in out:
            if ky.startswith('GET'):
                dat = out[ky]
                d = out2[ky.lstrip('GET')] = dict()
                for itm in dat.split(','):
                    k, val = itm.split('=')
                    try:
                        val = int(val)
                    except ValueError:
                        try:
                            val = float(val)
                        except ValueError:
                            pass
                    d[k] = val
            else:
                out2[ky] = out[ky]
        return out2

    def readfile(self, ens_start=0, ens_stop=None):
        nens_total = len(self._ens_pos)
        if ens_stop is None or ens_stop > nens_total:
            ens_stop = nens_total - 1
        ens_start = int(ens_start)
        ens_stop = int(ens_stop)
        nens = ens_stop - ens_start
        outdat = self.init_data(ens_start, ens_stop)
        outdat['filehead config'] = self.filehead_config
        print('Reading file %s ...' % self.fname)
        retval = None
        c = 0
        c26 = 0
        self.f.seek(self._ens_pos[ens_start], 0)
        while not retval:
            try:
                hdr = self.read_hdr()
            except IOError:
                return outdat
            id = hdr['id']
            if id in [21, 24]:
                self.read_burst(id, outdat[id], c)
            elif id in [26]:
                # warnings.warn(
                #     "Unhandled ID: 0x1A (26)\n"
                #     "    There still seems to be a discrepancy between\n"
                #     "    the '0x1A' data format, and the specification\n"
                #     "    in the System Integrator Manual.")
                # Question posted at:
                # http://www.nortek-as.com/en/knowledge-center/forum/system-integration-and-telemetry/538802891
                rdr = self._burst_readers[26]
                if not hasattr(rdr, '_nsamp_index'):
                    first_pass = True
                    tmp_idx = rdr._nsamp_index = rdr._names.index('altraw_nsamp')  # noqa
                    shift = rdr._nsamp_shift = defs.calcsize(
                        defs._format(rdr._format[:tmp_idx],
                                     rdr._N[:tmp_idx]))
                else:
                    first_pass = False
                    tmp_idx = rdr._nsamp_index
                    shift = rdr._nsamp_shift
                tmp_idx = tmp_idx + 2  # Don't add in-place
                self.f.seek(shift, 1)
                # Now read the num_samples
                sz = unpack('<I', self.f.read(4))[0]
                self.f.seek(-shift - 4, 1)
                if first_pass:
                    # Fix the reader
                    rdr._shape[tmp_idx].append(sz)
                    rdr._N[tmp_idx] = sz
                    rdr._struct = defs.Struct('<' + rdr.format)
                    rdr.nbyte = defs.calcsize(rdr.format)
                    rdr._cs_struct = defs.Struct('<' + '{}H'.format(int(rdr.nbyte // 2)))
                    # Initialize the array
                    outdat[26]['altraw_samp'] = defs.nans(
                        [rdr._N[tmp_idx],
                         len(outdat[26]['altraw_samp'])],
                        dtype=np.uint16)
                else:
                    if sz != rdr._N[tmp_idx]:
                        raise Exception(
                            "The number of samples in this 'Altimeter Raw' "
                            "burst is different from prior bursts.")
                self.read_burst(id, outdat[id], c26)
                outdat[id]['ensemble'][c26] = c
                c26 += 1

            elif id in [22, 23, 27, 28, 29, 30, 31]:
                warnings.warn(
                    "Unhandled ID: 0x{:02X} ({:02d})\n"
                    "    This ID is not yet handled by DOLfYN.\n"
                    "    If possible, please file an issue and share a\n"
                    "    portion of your data file:\n"
                    "      http://github.com/lkilcher/dolfyn/issues/"
                    .format(id, id))
                self.f.seek(hdr['sz'], 1)
            elif id == 160:
                # 0xa0 (i.e., 160) is a 'string data record'
                if id not in outdat:
                    outdat[id] = dict()
                s_id, s = self.read_string(hdr['sz'], )
                outdat[id][(c, s_id)] = s
            else:
                if id not in self.unknown_ID_count:
                    self.unknown_ID_count[id] = 1
                    print('Unknown ID: 0x{:02X}!'.format(id))
                else:
                    self.unknown_ID_count[id] += 1
                self.f.seek(hdr['sz'], 1)
            # It's unfortunate that all of this count checking is so
            # complex, but this is the best I could come up with right
            # now.
            if c + ens_start + 1 >= nens_total:
                # Make sure we're not at the end of the count list.
                continue
            while (self.f.tell() >= self._ens_pos[c + ens_start + 1]):
                c += 1
                if c + ens_start + 1 >= nens_total:
                    # Again check end of count list
                    break
            if c >= nens:
                return outdat

    def read_burst(self, id, dat, c, echo=False):
        rdr = self._burst_readers[id]
        rdr.read_into(self.f, dat, c)

    def read_string(self, size):
        string = self.f.read(size)
        id = string[0]
        #end = string[-1]
        string = string[1:-1]
        return id, string

    def sci_data(self, dat):
        for id in dat:
            dnow = dat[id]
            if id not in self._burst_readers:
                continue
            rdr = self._burst_readers[id]
            rdr.sci_data(dnow)
            if 'vel' in dnow and 'vel_scale' in dnow:
                dnow['vel'] = (dnow['vel'] *
                               10.0 ** dnow['vel_scale']).astype('float32')

    def __exit__(self, type, value, trace,):
        self.f.close()

    def __enter__(self,):
        return self


def reorg(dat):
    """This function grabs the data from the dictionary of data types
    (organized by ID), and combines them into the
    :class:`dolfyn.ADPdata` object.
    """
    outdat = apb.ADPdata()
    cfg = outdat['config'] = db.config(_type='Nortek AD2CP')
    cfh = cfg['filehead config'] = dat['filehead config']
    cfg['model'] = (cfh['ID'].split(',')[0][5:-1])
    outdat['props'] = {}
    outdat['props']['inst_make'] = 'Nortek'
    outdat['props']['inst_model'] = cfg['model']
    outdat['props']['inst_type'] = 'ADP'
    outdat['props']['rotate_vars'] = {'vel', }

    for id, tag in [(21, ''), (24, '_b5'), (26, '_ar')]:
        if id == 26:
            collapse_exclude = [0]
        else:
            collapse_exclude = []
        if id not in dat:
            continue
        dnow = dat[id]
        cfg['burst_config' + tag] = lib.headconfig_int2dict(
            lib.collapse(dnow['config'], exclude=collapse_exclude,
                         name='config'))
        outdat['mpltime' + tag] = lib.calc_time(
            dnow['year'] + 1900,
            dnow['month'],
            dnow['day'],
            dnow['hour'],
            dnow['minute'],
            dnow['second'],
            dnow['usec100'].astype('uint32') * 100)
        tmp = lib.beams_cy_int2dict(
            lib.collapse(dnow['beam_config'], exclude=collapse_exclude,
                         name='beam_config'), 21)
        cfg['ncells' + tag] = tmp['ncells']
        cfg['coord_sys' + tag] = tmp['cy']
        cfg['nbeams' + tag] = tmp['nbeams']
        for ky in ['SerialNum', 'cell_size', 'blanking',
                   'nom_corr', 'data_desc',
                   'vel_scale', 'power_level']:
            # These ones should 'collapse'
            # (i.e., all values should be the same)
            # So we only need that one value.
            cfg[ky + tag] = lib.collapse(dnow[ky], exclude=collapse_exclude,
                                         name=ky)
        for ky in ['c_sound', 'temp', 'press',
                   'heading', 'pitch', 'roll',
                   'temp_press', 'batt_V',
                   'temp_mag', 'temp_clock',
                   'mag', 'accel',
                   'ambig_vel', 'xmit_energy',
                   'error', 'status0', 'status',
                   '_ensemble', 'ensemble']:
            # No if statement here
            outdat[ky + tag] = dnow[ky]
        for ky in [
                'vel', 'amp', 'corr',
                'alt_dist', 'alt_quality', 'alt_status',
                'ast_dist', 'ast_quality', 'ast_offset_time',
                'ast_pressure',
                'altraw_nsamp', 'altraw_dist', 'altraw_samp',
                'echo',
                'orientmat', 'angrt',
                'percent_good',
                'std_pitch', 'std_roll', 'std_heading', 'std_press'
        ]:
            if ky in dnow:
                outdat[ky + tag] = dnow[ky]
        for grp, keys in defs._burst_group_org.items():
            if grp not in outdat and \
               len(set(defs._burst_group_org[grp])
                   .intersection(outdat.keys())):
                    outdat[grp] = db.TimeData()
            for ky in keys:
                if ky == grp and ky in outdat and \
                   not isinstance(outdat[grp], db.TimeData):
                    tmp = outdat.pop(grp)
                    outdat[grp] = db.TimeData()
                    outdat[grp][ky] = tmp
                    #print(ky, tmp)
                if ky + tag in outdat and not \
                   isinstance(outdat[ky + tag], db.TimeData):
                    outdat[grp][ky + tag] = outdat.pop(ky + tag)

    # Move 'altimeter raw' data to it's own down-sampled structure
    if 26 in dat:
        ard = outdat['altraw'] = db.MappedTime()
        for ky in list(outdat.iter_data(include_hidden=True)):
            if ky.endswith('_ar'):
                grp = ky.split('.')[0]
                if '.' in ky and grp not in ard:
                    ard[grp] = db.TimeData()
                ard[ky.rstrip('_ar')] = outdat.pop(ky)
        N = ard['_map_N'] = len(outdat['mpltime'])
        parent_map = np.arange(N)
        ard['_map'] = parent_map[np.in1d(outdat.sys.ensemble, ard.sys.ensemble)]
        outdat['config']['altraw'] = db.config(_type='ALTRAW', **ard.pop('config'))
    outdat.props['coord_sys'] = {'XYZ': 'inst',
                                 'ENU': 'earth',
                                 'BEAM': 'beam'}[cfg['coord_sys'].upper()]
    tmp = lib.status2data(outdat.sys.status)  # returns a dict
    outdat.orient['orient_up'] = tmp['orient_up']
    # 0: XUP, 1: XDOWN, 4: ZUP, 5: ZDOWN
    # Heding is: 0,1: Z; 4,5: X
    for ky in ['accel', 'angrt']:
        if ky in outdat['orient']:
            outdat.props['rotate_vars'].update({'orient.' + ky})
    return outdat


def reduce(data):
    """This function takes the :class:``dolfyn.ADPdata`` object output
    from `reorg`, and further simplifies the data. Mostly this is
    combining system, environmental, and orientation data --- from
    different data structures within the same ensemble --- by
    averaging.  """
    # Average these fields
    for ky in ['mpltime',
               'c_sound', 'temp', 'press',
               'temp_press', 'temp_clock', 'temp_mag',
               'batt_V']:
        grp = defs.get_group(ky)
        if grp is None:
            dnow = data
        else:
            dnow = data[grp]
        lib.reduce_by_average(dnow, ky, ky + '_b5')

    # Angle-averaging is treated separately
    for ky in ['heading', 'pitch', 'roll']:
        lib.reduce_by_average_angle(data['orient'], ky, ky + '_b5')

    # Drop the ensemble count from other data structures
    for ky in ['_ensemble', 'ensemble']:
        if ky + '_b5' in data['sys']:
            data['sys'].pop(ky + '_b5')

    data['range'] = (np.arange(data['vel'].shape[1]) *
                     data['config']['cell_size'] +
                     data['config']['blanking'])
    if 'vel_b5' in data:
        data['range_b5'] = (np.arange(data['vel_b5'].shape[1]) *
                            data['config']['cell_size_b5'] +
                            data['config']['blanking_b5'])

    if 'orientmat' in data['orient']:
        data['props']['has imu'] = True
    else:
        data['props']['has imu'] = False
    data.config['fs'] = data.config['filehead config']['BURST'].pop('SR')
    data['props']['fs'] = data.config['fs']
    tmat = data.config['filehead config'].pop('XFBURST')
    tm = np.zeros((tmat['ROWS'], tmat['COLS']), dtype=np.float32)
    for irow in range(tmat['ROWS']):
        for icol in range(tmat['COLS']):
            tm[irow, icol] = tmat['M' + str(irow + 1) + str(icol + 1)]
    data.config['TransMatrix'] = tm


if __name__ == '__main__':

    rdr = Ad2cpReader('../../example_data/BenchFile01.ad2cp')
    rdr.readfile()

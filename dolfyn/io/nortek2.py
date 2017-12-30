"""This is the top-level module for reading Nortek Signature (.ad2cp)
files. It relies heavily on the `nortek2_defs` and `nortek2lib`
modules.
"""
from struct import unpack
import nortek2_defs as defs
import nortek2lib as lib
from ..adp.base import adcp_raw, adcp_config
import numpy as np


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
        dat = read_signature(infile, ens_now,
                             min(ens_now + nens_per_file, ens_stop))
        dat.save(outfile.format(file_count))
        file_count += 1
        ens_now += nens_per_file


def read_signature(filename, ens_start=0, ens_stop=None):
    """Read a Nortek Signature (.ad2cp) file.

    Parameters
    ==========
    filename : string
        The filename of the file to load.
    ens_start : int
        The first ensemble to load (default: 0)
    ens_stop : int
        The ensemble to stop at (default: None, i.e., load to the last
        ensemble)

    Returns
    =======
    dat : :class:`dolfyn.adp.base.adcp_raw` object
        An ADCP data object containing the loaded data.
    """
    rdr = Ad2cpReader(filename)
    d = rdr.readfile(ens_start, ens_stop)
    rdr.sci_data(d)
    out = reorg(d)
    reduce(out)
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
        for ky in self._burst_readers:
            outdat[ky] = self._burst_readers[ky].init_data(nens)
            outdat[ky]['ensemble'] = np.arange(ens_start,
                                               ens_stop).astype('uint32')
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
                raise Exception(
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
        return out

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
                print("Unhandled ID: 0x1A (26)\n"
                      "    There still seems to be a discrepancy between\n"
                      "    the '0x1A' data format, and the specification\n"
                      "    in the System Integrator Manual.")
                # Question posted at:
                # http://www.nortek-as.com/en/knowledge-center/forum/system-integration-and-telemetry/538802891
                self.f.seek(hdr['sz'], 1)
            elif id in [22, 23, 27, 28, 29, 30, 31]:
                print("Unhandled ID: 0x{:02X} ({:02d})\n"
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
    (organized by ID), and combines them into the adcp_raw object.
    """
    outdat = adcp_raw()
    cfg = outdat['config'] = adcp_config('Nortek AD2CP')
    outdat.groups.add('config', 'config')
    cfg['filehead config'] = dat['filehead config']

    for id, tag in [(21, ''), (24, '_b5')]:
        if id not in dat:
            continue
        dnow = dat[id]
        cfg['burst_config' + tag] = lib.headconfig_int2dict(
            lib.collapse(dnow['config']))
        outdat['mpltime' + tag] = lib.calc_time(
            dnow['year'] + 1900,
            dnow['month'],
            dnow['day'],
            dnow['hour'],
            dnow['minute'],
            dnow['second'],
            dnow['usec100'].astype('uint32') * 100)
        outdat.groups.add('mpltime' + tag, '_essential')
        tmp = lib.beams_cy_int2dict(
            lib.collapse(dnow['beam_config']), 21)
        cfg['ncells' + tag] = tmp['ncells']
        cfg['coord_sys' + tag] = tmp['cy']
        cfg['nbeams' + tag] = tmp['nbeams']
        for ky in ['SerialNum', 'cell_size', 'blanking',
                   'nom_corr', 'data_desc',
                   'vel_scale', 'power_level']:
            # These ones should 'collapse'
            # (i.e., all values should be the same)
            # So we only need that one value.
            cfg[ky + tag] = lib.collapse(dnow[ky])
        for ky in ['c_sound', 'temp', 'press',
                   'heading', 'pitch', 'roll',
                   'temp_press', 'batt_V',
                   'temp_mag', 'temp_clock',
                   'Mag', 'Acc',
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
                'orientmat', 'ahrs_gyro',
                'percent_good',
                'std_pitch', 'std_roll', 'std_heading', 'std_press'
        ]:
            if ky in dnow:
                outdat[ky + tag] = dnow[ky]
        for grp, keys in defs._burst_group_org.items():
            for ky in keys:
                if ky + tag in outdat:
                    outdat.groups.add(ky + tag, grp)
    outdat.props['coord_sys'] = cfg['coord_sys']
    return outdat


def reduce(data):
    """This function takes the adcp_raw object output from `reorg`,
    and further simplifies the data. Mostly this is combining system,
    environmental, and orientation data --- from different data
    structures within the same ensemble --- by averaging.
    """
    # Average these fields
    for ky in ['mpltime',
               'c_sound', 'temp', 'press',
               'temp_press', 'temp_clock', 'temp_mag',
               'batt_V']:
        lib.reduce_by_average(data, ky, ky + '_b5')

    # Angle-averaging is treated separately
    for ky in ['heading', 'pitch', 'roll']:
        lib.reduce_by_average_angle(data, ky, ky + '_b5')

    # Drop the ensemble count from other data structures
    for ky in ['_ensemble', 'ensemble']:
        if ky + '_b5' in data:
            data[ky] = data.pop_data(ky + '_b5')


if __name__ == '__main__':

    rdr = Ad2cpReader('../../example_data/BenchFile01.ad2cp')
    rdr.readfile()

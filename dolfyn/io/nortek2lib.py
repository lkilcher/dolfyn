# Branch read_signature-cython has the attempt to do this in Cython.

from __future__ import print_function
import struct
import os.path as path
import numpy as np
import warnings
from ..data import time


class CollapseError(Exception):
    """Exception for handling cases where collapsing a variable (from
    an array to a single value) fails. Generally (always?) because it
    is non-uniform.
    """
    def __init__(self, message):
        self.message = message


def reduce_by_average(data, ky0, ky1):
    # Average two arrays together, if they both exist.
    if ky1 in data:
        tmp = data.pop(ky1)
        if ky0 in data:
            data[ky0] += tmp
            data[ky0] = data[ky0] / 2
        else:
            data[ky0] = tmp


def reduce_by_average_angle(data, ky0, ky1, degrees=True):
    # Average two arrays of angles together, if they both exist.
    if degrees:
        rad_fact = np.pi / 180
    else:
        rad_fact = 1
    if ky1 in data:
        if ky0 in data:
            data[ky0] = np.angle(
                np.exp(1j * data.pop(ky0) * rad_fact) +
                np.exp(1j * data.pop(ky1) * rad_fact)) / rad_fact
        else:
            data[ky0] = data.pop(ky1)


# This is the data-type of the index file.
# This must match what is written-out by the create_index function.
index_dtype = {
    None:
    np.dtype([('ens', np.uint64),
              ('pos', np.uint64),
              ('ID', np.uint16),
              ('config', np.uint16),
              ('beams_cy', np.uint16),
              ('_blank', np.uint16),
              ('year', np.uint8),
              ('month', np.uint8),
              ('day', np.uint8),
              ('hour', np.uint8),
              ('minute', np.uint8),
              ('second', np.uint8),
              ('usec100', np.uint16),
    ]),
    1:
    np.dtype([('ens', np.uint64),
              ('hw_ens', np.uint32),
              ('pos', np.uint64),
              ('ID', np.uint16),
              ('config', np.uint16),
              ('beams_cy', np.uint16),
              ('_blank', np.uint16),
              ('year', np.uint8),
              ('month', np.uint8),
              ('day', np.uint8),
              ('hour', np.uint8),
              ('minute', np.uint8),
              ('second', np.uint8),
              ('usec100', np.uint16),
              ('d_ver', np.uint8),
    ])
}
index_version = 1

hdr = struct.Struct('<BBBBhhh')


def calc_time(year, month, day, hour, minute, second, usec, zero_is_bad=True):
    dt = np.empty(year.shape, dtype='O')
    for idx, (y, mo, d, h, mi, s, u) in enumerate(
            zip(year, month, day,
                hour, minute, second, usec)):
        if (zero_is_bad and mo == 0 and d == 0 and
                h == 0 and mi == 0 and
                s == 0 and u == 0):
            continue
        try:
            # Note that month is zero-based
            dt[idx] = time.datetime(y, mo + 1, d, h, mi, s, u)
        except ValueError:
            # One of the time values is out-of-range (e.g., mi > 60)
            # This probably indicates a corrupted byte, so we just insert None.
            dt[idx] = None
    # None -> NaN in this step
    return time.time_array(time.date2num(dt))


def create_index_slow(infile, outfile, N_ens):
    print("Indexing {}...".format(infile), end='')
    fin = open(infile, 'rb')
    fout = open(outfile, 'wb')
    fout.write(b'Index Ver:')
    fout.write(struct.pack('<H', index_version))
    ens = 0
    N = 0
    config = 0
    last_ens = -1
    seek_2ens = {21: 40, 24: 40, 26: 40,
                 23: 42, 28: 40}
    while N < N_ens:
        pos = fin.tell()
        try:
            dat = hdr.unpack(fin.read(hdr.size))
        except:
            break
        if dat[2] in [21, 23, 24, 26, 28]:
            d_ver, d_off, config = struct.unpack('<BBH', fin.read(4))
            fin.seek(4, 1)
            yr, mo, dy, h, m, s, u = struct.unpack('6BH', fin.read(8))
            fin.seek(14, 1)
            beams_cy = struct.unpack('<H', fin.read(2))[0]
            fin.seek(seek_2ens[dat[2]], 1)
            ens = struct.unpack('<I', fin.read(4))[0]
            if dat[2] in [23, 28]:
                # ensemble counter is garbage(=1 ?!) for these ids
                ens = last_ens
            if last_ens > 0 and last_ens != ens:
                N += 1
            fout.write(struct.pack('<QIQ4H6BHB', N, ens, pos, dat[2],
                                   config, beams_cy, 0,
                                   yr, mo + 1, dy, h, m, s, u, d_ver))
            fin.seek(dat[4] - (36 + seek_2ens[dat[2]]), 1)
            last_ens = ens
        else:
            fin.seek(dat[4], 1)
        # if N < 5:
        #     print('%10d: %02X, %d, %02X, %d, %d, %d, %d\n' %
        #           (pos, dat[0], dat[1], dat[2], dat[4],
        #            N, ens, last_ens))
        # else:
        #     break
    fin.close()
    fout.close()
    print(" Done.")


def _check_index(idx, ):
    _hw_ens = idx['hw_ens'].copy().astype('int32')
    period = _hw_ens.max()
    ens = np.unwrap(_hw_ens, period=period)
    ens -= ens[0]
    dens = np.diff(ens)
    bad = (dens < 0)
    if bad.any():
        dens[~bad] = 0
        ens[1:] -= dens
        while ens[1] - ens[0] > 1:
            ens[1:] -= 1
        idx['ens'] = ens
        first_bad = np.nonzero(bad)[0][0]
        if first_bad > 16:
            # The files that fail this test probably follow files that
            # already had this error.
            print("There appears to be a skipped ping in the file "
                  "at ensemble {}".format(idx['ens'][first_bad]))


def get_index(infile, reload=False):
    index_file = infile + '.index'
    if not path.isfile(index_file) or reload:
        create_index_slow(infile, index_file, 2 ** 32)
    # else:
    #     print("Using saved index file.")
    f = open(index_file, 'rb')
    file_head = f.read(12)
    if file_head[:10] == b'Index Ver:':
        index_ver = struct.unpack('<H', file_head[10:])[0]
    else:
        # This is pre-versioning the index files
        index_ver = None
        f.seek(0, 0)
    out = np.fromfile(f, dtype=index_dtype[index_ver])
    f.close()
    _check_index(out)
    return out


def boolarray_firstensemble_ping(index):
    """Return a boolean of the index that indicates only the first ping in for each ensemble.
    """
    if (index['ens'] == 0).all() and (index['hw_ens'] == 1).all():
        # This is an ugly hack.
        # This is for when the system runs in 'raw/continuous mode' or something?
        # Is there a better way to detect this mode?
        n_IDs = {id:(index['ID'] == id).sum() for id in np.unique(index['ID'])}
        assert np.abs(np.diff(list(n_IDs.values()))) <= 1, "Unable to read this file"
        return index['ID']==index['ID'][0]
    else:
        dens = np.ones(index['ens'].shape, dtype='bool')
        dens[1:] = np.diff(index['ens']) != 0
        return dens


def getbit(val, n):
    try:
        return bool((val >> n) & 1)
    except ValueError: # An array
        return ((val >> n) & 1).astype('bool')
        


def crop_ensembles(infile, outfile, range):
    """This function is for cropping certain pings out of an AD2CP
    file to create a new AD2CP file. It properly grabs the header from
    infile.

    The range is the `ensemble/ping` counter as defined in the first column
    of the INDEX.

    """
    idx = get_index(infile)
    with open(infile, 'rb') as fin:
        with open(outfile, 'wb') as fout:
            fout.write(fin.read(idx['pos'][0]))
            i0 = np.nonzero(idx['ens'] == range[0])[0][0]
            ie = np.nonzero(idx['ens'] == range[1])[0][0]
            pos = idx['pos'][i0]
            nbyte = idx['pos'][ie] - pos
            fin.seek(pos, 0)
            fout.write(fin.read(nbyte))


class BitIndexer(object):

    def __init__(self, data):
        self.data = data

    @property
    def _data_is_array(self, ):
        return isinstance(self.data, np.ndarray)

    @property
    def nbits(self, ):
        if self._data_is_array:
            return self.data.dtype.itemsize * 8
        else:
            raise ValueError("You must specify the end-range "
                             "for non-ndarray input data.")

    def _get_out_type(self, mask):
        # The mask indicates how big this item is.
        if not self._data_is_array:
            return None
        if mask < 2:
            return np.bool
        if mask < 2 ** 8:
            return np.uint8
        elif mask < 2 ** 16:
            return np.uint16
        elif mask < 2 ** 32:
            return np.uint32
        else:
            return np.uint64

    def __getitem__(self, slc):
        if isinstance(slc, int):
            slc = slice(slc, slc + 1)
        if slc.step not in [1, None]:
            raise ValueError("Slice syntax for `getbits` does "
                             "not support steps")
        start = slc.start
        stop = slc.stop
        if start is None:
            start = 0
        if stop is None:
            stop = self.nbits
        mask = 2 ** (stop - start) - 1
        out = (self.data >> start) & mask
        ot = self._get_out_type(mask)
        if ot is not None:
            out = out.astype(ot)
        return out


def headconfig_int2dict(val, mode='burst'):
    """Convert the burst Configuration bit-mask to a dict of bools.

    mode: {'burst', 'bt'}
       For 'burst' configs, or 'bottom-track' configs.
    """
    if mode == 'burst':
        return dict(
            press_valid=getbit(val, 0),
            temp_valid=getbit(val, 1),
            compass_valid=getbit(val, 2),
            tilt_valid=getbit(val, 3),
            # bit 4 is unused
            vel=getbit(val, 5),
            amp=getbit(val, 6),
            corr=getbit(val, 7),
            alt=getbit(val, 8),
            alt_raw=getbit(val, 9),
            ast=getbit(val, 10),
            echo=getbit(val, 11),
            ahrs=getbit(val, 12),
            p_gd=getbit(val, 13),
            std=getbit(val, 14),
            # bit 15 is unused
        )
    elif mode == 'bt':
        return dict(
            press_valid=getbit(val, 0),
            temp_valid=getbit(val, 1),
            compass_valid=getbit(val, 2),
            tilt_valid=getbit(val, 3),
            # bit 4 is unused
            vel=getbit(val, 5),
            # bits 6-7 unused
            dist=getbit(val, 8),
            fom=getbit(val, 9),
            ahrs=getbit(val, 10),
            # bits 10-15 unused
        )

def status2data(val):
    # This is detailed in the 6.1.2 of the Nortek Signature
    # Integrators Guide (2017)
    bi = BitIndexer(val)
    out = {}
    out['wakeup state'] = bi[28:32]
    out['orient_up'] = bi[25:28]
    out['auto orientation'] = bi[22:25]
    out['previous wakeup state'] = bi[18:22]
    out['last meas low voltage skip'] = bi[17]
    out['active config'] = bi[16]
    out['echo sounder index'] = bi[12:16]
    out['telemetry data'] = bi[11]
    out['boost running'] = bi[10]
    out['echo sounder freq bin'] = bi[5:10]
    # 2,3,4 unused
    out['bd scaling'] = bi[1]  # if True: cm scaling of blanking dist
    # 0 unused
    return out


def beams_cy_int2dict(val, id):
    """Convert the beams/coordinate-system bytes to a dict of values.
    """
    if id == 28:  # 0x1C (echosounder)
        return dict(ncells=val)
    return dict(
        ncells=val & (2 ** 10 - 1),
        cy=['ENU', 'XYZ', 'BEAM', None][val >> 10 & 3],
        nbeams=val >> 12
    )


def isuniform(vec, exclude=[]):
    if len(exclude):
        return len(set(np.unique(vec)) - set(exclude)) <= 1
    return np.all(vec == vec[0])


def collapse(vec, exclude=[], name=None):
    """Check that the input vector is uniform, then collapse it to a
    single value, otherwise raise a warning.
    """
    if name is None:
        name = '**unkown**'
    if isuniform(vec):
        return vec[0]
    elif isuniform(vec, exclude=exclude):
        return list(set(np.unique(vec)) - set(exclude))[0]
    else:
        raise CollapseError("The variable {} is expected to be uniform,"
                           " but it is not.".format(name))


def _failsafe_collapse(arr, name):
    try:
        return collapse(arr, name=name)
    except CollapseError:
        try:
            return collapse(arr, exclude=[0],
                            name=name)
        except CollapseError:
            return collapse(arr[-16:16],
                            exclude=[0],
                            name=name)


def calc_config(index):
    """Calculate the configuration information (e.g., number of pings,
    number of beams, struct types, etc.) from the index data.

    Returns
    =======
    config : dict
        A dict containing the key information for initializing arrays.
    """
    ids = np.unique(index['ID'])
    config = {}
    for id in ids:
        if id not in [21, 23, 24, 26, 28]:
            continue
        if id == 23:
            type = 'bt'
        else:
            type = 'burst'
        inds = index['ID'] == id
        _config = index['config'][inds]
        _beams_cy = index['beams_cy'][inds]
        # Check that these variables are consistent
        if not isuniform(_config):
            raise Exception("config are not identical for id: 0x{:X}."
                            .format(id))
        if not isuniform(_beams_cy):
            raise Exception("beams_cy are not identical for id: 0x{:X}."
                            .format(id))
        # Now that we've confirmed they are the same:
        config[id] = headconfig_int2dict(_config[0], mode=type)
        config[id].update(beams_cy_int2dict(_beams_cy[0], id))
        config[id]['_config'] = _config[0]
        config[id]['_beams_cy'] = _beams_cy[0]
        config[id]['type'] = type
        config[id].pop('cy', None)
    return config


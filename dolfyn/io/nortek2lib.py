# Branch read_signature-cython has the attempt to do this in Cython.

from __future__ import print_function
import struct
import os.path as path
import numpy as np
import warnings


index_dtype = np.dtype([('ens', np.uint64),
                        ('pos', np.uint64),
                        ('ID', np.uint16),
                        ('config', np.uint16),
                        ('beams_cy', np.uint16),
                        ('_blank', np.uint16),
                        ])

hdr = struct.Struct('<BBBBhhh')


def create_index_slow(infile, outfile, N_ens):
    fin = open(infile, 'rb')
    fout = open(outfile, 'wb')
    ens = 0
    N = 0
    config = 0
    last_ens = 1
    while N < N_ens:
        pos = fin.tell()
        try:
            dat = hdr.unpack(fin.read(hdr.size))
        except:
            break
        if dat[2] in [21, 24]:
            fin.seek(2, 1)
            config = struct.unpack('<H', fin.read(2))[0]
            fin.seek(26, 1)
            beams_cy = struct.unpack('<H', fin.read(2))[0]
            fin.seek(40, 1)
            ens = struct.unpack('<I', fin.read(4))[0]
            if last_ens != ens:
                N += 1
            fout.write(struct.pack('<QQ4H', N, pos, dat[2],
                                   config, beams_cy, 0))
            fin.seek(dat[4] - 76, 1)
            last_ens = ens
        else:
            fin.seek(dat[4], 1)
        # if N < 5:
        #     print('%10d: %02X, %d, %02X, %d, %d, %d, %d\n' %
        #           (pos, dat[0], dat[1], dat[2], dat[4],
        #            N, ens, last_ens))
    fin.close()
    fout.close()


def get_index(infile, reload=False):
    index_file = infile + '.index'
    if not path.isfile(index_file) or reload:
        print("Indexing...", end='')
        if reload:
            create_index_slow(infile, index_file, 2 ** 32)
        print(" Done.")
    else:
        print("Using saved index file.")
    return np.fromfile(index_file, dtype=index_dtype)


def index2ens_pos(index):
    """Condense the index to only be the first occurence of each
    ensemble. Returns only the position (the ens number is the array
    index).
    """
    dens = np.ones(index['ens'].shape, dtype='bool')
    dens[1:] = np.diff(index['ens']) != 0
    return index['pos'][dens]


def getbit(val, n):
    return bool((val >> n) & 1)


def headconfig_int2dict(val):
    return dict(
        press_valid=getbit(val, 0),
        temp_valid=getbit(val, 1),
        compass_valid=getbit(val, 2),
        tilt_valid=getbit(val, 3),
        # bit 4 is unused
        vel=getbit(val, 5),
        amp=getbit(val, 6),
        corr=getbit(val, 7),
        alti=getbit(val, 8),
        altiRaw=getbit(val, 9),
        AST=getbit(val, 10),
        Echo=getbit(val, 11),
        ahrs=getbit(val, 12),
        PGood=getbit(val, 13),
        stdDev=getbit(val, 14),
        # bit 15 is unused
    )


def beams_cy_int2dict(val, id):
    if id == 28:  # 0x1C (echosounder)
        return dict(ncells=val)
    return dict(
        ncells=val & (2 ** 10 - 1),
        cy=['ENU', 'XYZ', 'BEAM', None][val >> 10 & 3],
        nbeams=val >> 12
    )


def isuniform(vec):
    return np.all(vec == vec[0])


def collapse(vec, name=None):
    if name is None:
        name = '**unkown**'
    if not isuniform(vec):
        warnings.warn("The variable {} is expected to be uniform,"
                      " but it is not.".format(name))
        return vec
    return vec[0]


def calc_config(index):
    ids = np.unique(index['ID'])
    config = {}
    for id in [21, 24]:
        inds = index['ID'] == id
        _config = index['config'][inds]
        _beams_cy = index['beams_cy'][inds]
        if id not in ids:
            continue
        # Check that these variables are consistent
        if not isuniform(_config):
            raise Exception("config are not identical for id: 0x{:X}."
                            .format(id))
        if not isuniform(_beams_cy):
            raise Exception("beams_cy are not identical for id: 0x{:X}."
                            .format(id))
        # Now that we've confirmed they are the same:
        config[id] = headconfig_int2dict(_config[0])
        config[id].update(beams_cy_int2dict(_beams_cy[0], id))
        config[id]['_config'] = _config[0]
        config[id]['_beams_cy'] = _beams_cy[0]
        config[id].pop('cy')
    return config


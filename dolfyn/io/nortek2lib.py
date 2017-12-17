# Branch read_signature-cython has the attempt to do this in Cython.

from __future__ import print_function
import struct
import os.path as path
import numpy as np


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

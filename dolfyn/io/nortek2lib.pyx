from __future__ import print_function
import struct
from libc.stdio cimport printf, fread, FILE, fopen, fseek, ftell, SEEK_CUR, fclose, fwrite
import os.path as path
cimport nortek2lib_defs as lib
import numpy as np
cimport numpy as np


cdef struct Index:
    np.uint32_t N
    np.uint16_t ID # This is uint8 in the data, but we need this struct to be a multiple of 64 bits, so it's padded here
    np.uint16_t config
    np.uint64_t pos

hdr = struct.Struct('<BBBBhhh')

    
def create_index_slow(infile, outfile, N_ens):
    fin = open(infile, 'rb')
    fout = open(outfile, 'wb')
    ens = 0
    last_ens = None
    N = 0
    config = 0
    while N < N_ens:
        pos = fin.tell()
        try:
            dat = hdr.unpack(fin.read(hdr.size))
        except:
            break
        if dat[2] in [21, 24]:
            fin.seek(2, 1)
            config = struct.unpack('<H', fin.read(2))[0]
            fin.seek(68, 1)
            ens = struct.unpack('<I', fin.read(4))[0]
            if last_ens != ens:
                #print(N, ens, config, pos)
                fout.write(struct.pack('<LHHQ', N, dat[2], config, pos))
                N += 1
            fin.seek(dat[4] - 76, 1)
        else:
            fin.seek(dat[4], 1)
        last_ens = ens
        #print('%10d: %02X, %d, %02X, %d\n' % (pos, dat[0], dat[1], dat[2], dat[4]))
    fin.close()
    fout.close()


cdef create_index(str infile, str outfile, long N_ens):
    cdef FILE *fin = fopen(infile, "rb")
    cdef FILE *fout = fopen(outfile, "wb")
    cdef lib.Header hd
    cdef np.uint32_t ens, last_ens, retval, ensemble_pos
    cdef Index idx
    #cdef lib.BurstHead bhead
    ensemble_pos = 72
    idx.N = 0
    idx.ID = 0
    idx.config = 0
    last_ens = 0
    while idx.N < N_ens:
        idx.pos = ftell(fin)
        retval = fread(&hd, sizeof(lib.Header), 1, fin)
        if retval < 1:
            # Presumably this is the end of the file.
            # I could do more checking here with feof or ferror, if necessary.
            break
        if hd.ID in [21, 24]:
            idx.ID = hd.ID
            fseek(fin, 2, SEEK_CUR)
            fread(&idx.config, sizeof(idx.config), 1, fin)
            # fread(&bhead, sizeof(bhead), 1, fin)
            # fseek(fin, -sizeof(bhead), SEEK_CUR)
            #printf("ver: %02d, off: %02d, year: %04d, ens: %05d, longsize: %d, ret: %d\n", bhead.ver, bhead.DataOffset, bhead.year + 1900, bhead.ens, sizeof(ens), retval)
            # Scan ahead 72 bytes to where the ensemble count is.
            fseek(fin, ensemble_pos - 4, SEEK_CUR)
            fread(&ens, sizeof(ens), 1, fin)
            fwrite(&idx, sizeof(idx), 1, fout)
            idx.N += 1
            fseek(fin, hd.dataSize - ensemble_pos - sizeof(ens), SEEK_CUR)
        else:
            fseek(fin, hd.dataSize, SEEK_CUR)
        #printf('%10ld: %02X, %d, %02X, %d, %05u\n', idx.pos, hd.sync, hd.hdrSize, hd.ID, hd.dataSize, ens)
        last_ens = ens
    fclose(fin)
    fclose(fout)


cpdef get_index(infile, reload=False):
    index_file = infile + '.index'
    if not path.isfile(index_file) or reload:
        print("Indexing...", end='')
        if reload == 'slow':
            create_index_slow(infile, index_file, 2 ** 32)
        create_index(infile, index_file, 2 ** 32)
        print(" Done.")
    else:
        print("Using saved index file.")
    #return np.fromfile(index_file, dtype=np.dtype([('ens', '>u4'), ('pos', '>u8')]))
    return np.fromfile(index_file, dtype=np.dtype([('ens', '<u4'), ('ID', '<u2'), ('config', '<u2'), ('pos', '<u8')]))
    #return np.fromfile(index_file, dtype=np.uint32 ).reshape((-1, 2))



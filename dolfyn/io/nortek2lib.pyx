from __future__ import print_function
import struct
from libc.stdio cimport printf, fread, FILE, fopen, fseek, ftell, SEEK_CUR, SEEK_SET, fclose, fwrite, feof, ferror
from libc.stdlib cimport malloc, free
import os.path as path
cimport nortek2lib_defs as lib
import numpy as np
cimport numpy as np
#from cpython import dict


cdef struct Index:
    np.uint64_t N
    np.uint64_t pos
    np.uint16_t ID # This is uint8 in the data, but we need this struct to be a multiple of 64 bits, so it's padded here
    np.uint16_t config
    np.uint16_t beams_cy
    np.uint16_t _blank

# This must match above
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
            fout.write(struct.pack('<QQ4H', N, pos, dat[2], config, beams_cy, 0))
            fin.seek(dat[4] - 76, 1)
            last_ens = ens
        else:
            fin.seek(dat[4], 1)
        # if N < 5:
        #     print('%10d: %02X, %d, %02X, %d, %d, %d, %d\n' % (pos, dat[0], dat[1], dat[2], dat[4], N, ens, last_ens))
    fin.close()
    fout.close()


cdef create_index(str infile, str outfile, long N_ens):
    cdef FILE *fin = fopen(infile, "rb")
    cdef FILE *fout = fopen(outfile, "wb")
    cdef lib.Header hd
    cdef np.uint32_t ens, retval, last_ens
    cdef Index idx
    #cdef lib.BurstHead bhead
    idx.N = 0
    idx.ID = 0
    idx.config = 0
    idx._blank = 0
    last_ens = 1
    while idx.N < N_ens:
        idx.pos = ftell(fin)
        retval = fread(&hd, sizeof(lib.Header), 1, fin)
        if retval < 1:
            # Presumably this is the end of the file.
            # I could do more checking here with feof or ferror, if necessary.
            break
        if hd.ID in [21, 24]:
            idx.ID = hd.ID
            fseek(fin, 2, SEEK_CUR) # 2 bytes (pos: 2)
            fread(&idx.config, sizeof(idx.config), 1, fin) # 2 bytes (pos: 4)
            fseek(fin, 26, SEEK_CUR) # 26 (pos: 30)
            fread(&idx.beams_cy, sizeof(idx.beams_cy), 1, fin) # 2 bytes (pos: 32)
            fseek(fin, 40, SEEK_CUR) # 40 (pos: 72)
            fread(&ens, sizeof(ens), 1, fin) # 4 bytes (pos: 76)
            if last_ens != ens:
                idx.N += 1
            fwrite(&idx, sizeof(idx), 1, fout)
            fseek(fin, hd.dataSize - 76, SEEK_CUR)
            last_ens = ens
        else:
            fseek(fin, hd.dataSize, SEEK_CUR)
        # if idx.N < 5:
        #     printf('%10ld: %02X, %d, %02X, %d, %05u, %05u\n', idx.pos, hd.sync, hd.hdrSize, hd.ID, hd.dataSize, ens, last_ens)
    fclose(fin)
    fclose(fout)


cdef zeros_3D_int16(size):
    narr = np.zeros(size, dtype=np.dtype('int16'))
    cdef short[:, :, :] narr_view = narr
    return narr, narr_view
    

cpdef test_readfile(str infile, config, index, np.uint64_t ens_start, np.uint64_t ens_stop):
    npings = ens_stop - ens_start
    cdef lib.Header hd
    cdef lib.BurstHead bhead
    cdef np.uint64_t c = 0
    cdef short *vel_tmp24 = <short *>malloc(config[24]['nbeams'] * config[24]['ncells'] * sizeof(short))
    if 24 in config:
        cfg = config[24]
        if cfg['vel']:
            vel_arr24, vel_arr24_v = zeros_3D_int16((cfg['nbeams'], cfg['ncells'], npings))
    start_pos = index[ens_start]
    stop_pos = index[ens_stop]
    cdef FILE *fin = fopen(infile, "rb")
    fseek(fin, start_pos, SEEK_SET)
    while ftell(fin) < stop_pos:
        retval = fread(&hd, sizeof(hd), 1, fin)
        if retval < 1:
            # Presumably this is the end of the file.
            # I could do more checking here with feof or ferror, if necessary.
            break
        print('hello!!')
        # Read the fixed header
        if hd.ID == 24:
            retval = fread(&bhead, sizeof(lib.BurstHead), 1, fin)
            if cfg['vel']:
                print('hello')
                fread(&vel_tmp24, sizeof(vel_tmp24), 1, fin)
                velarr24_v[:, :, c] = vel_tmp24
                break
    fclose(fin)
    free(vel_tmp24)
    vel_arr24_v[:, :, 10] = 1
    return dict(vel_arr24=vel_arr24)


cpdef get_index(infile, reload=False):
    index_file = infile + '.index'
    if not path.isfile(index_file) or reload:
        print("Indexing...", end='')
        if reload == 'slow':
            create_index_slow(infile, index_file, 2 ** 32)
        else:
            create_index(infile, index_file, 2 ** 32)
        print(" Done.")
    else:
        print("Using saved index file.")
    #return np.fromfile(index_file, dtype=np.dtype([('ens', '>u4'), ('pos', '>u8')]))
    return np.fromfile(index_file, dtype=index_dtype)
    #return np.fromfile(index_file, dtype=np.uint32 ).reshape((-1, 2))



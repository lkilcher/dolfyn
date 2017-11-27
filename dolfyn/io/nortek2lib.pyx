import struct
from libc.stdio cimport printf, fread, FILE, fopen, fseek, ftell, SEEK_CUR, fclose, fwrite

cdef struct Header:
    unsigned char  sync
    unsigned char  hdrSize
    unsigned char  ID
    unsigned char  family
    unsigned short dataSize
    unsigned short dataChecksum
    unsigned short hdrChecksum

cdef struct Index:
    unsigned long N
    unsigned long pos

hdr = struct.Struct('<BBBBhhh')
    
def indexfile_slow(fname, N_iter):
    f = open(fname, 'rb')
    for idx in range(N_iter):
        pos = f.tell()
        dat = hdr.unpack(f.read(hdr.size))
        f.seek(dat[4], 1)
        #print('%10d: %02X, %d, %02X, %d\n' % (pos, dat[0], dat[1], dat[2], dat[4]))
    f.close()


cpdef indexfile(str infile, str outfile, int N_iter):
    cdef FILE *fin = fopen(infile, "rb")
    cdef FILE *fout = fopen(outfile, "wb")
    cdef Header hd
    cdef unsigned long ens, last_ens, pos
    for i in range(N_iter):
        pos = ftell(fin)
        fread(&hd, sizeof(Header), 1, fin)
        printf('%10ld: %02X, %d, %02X, %d\n', pos, hd.sync, hd.hdrSize, hd.ID, hd.dataSize)
        fseek(fin, hd.dataSize, SEEK_CUR)
    fclose(fin)
    fclose(fout)

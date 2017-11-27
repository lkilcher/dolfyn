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

cdef struct BurstHead:
    unsigned char ver
    unsigned char DataOffset
    unsigned short config
    unsigned int SerialNum
    unsigned char year
    unsigned char month
    unsigned char day
    unsigned char hour
    unsigned char minute
    unsigned char second
    unsigned short usec100
    unsigned short c_sound
    signed short temp
    signed int pressure
    unsigned short heading
    unsigned short pitch
    unsigned short roll
    unsigned short HeadConfig
    unsigned short CellSize
    unsigned short Blanking
    unsigned char NomCorr
    unsigned char TempPress
    unsigned short Voltage
    unsigned short MagX
    unsigned short MagY
    unsigned short MagZ
    unsigned short AccX
    unsigned short AccY
    unsigned short AccZ
    unsigned short AmbigVel
    unsigned short DataDescription
    unsigned short TransmitEnergy
    signed char VelScale
    signed char PowerLevel
    signed short TempMag
    signed short TempClock
    unsigned short Error
    unsigned short Status0
    unsigned int Status
    unsigned int ens


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


cpdef create_index(str infile, str outfile):
    cdef FILE *fin = fopen(infile, "rb")
    cdef FILE *fout = fopen(outfile, "wb")
    cdef Header hd
    cdef unsigned int ens, last_ens, retval
    cdef unsigned long pos
    cdef Index idx
    cdef int ensemble_pos = 72
    cdef BurstHead bhead
    idx.N = 0
    last_ens = 0
    while True:
        idx.pos = ftell(fin)
        retval = fread(&hd, sizeof(Header), 1, fin)
        if retval < 1:
            # Presumably this is the end of the file.
            # I could do more checking here with feof or ferror, if necessary.
            break
        if hd.ID in [21, 24]:
            fread(&bhead, sizeof(bhead), 1, fin)
            fseek(fin, -sizeof(bhead), SEEK_CUR)
            #printf("ver: %02d, off: %02d, year: %04d, ens: %05d, longsize: %d, ret: %d\n", bhead.ver, bhead.DataOffset, bhead.year + 1900, bhead.ens, sizeof(ens), retval)
            # Scan ahead 72 bytes to where the ensemble count is.
            fseek(fin, ensemble_pos, SEEK_CUR)
            fread(&ens, sizeof(ens), 1, fin)
            if last_ens != ens:
                fwrite(&idx, sizeof(idx), 1, fout)
                idx.N += 1
            fseek(fin, hd.dataSize - ensemble_pos - sizeof(ens), SEEK_CUR)
        else:
            fseek(fin, hd.dataSize, SEEK_CUR)
        #printf('%10ld: %02X, %d, %02X, %d, %05u\n', idx.pos, hd.sync, hd.hdrSize, hd.ID, hd.dataSize, ens)
        last_ens = ens
    fclose(fin)
    fclose(fout)

from struct import unpack, calcsize
import nortek2_defs as defs
import bitops as bo
from nortek2lib import get_index, index2ens_pos
import pdb
reload(defs)    


class Ad2cpReader(object):
    debug = False

    def __init__(self, fname, endian=None, bufsize=None, rebuild_index=False):

        self.fname = fname
        self._check_nortek(endian)
        self.c = 0
        self._burst_readers = {}
        self.reopen(bufsize)
        self._index = get_index(fname,
                                reload=rebuild_index)
        self._ens_pos = index2ens_pos(self._index)

    def init_data(self, npings=None):
        pass

    def _readbyte(self, backward=False):
        print self.f.tell()
        if backward:
            self.f.seek(-2, 1)
        return self.f.read(1)

    def _scan4sync(self, backward=False):
        while self._readbyte(backward=backward) != b'\xa5':
            pass
        self.f.seek(-1, 1)

    def read_hdr(self, do_cs=False):
        res = defs._header.read2dict(self.f, cs=do_cs)
        if res['sync'] != 165:
            raise Exception("Out of sync!")
        return res

    def ens_seek(self, ensnum):
        for c in range(ensnum):
            h = self.read_hdr()
            self.f.seek(h['sz'], 1)

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

    def readfile(self, npings=None):
        print('Reading file %s ...' % self.fname)
        retval = None
        dout0 = []
        dout1 = []
        while not retval:
            hdr = self.read_hdr()
            id = hdr['id']
            #print id
            if id in [21, 24]:
                dnow = self.read_burst()
            else:
                # 0xa0 (i.e., 160) is a 'string data record',
                # according to the AD2CP manual
                # Need to catch the string at some point...
                self.f.seek(hdr['sz'], 1)
            if id == 21:
                dout0.append(dnow)
            elif id == 24:
                dout1.append(dnow)
            self.c += 1
            #print self.c
            if self.c >= npings:
                return (dout0, dout1)

    def _read(self, strct):
        nbyte = strct.size
        byts = self.f.read(nbyte)
        if not (len(byts) == nbyte):
            raise EOFError('Reached the end of the file')
        return strct.unpack(byts)

    def read(self, format):
        nbyte = calcsize(format)
        byts = self.f.read(nbyte)
        if not (len(byts) == nbyte):
            raise EOFError('Reached the end of the file')
        return unpack(self.endian + format, byts)

    def read_burst(self, echo=False):
        b_hd = defs._burst_hdr.read2dict(self.f)
        if not echo:
            bcfg = bo.bs16(b_hd['beam_config'])
            b_hd['n_cells'] = int(bcfg[-10:], 2)
            b_hd['coord_sys'] = ['ENU', 'XYZ',
                                 'BEAM', None][int(bcfg[-12:-10], 2)]
            b_hd['n_beams'] = int(bcfg[-16:-12], 2)
        else:
            b_hd['n_cells'] = b_hd['beam_config']
        reader_id = (b_hd['config'], b_hd['beam_config'])
        try:
            brdr = self._burst_readers[reader_id]
            #print("using cached reader")
        except KeyError:
            print("Loading reader")
            brdr = self._burst_readers[reader_id] = defs.calc_burst_struct(
                b_hd['config'], b_hd['n_beams'], b_hd['n_cells'])
        dat = brdr.read2dict(self.f)
        # Note, for some reason, the ENS counter tops out (and starts
        # over) at 2**12 (4096). I do not know why. After all, there
        # are 32 bits available here.
        if self.debug == 1:
            print 'ENS: {:016d} '.format(b_hd['ensemble'])
        return dat, b_hd

    def __exit__(self, type, value, trace,):
        self.f.close()

    def __enter__(self,):
        return self

    @property
    def pos(self, ):
        return self.f.tell()


if __name__ == '__main__':

    rdr = Ad2cpReader('../../example_data/BenchFile01.ad2cp')
    rdr.readfile()

from struct import unpack, calcsize
import nortek2_defs as defs
import bitops as bo
from nortek2lib import get_index, index2ens_pos, calc_config
from ..adp.base import adcp_raw
import pdb
reload(defs)    


class Ad2cpReader(object):
    debug = False

    def __init__(self, fname, endian=None, bufsize=None, rebuild_index=False):

        self.fname = fname
        self._check_nortek(endian)
        self.reopen(bufsize)
        self._index = get_index(fname,
                                reload=rebuild_index)
        self._ens_pos = index2ens_pos(self._index)
        self._config = calc_config(self._index)
        self._init_burst_readers()

    def _init_burst_readers(self, ):
        self._burst_readers = {}
        for rdr_id, cfg in self._config.items():
            self._burst_readers[rdr_id] = defs.calc_burst_struct(
                cfg['_config'], cfg['nbeams'], cfg['ncells'])

    def init_data(self, nens):
        outdat = {}
        for ky in self._burst_readers:
            outdat[ky] = self._burst_readers[ky].init_data(nens)
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

    def readfile(self, ens_start=0, ens_stop=None):
        if ens_stop is None:
            ens_stop = len(self._ens_pos)
        nens = ens_stop - ens_start
        outdat = self.init_data(nens)
        print('Reading file %s ...' % self.fname)
        retval = None
        c = 0
        if ens_start > 0:
            self.f.seek(self._ens_pos[ens_start], 0)
        while not retval:
            hdr = self.read_hdr()
            id = hdr['id']
            if id in [21, 24]:
                self.read_burst(id, outdat[id], c)
            else:
                # 0xa0 (i.e., 160) is a 'string data record',
                # according to the AD2CP manual
                # Need to catch the string at some point...
                self.f.seek(hdr['sz'], 1)
            while self.f.tell() >= self._ens_pos[c + ens_start + 1]:
                c += 1
            if c >= nens:
                return outdat

    def read_burst(self, id, dat, c, echo=False):
        b_hd = defs._burst_hdr.read2dict(self.f)
        rdr = self._burst_readers[id]
        rdr.read_into(self.f, dat, c)
        # Note, for some reason, the ENS counter tops out (and starts
        # over) at 2**12 (4096). I do not know why. After all, there
        # are 32 bits available here.
        #pdb.set_trace()
        if self.debug == 1:
            print 'ENS: {:016d} '.format(b_hd['ensemble'])
        return dat, b_hd

    def __exit__(self, type, value, trace,):
        self.f.close()

    def __enter__(self,):
        return self


if __name__ == '__main__':

    rdr = Ad2cpReader('../../example_data/BenchFile01.ad2cp')
    rdr.readfile()

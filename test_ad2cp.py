import dolfyn.io.nortek2 as nrtk
import os.path as path
import warnings
reload(nrtk)

# warnings.filterwarnings('error')

testfile = path.expanduser('~/data/WA2017/SMB500_Signature1000_Jul2017/'
                           'SMB500_Sig1000_Jul2017.ad2cp')


def readfile(e_start=0, e_stop=None):
    rdr = nrtk.Ad2cpReader(testfile)
    d = rdr.readfile(e_start, e_stop)
    rdr.sci_data(d)
    out = nrtk.reorg(d)
    nrtk.reduce(out)
    return out, d


#dat, d = readfile(0, 1000)
dat, d = readfile(0, None)
dat.save('/Users/lkilcher/tmp/test.h5')

import dolfyn.io.nortek2 as nrtk
import os.path as path
reload(nrtk)

testfile = path.expanduser('~/data/WA2017/SMB500_Signature1000_Jul2017/'
                           'SMB500_Sig1000_Jul2017.ad2cp')


def readfile(nens):
    rdr = nrtk.Ad2cpReader(testfile)
    d = rdr.readfile(0, nens)
    rdr.sci_data(d)
    return rdr.organize2dolfyn(d), d


dat, d = readfile(1000)

import dolfyn.io.nortek2 as nrtk
import os.path as path
import pyximport
pyximport.install(reload_support=True)
import dolfyn.io.nortek2lib as nlib
reload(nrtk)
reload(nlib)
import numpy as np

testfile = path.expanduser('~/data/WA2017/SMB500_Signature1000_Jul2017/SMB500_Sig1000_Jul2017.ad2cp')

#rdr = nrtk.Ad2cpReader(testfile)
#rdr.readfile(10000)
#rdr._scan4sync()
#h = rdr._ensemble_total()

#nlib.indexfile_slow(testfile, 'tmp/test_index.dat', 1000000)
#nlib.get_index(testfile, reload=True)
#nlib.indexfile_slow(testfile, 100)

idx = nlib.get_index(testfile, reload=True)

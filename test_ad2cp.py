import dolfyn.io.nortek2 as nrtk
import os.path as path
import dolfyn.io.nortek2lib as lib
import numpy as np
reload(nrtk)

testfile = path.expanduser('~/data/WA2017/SMB500_Signature1000_Jul2017/SMB500_Sig1000_Jul2017.ad2cp')

idx = lib.get_index(testfile)

rdr = nrtk.Ad2cpReader(testfile)
d = rdr.readfile(0, 10000)
rdr.sci_data(d)
#rdr._scan4sync()
#h = rdr._ensemble_total()

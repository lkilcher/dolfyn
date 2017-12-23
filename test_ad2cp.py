import dolfyn.io.nortek2 as nrtk
import os.path as path
import dolfyn.io.nortek2lib as lib
import warnings
reload(nrtk)

# warnings.filterwarnings('error')

testfile = path.expanduser('~/data/WA2017/SMB500_Signature1000_Jul2017/'
                           'SMB500_Sig1000_Jul2017.ad2cp')
testfile = path.expanduser('~/data/wp2017/adp/signature/'
                           'S100259A012_WPdeploy.ad2cp')


#idx = lib.get_index(testfile, reload=True)
idx = lib.get_index(testfile)

# dat = nrtk.read_signature(testfile, 10195200, 10368000)
dat = nrtk.read_signature(testfile, 10368000, 10540800)

#dat = nrtk.read_signature(testfile, 0, 10000)
#nrtk.split_to_hdf(testfile, 100000)
#dat, d = readfile(0, None)
#dat.save('/Users/lkilcher/tmp/test.h5')

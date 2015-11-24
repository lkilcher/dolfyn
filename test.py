#import dolfyn.adv.api as avm
import dolfyn.io.nortek as nrtk
reload(nrtk)

datfile = 'example_data/vector_data01.VEC'

# d=np.zeros(100)
rdr = nrtk.NortekReader(datfile, debug=False, do_checksum=True)
rdr.readfile()
rdr.dat2sci()

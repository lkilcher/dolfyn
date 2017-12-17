#import dolfyn.io.nortek2 as nrtk
#reload(nrtk)
import os
import numpy as np
os.environ['CFLAGS'] = '-I' + np.get_include()
import pyximport
pyximport.install(
    # setup_args={
    #     #"script_args": ["--compiler=clang"],
    #     "include_dirs": np.get_include()},
    reload_support=True)
import dolfyn.io.nortek2lib as nlib
import dolfyn.io.nortek2_junk as nlibj
reload(nlib)
reload(nlibj)

testfile = os.path.expanduser('~/data/WA2017/SMB500_Signature1000_Jul2017/SMB500_Sig1000_Jul2017.ad2cp')

#rdr = nrtk.Ad2cpReader(testfile)
#rdr.readfile(10000)
#rdr._scan4sync()
#h = rdr._ensemble_total()

#nlib.indexfile_slow(testfile, 'tmp/test_index.dat', 1000000)
#nlib.get_index(testfile, reload=True)
#nlib.indexfile_slow(testfile, 100)

#idx = nlib.get_index(testfile, reload='slow')
#idx = nlib.get_index(testfile, reload=True)
idx = nlib.get_index(testfile)
#idx['beams_cy'][2] = 6


def read_ad2cp(filename, index, ens_start=None, ens_stop=None):
    if ens_start is None:
        ens_start = 0
    if ens_stop is None:
        ens_stop = index['ens'][-1]
    print(type(ens_stop))
    ids = np.unique(index['ID'])
    config = {}
    for id in [21, 24]:
        inds = index['ID'] == id
        _config = index['config'][inds]
        _beams_cy = index['beams_cy'][inds]
        if id not in ids:
            continue
        # Check that these variables are consistent
        if not np.all(_config == _config[0]):
            raise Exception("config are not identical for id: 0x{:X}."
                            .format(id))
        if not np.all(_beams_cy == _beams_cy[0]):
            raise Exception("beams_cy are not identical for id: 0x{:X}."
                            .format(id))
        # Now that we've confirmed they are the same:
        config[id] = nlibj.headconfig_int2dict(_config[0])
        config[id].update(nlibj.beams_cy_int2dict(_beams_cy[0], id))
        config[id].pop('cy')
    val = nlib.test_readfile(filename, config,
                             nlibj.first_index(index),
                             ens_start, ens_stop)
    return val

dat = read_ad2cp(testfile, idx, 100, 200)

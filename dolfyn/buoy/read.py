import base as buoy
from ..data import time
import numpy as np


def readtxt(fname):
    with open(fname) as fl:
        h1 = fl.readline()
        h2 = fl.readline()
        dat = fl.readlines()
    n = len(dat)
    odat = buoy.buoy_raw()
    odat.add_data('mpltime', np.empty((n), dtype=np.float64))
    odat.add_data('wspd', np.empty((n), dtype=np.float32))
    odat.add_data('wdir', np.empty((n), dtype=np.float32))
    odat.add_data('gst', np.empty((n), dtype=np.float32))
    odat.add_data('wvht', np.empty((n), dtype=np.float32))
    odat.add_data('apd', np.empty((n), dtype=np.float32))
    odat.add_data('dpd', np.empty((n), dtype=np.float32))
    odat.add_data('mwd', np.empty((n), dtype=np.float32))
    odat.add_data('press', np.empty((n), dtype=np.float32))
    odat.add_data('atmp', np.empty((n), dtype=np.float32))
    odat.add_data('wtmp', np.empty((n), dtype=np.float32))
    odat.add_data('dewp', np.empty((n), dtype=np.float32))
    odat.add_data('tide', np.empty((n), dtype=np.float32))
    odat.add_data('vis', np.empty((n), dtype=np.float32))
    for idx, ln in enumerate(dat):
        tmp = np.array(ln.split(), dtype=np.float32)
        odat.mpltime[idx] = time.date2num(time.datetime(tmp[0],
                                                        tmp[1],
                                                        tmp[2],
                                                        tmp[3],
                                                        tmp[4],
                                                        0))
        odat.wdir[idx] = tmp[5]
        odat.wspd[idx] = tmp[6]
        odat.gst[idx] = tmp[7]
        odat.wvht[idx] = tmp[8]
        odat.dpd[idx] = tmp[9]
        odat.apd[idx] = tmp[10]
        odat.mwd[idx] = tmp[11]
        odat.press[idx] = tmp[12]
        odat.atmp[idx] = tmp[13]
        odat.wtmp[idx] = tmp[14]
        odat.dewp[idx] = tmp[15]
        odat.vis[idx] = tmp[16]
        odat.tide[idx] = tmp[17]
    for nm in odat._data_groups['main']:
        dat = getattr(odat, nm)
        bad = (dat == 99) | (dat == 999)
        dat[bad] = np.NaN

    return odat

if __name__ == '__main__':
    bdat = readtxt('/home/lkilcher/data/pnnl/buoy/ptww1h2011.txt')
    bdat.save('/home/lkilcher/data/pnnl/buoy_ptww.h5')

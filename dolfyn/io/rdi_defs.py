import numpy as np

century = 2000
data_defs = {'number': ([], 'data_vars', 'uint32', ''),
             'rtc': ([7], 'sys', 'uint16', ''),
             'builtin_test_fail': ([], 'data_vars', 'bool', ''),
             'c_sound': ([], 'data_vars', 'float32', 'm/s'),
             'depth': ([], 'data_vars', 'float32', 'm'),
             'pitch': ([], 'data_vars', 'float32', 'deg'),
             'roll': ([], 'data_vars', 'float32', 'deg'),
             'heading': ([], 'data_vars', 'float32', 'deg'),
             'temp': ([], 'data_vars', 'float32', 'C'),
             'salinity': ([], 'data_vars', 'float32', 'psu'),
             'min_preping_wait': ([], 'data_vars', 'float32', 's'),
             'heading_std': ([], 'data_vars', 'float32', 'deg'),
             'pitch_std': ([], 'data_vars', 'float32', 'deg'),
             'roll_std': ([], 'data_vars', 'float32', 'deg'),
             'adc': ([8], 'sys', 'uint8', ''),
             'error_status_wd': ([], 'attrs', 'float32', ''),
             'pressure': ([], 'data_vars', 'float32', 'dbar'),
             'pressure_std': ([], 'data_vars', 'float32', 'dbar'),
             'vel': (['nc', 4], 'data_vars', 'float32', 'm/s'),
             'amp': (['nc', 4], 'data_vars', 'uint8', 'counts'),
             'corr': (['nc', 4], 'data_vars', 'uint8', 'counts'),
             'prcnt_gd': (['nc', 4], 'data_vars', 'uint8', '%'),
             'status': (['nc', 4], 'data_vars', 'float32', ''),
             'dist_bt': ([4], 'data_vars', 'float32', 'm'),
             'vel_bt': ([4], 'data_vars', 'float32', 'm/s'),
             'corr_bt': ([4], 'data_vars', 'uint8', 'counts'),
             'amp_bt': ([4], 'data_vars', 'uint8', 'counts'),
             'prcnt_gd_bt': ([4], 'data_vars', 'uint8', '%'),
             'time': ([], 'coords', 'float64', ''),
             'etime_gps': ([], 'coords', 'float64', ''),
             'elatitude_gps': ([], 'data_vars', 'float64', 'deg'),
             'elongitude_gps': ([], 'data_vars', 'float64', 'deg'),
             'time_gps': ([], 'coords', 'float64', ''),
             'latitude_gps': ([], 'data_vars', 'float64', 'deg'),
             'longitude_gps': ([], 'data_vars', 'float64', 'deg'),
             'speed_made_good': ([], 'data_vars', 'float64', 'm/s'),
             'direction_made_good': ([], 'data_vars', 'float64', 'deg'),
             'speed_over_ground': ([], 'data_vars', 'float64', 'm/s'),
             'direction_over_ground': ([], 'data_vars', 'float64', 'deg'),
             'ntime': ([], 'coords', 'float64', ''),
             'flags': ([], 'data_vars', 'float32', ''),
             }


def _get(dat, nm):
    grp = data_defs[nm][1]
    if grp is None:
        return dat[nm]
    else:
        return dat[grp][nm]


def _in_group(dat, nm):
    grp = data_defs[nm][1]
    if grp is None:
        return nm in dat
    else:
        return nm in dat[grp]


def _pop(dat, nm):
    grp = data_defs[nm][1]
    if grp is None:
        dat.pop(nm)
    else:
        dat[grp].pop(nm)


def _setd(dat, nm, val):
    grp = data_defs[nm][1]
    if grp is None:
        dat[nm] = val
    else:
        dat[grp][nm] = val


def _idata(dat, nm, sz):
    group = data_defs[nm][1]
    dtype = data_defs[nm][2]
    units = data_defs[nm][3]
    arr = np.empty(sz, dtype=dtype)
    if dtype.startswith('float'):
        arr[:] = np.NaN
    dat[group][nm] = arr
    dat['units'][nm] = units
    return dat


def _get_size(name, n=None, ncell=0):
    sz = list(data_defs[name][0])  # create a copy!
    if 'nc' in sz:
        sz.insert(sz.index('nc'), ncell)
        sz.remove('nc')
    if n is None:
        return tuple(sz)
    return tuple(sz + [n])


class _variable_setlist(set):
    def __iadd__(self, vals):
        if vals[0] not in self:
            self |= set(vals)
        return self


class _ensemble():
    n_avg = 1
    k = -1  # This is the counter for filling the ensemble object

    def __getitem__(self, nm):
        return getattr(self, nm)

    def __init__(self, navg, n_cells):
        if navg is None or navg == 0:
            navg = 1
        self.n_avg = navg
        for nm in data_defs:
            setattr(self, nm,
                    np.zeros(_get_size(nm, n=navg, ncell=n_cells),
                             dtype=data_defs[nm][2]))

    def clean_data(self,):
        self['vel'][self['vel'] == -32.768] = np.NaN

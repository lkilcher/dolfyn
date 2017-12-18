from struct import calcsize, Struct
import bitops as bo
import numpy as np

grav = 9.81
# The starting value for the checksum:
cs0 = int('0xb58c', 0)


def nans(*args, **kwargs):
    out = np.empty(*args, **kwargs)
    if out.dtype.kind == 'f':
        out[:] = np.NaN
    else:
        out[:] = 0
    return out


class BadCheckSum(Exception):
    pass


class DataDef(object):

    def __init__(self, list_of_defs):
        self._names = []
        self._format = []
        self._shape = []
        self._N = []
        for itm in list_of_defs:
            self._names.append(itm[0])
            self._format.append(itm[1])
            if len(itm) <= 2:
                self._shape.append([])
                self._N.append(1)
            else:
                try:
                    self._shape.append(list(itm[2]))
                except TypeError:
                    self._shape.append([itm[2]])
                self._N.append(np.prod(itm[2]))
        self._struct = Struct('<' + self.format)
        self.nbyte = calcsize(self.format)
        self._cs_struct = Struct('<' + '{}H'.format(self.nbyte // 2))

    def init_data(self, npings):
        out = {}
        for nm, fmt, shp in zip(self._names, self._format, self._shape):
            out[nm] = nans(shp + [npings], dtype=np.dtype(fmt))
        return out

    def read_into(self, fobj, data, ens, cs=None):
        dat_tuple = self.read(fobj, cs=cs)
        for nm, d in zip(self._names, dat_tuple):
            data[nm][..., ens] = d

    @property
    def format(self, ):
        out = ''
        for f, n in zip(self._format, self._N):
            if n >= 1:
                out += '{}'.format(n)
            out += f
        return out

    def read(self, fobj, cs=None):
        bytes = fobj.read(self.nbyte)
        if len(bytes) != self.nbyte:
            raise IOError("End of file.")
        data = self._struct.unpack(bytes)
        if cs is not None:
            if cs is True:
                # if cs is True, then it should be the last value that
                # was read.
                csval = data[-1]
                off = cs0 - csval
            elif isinstance(cs, int):
                csval = cs
                off = cs0
            cs_res = sum(self._cs_struct.unpack(bytes)) + off
            if csval is not False and (cs_res % 65536) != csval:
                raise BadCheckSum('Checksum failed!')
        out = []
        c = 0
        for idx, n in enumerate(self._N):
            if n == 1:
                out.append(data[c])
            else:
                out.append(data[c:(c + n)])
            c += n
        return out

    def read2dict(self, fobj, cs=False):
        return {self._names[idx]: dat
                for idx, dat in enumerate(self.read(fobj, cs=cs))}


_header = DataDef([
    ('sync', 'B'),
    ('hsz', 'B'),
    ('id', 'B'),
    ('fam', 'B'),
    ('sz', 'H'),
    ('cs', 'H'),
    ('hcs', 'H'),
])

_burst_hdr = DataDef([
    ('ver', 'B'),
    ('DatOffset', 'B'),
    ('config', 'H'),
    ('SerialNum', 'I'),
    ('year', 'B'),
    ('month', 'B'),
    ('day', 'B'),
    ('hour', 'B'),
    ('minute', 'B'),
    ('second', 'B'),
    ('usec', 'H'),
    ('c_sound', 'H'),
    ('temp', 'H'),
    ('press', 'I'),
    ('heading', 'H'),
    ('pitch', 'H'),
    ('roll', 'H'),
    ('beam_config', 'H'),
    ('cell_size', 'H'),
    ('blanking', 'H'),
    ('nom_corr', 'B', ),
    ('press_temp', 'B'),
    ('batt_V', 'H'),
    ('Mag', 'h', 3),
    ('Acc', 'h', 3),
    ('ambig_vel', 'h'),
    ('data_desc', 'H'),
    ('xmit_energy', 'H'),
    ('vel_scale', 'b'),
    ('power_level', 'b'),
    ('mag_temp', 'h'),
    ('clock_temp', 'h'),
    ('error', 'H'),
    ('status0', 'H'),
    ('status', 'I'),
    ('ensemble', 'I')
])


def calc_burst_struct(config, nb, nc):
    cb = bo.i16ba(config)[::-1]
    flags = {}
    for idx, nm in enumerate([
            'press', 'temp', 'compass', 'tilt',
            None, 'vel', 'amp', 'corr',
            'alt', 'alt_raw', 'ast', 'echo',
            'ahrs', 'p_gd', 'std', None]):
        flags[nm] = cb[idx]
    dd = []
    if flags['vel']:
        dd.append(('vel', 'h', (nb, nc)))
    if flags['amp']:
        dd.append(('amp', 'B', (nb, nc)))
    if flags['corr']:
        dd.append(('corr', 'B', (nb, nc)))
    if flags['alt']:
        # There may be a problem here with reading 32bit floats if
        # nb and nc are odd?
        dd += [('alt_dist', 'f'),
               ('alt_quality', 'H'),
               ('alt_status', 'H')]
    if flags['ast']:
        dd += [('ast_dist', 'f'),
               ('ast_quality', 'H'),
               ('ast_offset_time', 'h'),
               ('ast_pressure', 'f'),
               # This use of 'x' here is a hack
               ('alt_spare', 'B7x')]
    if flags['alt_raw']:
        dd += [('altraw_nsamp', 'L'),
               ('altraw_dist', 'H'),
               ('altraw_samp', 'h')]
    if flags['echo']:
        dd += [('echo', 'H', nc)]
    if flags['ahrs']:
        dd += [('orientmat', 'f', (3, 3)),
               # This use of 'x' here is a hack
               ('ahrs_spare', 'B15x'),
               ('ahrs_gyro', 'f', 3)]
    if flags['p_gd']:
        dd += [('percent_good', 'B', nc)]
    if flags['std']:
        dd += [('std_pitch', 'h'),
               ('std_roll', 'h'),
               ('std_heading', 'h'),
               ('std_press', 'h'),
               # This use of 'x' here is a hack
               ('std_spare', 'H22x')]
    return DataDef(dd)

"""
Note on "This use of 'x' is a hack": I'm afraid that using a larger
int size will give syncing problems (e.g. unpack('HB')
vs. unpack('BH')), and I need to read SOMETHING otherwise, the
unpack order will get messed up. In the future, it'd be good to read
the size of the format, and hold that differently than self._N
(e.g. self._N2?)
"""

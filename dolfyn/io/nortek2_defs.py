from struct import calcsize, Struct
import bitops as bo

grav = 9.81


class DataDef(object):

    def __init__(self, list_of_defs):
        self._names = []
        self._format = []
        self._N = []
        for itm in list_of_defs:
            self._names.append(itm[0])
            self._format.append(itm[1])
            if len(itm) <= 2:
                self._N.append(1)
            else:
                self._N.append(itm[2])
        self._struct = Struct('<' + self.format)
        self.nbyte = calcsize(self.format)

    @property
    def format(self, ):
        out = ''
        for f, n in zip(self._format, self._N):
            if n >= 1:
                out += '{}'.format(n)
            out += f
        return out

    def read(self, fobj):
        bytes = fobj.read(self.nbyte)
        if len(bytes) != self.nbyte:
            raise IOError("End of file.")
        data = self._struct.unpack(bytes)
        out = []
        c = 0
        for idx, n in enumerate(self._N):
            if n == 1:
                out.append(data[c])
            else:
                out.append(data[c:(c + n)])
            c += n
        return out

    def read2dict(self, fobj):
        return {self._names[idx]: dat
                for idx, dat in enumerate(self.read(fobj))}


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
    ('MagX', 'h'),
    ('MagY', 'h'),
    ('MagZ', 'h'),
    ('AccX', 'h'),
    ('AccY', 'h'),
    ('AccZ', 'h'),
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
        dd.append(('vel', 'h', nb * nc))
    if flags['amp']:
        dd.append(('amp', 'B', nb * nc))
    if flags['corr']:
        dd.append(('corr', 'B', nb * nc))
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
        dd += [('orientmat', 'f', 9),
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

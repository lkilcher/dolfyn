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
            if len(itm[1]) == 1:
                self._N.append(1)
            else:
                self._N.append(int(itm[1][:-1]))
        self._struct = Struct('<' + self.format)

    @property
    def format(self, ):
        out = ''
        for f in self._format:
            out += f
        return out

    @property
    def nbyte(self, ):
        return calcsize(self.format)

    def read(self, fobj):
        bytes = fobj.read(self.nbyte)
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
    dd = DataDef([
        ('vel', '{}h'.format(nb * nc)),
    ])
    return dd

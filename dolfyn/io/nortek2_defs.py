import numpy as np
from copy import copy
from struct import Struct
from . import nortek2_lib as lib

dt32 = 'float32'
dt64 = 'float64'

grav = 9.81
# The starting value for the checksum:
cs0 = int('0xb58c', 0)


def _nans(*args, **kwargs):
    out = np.empty(*args, **kwargs)
    if out.dtype.kind == 'f':
        out[:] = np.NaN
    else:
        out[:] = 0
    return out


def _format(form, N):
    out = ''
    for f, n in zip(form, N):
        if n > 1:
            out += '{}'.format(n)
        out += f
    return out


class _DataDef():
    def __init__(self, list_of_defs):
        self._names = []
        self._format = []
        self._shape = []
        self._sci_func = []
        self._units = []
        self.long_name = []
        self.standard_name = []
        self._N = []
        for itm in list_of_defs:
            self._names.append(itm[0])
            self._format.append(itm[1])
            self._shape.append(itm[2])
            self._sci_func.append(itm[3])
            if len(itm) >= 5:
                self._units.append(itm[4])
            else:
                self._units.append('1')
            if len(itm) > 5:
                self.long_name.append(itm[5])
                self.standard_name.append(itm[6])
            else:
                self.long_name.append('')
                self.standard_name.append('')
            if itm[2] == []:
                self._N.append(1)
            else:
                self._N.append(int(np.prod(itm[2])))
        self._struct = Struct('<' + self.format)
        self.nbyte = self._struct.size
        self._cs_struct = Struct('<' + '{}H'.format(int(self.nbyte // 2)))

    def init_data(self, npings):
        out = {}
        for nm, fmt, shp in zip(self._names, self._format, self._shape):
            # fmt[0] uses only the first format specifier
            # (ie, skip '15x' in 'B15x')
            out[nm] = _nans(shp + [npings], dtype=np.dtype(fmt[0]))
        return out

    def read_into(self, fobj, data, ens, cs=None):
        dat_tuple = self.read(fobj, cs=cs)
        for nm, shp, d in zip(self._names, self._shape, dat_tuple):
            try:
                data[nm][..., ens] = d
            except ValueError:
                data[nm][..., ens] = np.asarray(d).reshape(shp)

    @property
    def format(self, ):
        return _format(self._format, self._N)

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
                raise Exception('Checksum failed!')
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

    def sci_data(self, data):
        for ky, func in zip(self._names,
                            self._sci_func):
            if func is None:
                continue
            data[ky] = func(data[ky])

    def data_units(self):
        units = {}
        for ky, unit in zip(self._names, self._units):
            units[ky] = unit
        return units

    def data_longnames(self):
        lngnms = {}
        for ky, unit in zip(self._names, self.long_name):
            lngnms[ky] = unit
        return lngnms

    def data_stdnames(self):
        stdnms = {}
        for ky, unit in zip(self._names, self.standard_name):
            stdnms[ky] = unit
        return stdnms


class _LinFunc():
    """A simple linear offset and scaling object.

    Usage:
       scale_func = _LinFunc(scale=3, offset=5)

       new_data = scale_func(old_data)

    This will do:
       new_data = (old_data + 5) * 3
    """

    def __init__(self, scale=1, offset=0, dtype=None):
        self.scale = scale
        self.offset = offset
        self.dtype = dtype

    def __call__(self, array):
        if self.scale != 1 or self.offset != 0:
            array = (array + self.offset) * self.scale
        if self.dtype is not None:
            array = array.astype(self.dtype)
        return array


header = _DataDef([
    ('sync', 'B', [], None),
    ('hsz', 'B', [], None),
    ('id', 'B', [], None),
    ('fam', 'B', [], None),
    ('sz', 'H', [], None),
    ('cs', 'H', [], None),
    ('hcs', 'H', [], None),
])

_burst_hdr = [
    ('ver', 'B', [], None),
    ('DatOffset', 'B', [], None),
    ('config', 'H', [], None),
    ('SerialNum', 'I', [], None),
    ('year', 'B', [], None),
    ('month', 'B', [], None),
    ('day', 'B', [], None),
    ('hour', 'B', [], None),
    ('minute', 'B', [], None),
    ('second', 'B', [], None),
    ('usec100', 'H', [], None),
    ('c_sound', 'H', [], _LinFunc(0.1, dtype=dt32), 'm s-1',
     'Speed of Sound', 'speed_of_sound_in_sea_water'),
    ('temp', 'H', [], _LinFunc(0.01, dtype=dt32),
     'degree_C', 'Temperature', 'sea_water_temperature'),
    ('pressure', 'I', [], _LinFunc(0.001, dtype=dt32),
     'dbar', 'Pressure', 'sea_water_pressure'),
    ('heading', 'H', [], _LinFunc(0.01, dtype=dt32),
     'deg', 'Heading', 'platform_orientation'),
    ('pitch', 'h', [], _LinFunc(0.01, dtype=dt32), 'deg', 'Pitch', 'platform_pitch'),
    ('roll', 'h', [], _LinFunc(0.01, dtype=dt32), 'deg', 'Roll', 'platform_roll'),
    ('beam_config', 'H', [], None),
    ('cell_size', 'H', [], _LinFunc(0.001), 'm'),
    ('blank_dist', 'H', [], _LinFunc(0.01), 'm'),
    ('nominal_corr', 'B', [], None, '%'),
    ('temp_press', 'B', [], _LinFunc(0.2, -20, dtype=dt32),
     'degree_C', 'Pressure Sensor Temperature', 'pressure_sensor_temperature'),
    ('batt', 'H', [], _LinFunc(0.1, dtype=dt32),
     'V', 'Battery Voltage', 'battery_voltage'),
    ('mag', 'h', [3], _LinFunc(0.1, dtype=dt32),
     'uT', 'Compass', 'magnetic_field_vector'),
    ('accel', 'h', [3], _LinFunc(1. / 16384 * grav, dtype=dt32),
     'm s-2', 'Acceleration', 'platform_acceleration'),
    ('ambig_vel', 'h', [], _LinFunc(0.001, dtype=dt32), 'm s-1'),
    ('data_desc', 'H', [], None),
    ('xmit_energy', 'H', [], None, 'dB', 'Transmit Energy',
     'sound_pressure_level_of_acoustic_signal'),
    ('vel_scale', 'b', [], None),
    ('power_level_dB', 'b', [], _LinFunc(dtype=dt32), 'dB'),
    ('temp_mag', 'h', [], None),  # uncalibrated
    ('temp_clock', 'h', [], _LinFunc(0.01, dtype=dt32),
     'degree_C', 'Internal Clock Temperature', 'internal_clock_temperature'),
    ('error', 'H', [], None),
    ('status0', 'H', [], None),
    ('status', 'I', [], None),
    ('_ensemble', 'I', [], None),
]

_bt_hdr = [
    ('ver', 'B', [], None),
    ('DatOffset', 'B', [], None),
    ('config', 'H', [], None),
    ('SerialNum', 'I', [], None),
    ('year', 'B', [], None),
    ('month', 'B', [], None),
    ('day', 'B', [], None),
    ('hour', 'B', [], None),
    ('minute', 'B', [], None),
    ('second', 'B', [], None),
    ('usec100', 'H', [], None),
    ('c_sound', 'H', [], _LinFunc(0.1, dtype=dt32), 'm s-1',
     'Speed of Sound', 'speed_of_sound_in_sea_water'),
    ('temp', 'H', [], _LinFunc(0.01, dtype=dt32),
     'degree_C', 'Temperature', 'sea_water_temperature'),
    ('pressure', 'I', [], _LinFunc(0.001, dtype=dt32),
     'dbar', 'Pressure', 'sea_water_pressure'),
    ('heading', 'H', [], _LinFunc(0.01, dtype=dt32),
     'deg', 'Heading', 'platform_orientation'),
    ('pitch', 'h', [], _LinFunc(0.01, dtype=dt32), 'deg', 'Pitch', 'platform_pitch'),
    ('roll', 'h', [], _LinFunc(0.01, dtype=dt32), 'deg', 'Roll', 'platform_roll'),
    ('beam_config', 'H', [], None),
    ('cell_size', 'H', [], _LinFunc(0.001), 'm'),
    ('blank_dist', 'H', [], _LinFunc(0.01), 'm'),
    ('nominal_corr', 'B', [], None, '%'),
    ('unused', 'B', [], None),
    ('batt', 'H', [], _LinFunc(0.1, dtype=dt32),
     'V', 'Battery Voltage', 'battery_voltage'),
    ('mag', 'h', [3], None,
     'gauss', 'Compass', 'magnetic_field_vector'),
    ('accel', 'h', [3], _LinFunc(1. / 16384 * grav, dtype=dt32),
     'm s-2', 'Acceleration', 'platform_acceleration'),
    ('ambig_vel', 'I', [], _LinFunc(0.001, dtype=dt32), 'm s-1'),
    ('data_desc', 'H', [], None),
    ('xmit_energy', 'H', [], None, 'dB'),
    ('vel_scale', 'b', [], None),
    ('power_level_dB', 'b', [], _LinFunc(dtype=dt32)),
    ('temp_mag', 'h', [], None),  # uncalibrated
    ('temp_clock', 'h', [], _LinFunc(0.01, dtype=dt32),
     'degree_C', 'Internal Clock Temperature', 'internal_clock_temperature'),
    ('error', 'I', [], None),
    ('status', 'I', [], None, 'binary'),
    ('_ensemble', 'I', [], None),
]

_ahrs_def = [
    ('orientmat', 'f', [3, 3], None, '1', 'Orientation Matrix',
     'earth_to_instrument_orientation_matrix'),
    ('quaternions', 'f', [4], None, '1',
     'Quaternions', 'platform_quaternion_vector'),
    ('angrt', 'f', [3], _LinFunc(np.pi / 180, dtype=dt32),
     'rad/s', 'Angular Velocity', 'platform_angular_velocity'),
]


def _calc_bt_struct(config, nb):
    flags = lib._headconfig_int2dict(config, mode='bt')
    dd = copy(_bt_hdr)
    if flags['vel']:
        # units handled in Ad2cpReader.sci_data
        dd.append(('vel', 'i', [nb], None, 'm s-1', 'Bottom Track Velocity',
                  'platform_velocity_from_bottom_track'))
    if flags['dist']:
        dd.append(('dist', 'i', [nb], _LinFunc(0.001, dtype=dt32), 'm',
                  'Bottom Track Depth', 'depth_below_platform'))
    if flags['fom']:
        dd.append(('fom', 'H', [nb], None, '1',
                  'Figure of Merit', 'figure_of_merit'))
    if flags['ahrs']:
        dd += _ahrs_def
    return _DataDef(dd)


def _calc_echo_struct(config, nc):
    flags = lib._headconfig_int2dict(config)
    dd = copy(_burst_hdr)
    dd[19] = ('blank_dist', 'H', [], _LinFunc(0.001))  # m
    if any([flags[nm] for nm in ['vel', 'amp', 'corr', 'alt', 'ast',
                                 'alt_raw', 'p_gd', 'std']]):
        raise Exception("Echosounder ping contains invalid data?")
    if flags['echo']:
        dd += [('echo', 'H', [nc], _LinFunc(0.01, dtype=dt32), 'dB', 'Echo Sounder',
               'echo_sounder_signal_intensity')]
    if flags['ahrs']:
        dd += _ahrs_def
    return _DataDef(dd)


def _calc_burst_struct(config, nb, nc):
    flags = lib._headconfig_int2dict(config)
    dd = copy(_burst_hdr)
    if flags['echo']:
        raise Exception("Echosounder data found in velocity ping?")
    if flags['vel']:
        dd.append(('vel', 'h', [nb, nc], None, 'm s-1', 'Water Velocity',
                  'velocity_from_multibeam_acoustic_doppler_velocity_profiler_in_sea_water'))
    if flags['amp']:
        dd.append(('amp', 'B', [nb, nc], _LinFunc(0.5, dtype=dt32), 'dB', 'Acoustic Signal Amplitude',
                  'signal_intensity_from_multibeam_acoustic_doppler_velocity_profiler_in_sea_water'))
    if flags['corr']:
        dd.append(('corr', 'B', [nb, nc], None, '%', 'Acoustic Signal Correlation',
                  'beam_consistency_indicator_from_multibeam_acoustic_doppler_velocity_profiler_in_sea_water'))
    if flags['alt']:
        # There may be a problem here with reading 32bit floats if
        # nb and nc are odd?
        dd += [('alt_dist', 'f', [], _LinFunc(dtype=dt32), 'm', 'Altimeter Range', 'altimeter_range'),
               ('alt_quality', 'H', [], _LinFunc(0.01, dtype=dt32), 'dB',
                'Altimeter Quality', 'altimeter_quality_indicator'),
               ('alt_status', 'H', [], None)]
    if flags['ast']:
        dd += [
            ('ast_dist', 'f', [], _LinFunc(dtype=dt32), 'm', 'AST Range',
             'acoustic_surface_tracking_range'),
            ('ast_quality', 'H', [], _LinFunc(0.01, dtype=dt32), 'dB',
             'AST Quality', 'acoustic_surface_tracking_quality_indicator'),
            ('ast_offset_time', 'h', [], _LinFunc(0.0001, dtype=dt32),
             's', 'AST Offset Time', 'time_offset_to_platform_time'),
            ('ast_pressure', 'f', [], None, 'dbar', 'AST Signal Intensity',
             'acoustic_surface_tracking_signal_intensity'),
            # This use of 'x' here is a hack
            ('ast_spare', 'B7x', [], None),
        ]
    if flags['alt_raw']:
        dd += [
            ('altraw_nsamp', 'I', [], None, '#',
             'Altimeter N Samples', 'altimeter_number_of_samples'),
            ('altraw_dsamp', 'H', [], _LinFunc(0.0001, dtype=dt32), 'm',
             'Altimeter Sample Distances', 'altimeter_distance_between_samples'),
            ('altraw_samp', 'h', [], None),
        ]
    if flags['ahrs']:
        dd += _ahrs_def
    if flags['p_gd']:
        dd += [('percent_good', 'B', [nc], None, '%', 'Percent Good',
                'proportion_of_acceptable_signal_returns_from_acoustic_instrument_in_sea_water')]
    if flags['std']:
        dd += [('pitch_std', 'h', [],
                _LinFunc(0.01, dtype=dt32), 'deg', 'Pitch Std', 'platform_pitch_standard_devation'),
               ('roll_std', 'h', [],
                _LinFunc(0.01, dtype=dt32), 'deg', 'Roll Std', 'platform_roll_standard_devation'),
               ('heading_std', 'h', [],
                _LinFunc(0.01, dtype=dt32), 'deg', 'Heading Std', 'platform_course_standard_devation'),
               ('press_std', 'h', [],
                _LinFunc(0.1, dtype=dt32), 'dbar', 'Pressure Std', 'sea_water_pressure_standard_devation'),
               # This use of 'x' here is a hack
               ('std_spare', 'H22x', [], None)]
    return _DataDef(dd)


"""
Note on "This use of 'x' is a hack": I'm afraid that using a larger
int size will give syncing problems (e.g. unpack('HB')
vs. unpack('BH')), and I need to read something, otherwise the
unpack order will get messed up. In the future, it'd be good to read
the size of the format, and hold that differently than self._N
(e.g. self._N2?)
"""

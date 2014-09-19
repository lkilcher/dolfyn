import base as adv
import os
from ..tools import misc as tbx
from ..data import time
import string
import numpy as np

alphs = set(string.ascii_letters).union(['(', ')', '%'])


def count_lines(fd):
    """
    !!! This function assumes each line has the same number of bytes!!!

    Counts the lines remaining in the file,
    and returns to the current position.

    """
    p1 = fd.tell()
    fd.readline()
    p2 = fd.tell()
    fd.seek(0, 2)
    pe = fd.tell()
    fd.seek(p1, 0)
    val = (pe - p1) / (p2 - p1)
    if val != int(val):
        raise ValueError('Number of lines is not an integer: \
                         perhaps the bytes / line is not constant?')
    return int(val)


def parseStr(x):
    if x == '0':
        return 0
    else:
        return (x.isalpha() and x or
                x.isdigit() and int(x) or
                x.isalnum() and x or
                (len(set(string.punctuation).intersection(x)) == 1 and
                 x.count('.') == 1 and float(x)) or
                x)


class header_reader(object):

    """
    This is incomplete.  It should eventually return an ADVconfig object...
    """
    section_names = ['User setup', 'Data file format', ]
    names = {}

    def readline(self,):
        while True:
            ln = self.fd.readline()
            pos = self.fd.tell()
            nxtln = self.fd.readline()
            while nxtln.startswith(' '):
                pos = self.fd.tell()
                ln += nxtln[self.col_ind:]
                nxtln = self.fd.readline()
            self.fd.seek(pos, 0)
            if (ln.startswith('---') or
                ln.strip('\r\n') in ['Head configuration',
                                     'Hardware configuration',
                                     'User setup']):
                continue
            elif ln == '':
                return None
            return ln.strip('\r\n')

    def parseline(self, ln):
        return [ln[:self.col_ind].strip(), ln[self.col_ind:], ]

    def read_dat(self,):
        pass

    def read_sen(self,):
        pass

    def read_vhd(self,):
        pass

    def read_pck(self,):
        pass

    def read(self,):
        ln = 'init'
        while ln != '':
            ln = self.readline()
            if ln is None:
                return self.out
            elif ln.endswith(r'.vec]'):
                self.read_setup()
            elif ln.endswith('.sen]'):
                self.read_sen()
            elif ln.endswith('.pck]'):
                self.read_pck()
            elif ln.endswith('.vhd]'):
                self.read_vhd()
            elif ln.endswith('.dat]'):
                self.read_dat()

    def parse_data(self, dt):
        if dt[0] == '':
            return
        elif dt[1].count('\n'):
            # Handle arrays.
            ndt = dt[1].split('\r\n')
            if alphs.intersection(ndt[0]):
                return dt
            for idx, nd in enumerate(ndt):
                ndt[idx] = nd.split()
            dt[1] = np.array(ndt, parseStr(ndt[0][0]).__class__)
        elif dt[1].count(' '):
            # Handle row vectors.
            ndt = dt[1].split()
            for idx, nd in enumerate(ndt):
                ndt[idx] = nd.replace(',', '')
            if alphs.intersection(dt[1]):
                return dt
            dt[1] = np.array(ndt, parseStr(ndt[0]).__class__)
        return dt

    def read_setup(self,):
        # Specify the format of some variables.
        # Others will be formed as *Name*.replace(' ','_').lower()
        format = {'Number of measurements': 'N_samp',
                  'Number of velocity checksum errors': 'N_err_vel',
                  'Number of sensor checksum errors': 'N_err_sens',
                  'Number of data gaps': 'N_gaps',
                  'Time of first measurement': 'Time_0',
                  'Time of last measurement': 'Time_end',
                  'Sampling rate': 'samp_rate',
                  }

        while True:
            ln = self.readline()
            if ln is None:
                return
            if ln == 'Data file format':
                return
            else:
                dt = self.parseline(ln)
                if dt[0] in format.keys():
                    dt[0] = format[dt[0]]
                else:
                    dt[0] = dt[0].replace(' ', '_').lower()
                dt = self.parse_data(dt)
                if dt is not None:
                    setattr(self.out, *dt)

    def __enter__(self,):
        return self

    def __init__(self, filename, col_ind=None):
        self.fd = open(filename, 'r')
        self.close = self.fd.close
        self.filename = filename
        self.out = adv.ADVconfig()
        if col_ind is None:
            self.find_colind()
        else:
            self.col_ind = col_ind

    def find_colind(self,):
        pos = self.fd.tell()
        self.fd.seek(0, 0)
        while True:
            ln = self.readline()
            if ln.startswith('Number of measurements'):
                a = ln.strip('Number of measurements')
                self.col_ind = ln.find(a)
                self.fd.seek(pos, 0)
                return

    def __exit__(self, type, value, trace,):
        self.close()


def read_sen(filename, advd):
    print("Reading sensor (time, etc.) file %s..." % filename)
    sr = advd.fs
    with open(filename, 'r') as fe:
        nlines = int(count_lines(fe))
        # prog_bar = dio.progress_bar(nlines, 40)
        for ind, ln in enumerate(fe):
            # prog_bar.increment()
            dt = ln.split()
            k = ind * sr
            advd.mpltime[k] = time.date2num(
                time.datetime(int(dt[2]),
                              int(dt[0]),
                              int(dt[1]),
                              int(dt[3]),
                              int(dt[4]),
                              int(dt[5]))
            )
            advd.heading[k] = float(dt[10])
            advd.pitch[k] = float(dt[11])
            advd.roll[k] = float(dt[12])
            advd.temp[k] = float(dt[13])
            if k + sr > advd.shape[-1]:
                break  # Exit when we get enough data.
    bd = advd.mpltime == 0
    advd.mpltime[bd] = np.nan
    advd.heading[bd] = np.nan
    advd.pitch[bd] = np.nan
    advd.roll[bd] = np.nan
    advd.temp[bd] = np.nan
    tbx.fillgaps(advd.mpltime)
    tbx.fillgaps(advd.heading)
    tbx.fillgaps(advd.pitch)
    tbx.fillgaps(advd.roll)
    tbx.fillgaps(advd.temp)

    return advd


def time_func(date, frmt):
    frmts = frmt.split(';')
    for frmt in frmts:
        try:
            return time.date2num(time.datetime.strptime(date, frmt))
        except:
            pass
    raise ValueError('No valid format in format specifier?')


def read_sontek_HorizonTab(filename,
                           dat_map=['ensemble',
                                    '_time:%m/%d/%Y %I:%M:%S %p;%m/%d/%Y',
                                    'u', 'v', 'w',
                                    'Amp1', 'Amp2', 'Amp3',
                                    'corr1', 'corr2', 'corr3',
                                    'SNR1', 'SNR2', 'SNR3', ],
                           dlm='\t'):
    """
    Read tabulated ascii data output by Sontek's HorizonADV software.
    """
    dat = read_dat(filename, dat_map, dlm)

    return dat


def read_sontek_winadv(filename,
                       dat_map=['mpltime',
                                None, None,
                                'u', 'v', 'w',
                                'corr1', 'corr2', 'corr3',
                                'SNR1', 'SNR2', 'SNR3',
                                'Amp1', 'Amp2', 'Amp3',
                                None, None, None],
                       dlm=';',
                       skip_n_headlines=9):
    dat = read_dat(filename, dat_map, dlm, skip_n_headlines=skip_n_headlines)
    return dat


def read_dat(filename,
             dat_map=['burst', 'ensemble',
                      'u', 'v', 'w',
                      'Amp1', 'Amp2', 'Amp3',
                      'SNR1', 'SNR2', 'SNR3',
                      'corr1', 'corr2', 'corr3',
                      'pressure'],
             dlm=' ',
             skip_n_headlines=0,
             cls=adv.ADVraw,
             nlines=None):
    """
    Read ADV ascii file *filename*, and return a ADVraw object
    containing the data.

    *dat_map* specifies the variable names of the columns of the file.

    """
    print("Reading adv ascii data file: %s..." % filename)
    with open(filename, 'r') as fu:
        k = 0
        if nlines is None:
            nlines = int(count_lines(fu))
        # prog_bar = dio.progress_bar(nlines, 40)
        advd = cls(nlines, dat_map)
        advd.add_data('mpltime', np.empty(
            nlines, dtype=np.float64), '_essential')
        bd_time = 0
        for i, ln in enumerate(fu):
            if i < skip_n_headlines:
                continue
            idx = i - skip_n_headlines
            if idx >= nlines:
                break
            # prog_bar.increment()
            if dlm == ' ':
                dt = ln.split()
            else:
                dt = ln.split(dlm)
            if len(dt) == 0:  # EOF?
                break
            for ind, nm in enumerate(dat_map):
                if nm is None:
                    continue
                # if not hasattr(advd,nm):

                if nm.__class__ in [str, unicode] and not nm.startswith('_'):
                    advd.__getattribute__(nm)[idx] = float(dt[ind])
                # is 'nm' a function?
                elif nm.__class__ is time_func.__class__:
                    args = [dt[ind]]
                    itmp = 1
                    while dat_map[ind + itmp].startswith('_'):
                        args.append(dt[ind + itmp])
                        itmp += 1
                    advd.__getattribute__(nm)[idx] = nm(*args)
                elif nm.startswith('_time:'):
                    try:
                        advd.mpltime[idx] = time_func(dt[ind], nm[6:])
                    except ValueError:
                        # See if it is only a date, presuming the
                        # format starts with date.
                        advd.mpltime[idx] = time_func(dt[ind], nm[6:15])
                    except ValueError:
                        bd_time += 1
                        break
            k += 1
    # What does this do?
    if k < len(advd.mpltime):
        for nm, dat in advd.iter():
            if nm.startswith('_time'):
                nm = 'mpltime'
            setattr(advd, nm, dat[..., :k])
    print('%d out of %d lines had bad time stamps' % (bd_time, k))
    return advd


def count_burst_lines(direc, sfx='.dat'):
    """
    Count the total number of lines in the files that end in *sfx* in
    directory *direc*.

    *sfx* defualts to '.dat'
    """
    fls = os.listdir(direc)
    n = 0
    for flnm in fls:
        if flnm.endswith(sfx):
            with open(direc + flnm, 'r') as fl:
                c = count_lines(fl)
                print('%d lines in %s' % (c, flnm))
                n += c
    return n

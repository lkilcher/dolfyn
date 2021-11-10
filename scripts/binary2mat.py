#!/usr/bin/python
import argparse
from dolfyn import read, save_mat

parser = argparse.ArgumentParser(
    description="Converts acoustic Doppler instrument data from binary"
    " format to Matlab(TM) (.mat).")

parser.add_argument('files',
                    help="The filename(s) to convert.",
                    action='append',
                    )

args = parser.parse_args()

for fnm in args.files:
    dat = read(fnm)

    if '.' in fnm:
        ext = fnm[fnm.index('.'):]
        
    outnm = fnm.rstrip(ext) + '.mat'
    print('Saving to %s.' % outnm)
    # Save the data.
    save_mat(dat, outnm, datenum=True)
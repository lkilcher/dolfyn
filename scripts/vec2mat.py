#!/usr/bin/python
import argparse
import dolfyn
import dolfyn.adv.api as avm

parser = argparse.ArgumentParser(
    description="Converts Nortek Vector .vec files from binary"
    " (.vec) format to Matlab(TM) (.mat).")

parser.add_argument('files',
                    help="The filename(s) to convert.",
                    action='append',
                    )

args = parser.parse_args()

for fnm in args.files:
    dat = avm.read(fnm)

    # Set matlab 'datenum' time.
    dt = dolfyn.time.epoch2date(dat['time'])
    dat['datenum'] = dolfyn.time.date2matlab(dt)

    outnm = fnm.rstrip('.vec').rstrip('.VEC') + '.mat'
    print('Saving to %s.' % outnm)
    # Save the data.
    dolfyn.io.api.save_mat(dat, outnm)

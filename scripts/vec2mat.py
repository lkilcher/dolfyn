#!/usr/bin/python
import argparse
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
    dat = avm.read.read_nortek(fnm)

    # Set matlab 'datenum' time.
    dat.add_data('datenum', dat.mpltime + 366., 'main')

    outnm = fnm.rstrip('.vec').rstrip('.VEC') + '.mat'
    print 'Saving to %s.' % outnm
    # Save the data.
    dat.save_mat(outnm,
                 groups=['main',
                         'orient',
                         'signal',
                         '#error',
                         '#env',
                         '#sys',
                         '#extra']
                 )

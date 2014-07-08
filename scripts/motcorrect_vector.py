#!/usr/bin/python
import argparse,os
import numpy as np
import dolfyn.adv.rotate as avr
import dolfyn.adv.api as avm

script_dir=os.path.dirname(__file__)

parser = argparse.ArgumentParser(description='Perform motion correction of a Nortek Vector (.vec) file and save the output as a Matlab(TM) (.mat) file.')
parser.add_argument('-f',
                    default=0.03333,
                    help="Specify the high-pass filter frequency that is applied to the acceleration \
                    prior to integrating acceleration (Accel) to get velocity. Default '0.03333' (Hz) \
                    = 30sec."
                    )

parser.add_argument('-F',
                    default=0.01,
                    help="Specify the high-pass filter frequency that is applied to the integrated \
                    acceleration (uacc) to remove drift that remains after integration. Default \
                    '0.01' (Hz) = 100sec"
                    )

parser.add_argument('-O',
                    default=None,
                    help=
                    """
                    Specify the 'orientation' configuration file (default: '<filename>.orient', or
                    'vector.orient', in that order). Cable-Head Vector probes the orientation of,
                    and distance between, the head to the body is arbitrary. This option specifies
                    the file which defines these variables. For more information on how to measure
                    these variables, consult the 'fixed_head.orient' file.
                    """
                    )
parser.add_argument('--fixed-head',action='store_true')
parser.add_argument('filename',help="The filename(s) of the the Nortek Vector file(s) to be processed (they probably end with '.vec').",action='append')

## parser.add_argument('-body2head',
##                     nargs=3,
##                     type=float,
##                     help="Specify the vector from the ADV-body to the ADV-head, in the ADV-body frame, in units of meters.",
##                     default=[0.0,0.0,0.4]
##                     )

## parser.add_argument('-body2head_rotmat',
##                     nargs=9,
##                     type=float,
##                     help="Specify the vector from the ADV-body to the ADV-head, in the ADV-body frame, in units of meters.",
##                     default=[0.0,0.0,0.4]
##                     )

args = parser.parse_args()

if bool(args.fixed_head) != bool(args.O):
    # Either args.fixed_head is True or args.O should be a string.
    if bool(args.O):
        execfile(args.O)
    else:
        execfile(script_dir+'/'+'fixed_head.orient')
else:
    raise Exception("You must either specify --fixed-head, or specify an 'orientation' config file.")

print VEC,ROTMAT
    

## if len(sys.argv)>1:
##     fname=sys.argv[1]
## else:
##     fname='HydroTurbSim.inp'

## config=readConfig(fname)

## tm0=time.time()
## tsdat=run(config)
## write(tsdat,config,fname)
## print 'TurbSim exited normally, runtime was %g seconds' % (time.time()-tm0)

#!/usr/bin/python
import argparse,os
import numpy as np
import dolfyn.adv.rotate as avr
import dolfyn.adv.api as avm

script_dir=os.path.dirname(__file__)

parser = argparse.ArgumentParser(description='Perform motion correction of a Nortek Vector (.vec) file and save the output as a Matlab(TM) (.mat) file.')
parser.add_argument(
    '-f',
    default=0.03333,
    help="""
    Specify the high-pass filter frequency that is applied to the acceleration
    prior to integrating acceleration (Accel) to get velocity. Default '0.03333' (Hz)
    = 30sec."""
    )
parser.add_argument(
    '-F',
    default=0.01,
    help="""
    Specify the high-pass filter frequency that is applied to the integrated
    acceleration (uacc) to remove drift that remains after integration. Default
    '0.01' (Hz) = 100sec
    """
    )
parser.add_argument(
    '-O',
    default=None,
    help="""
    Specify the 'orientation' configuration file (default: '<filename>.orient', or
    'vector.orient', in that order). Cable-Head Vector probes the orientation of,
    and distance between, the head to the body is arbitrary. This option specifies
    the file which defines these variables. For more information on how to measure
    these variables, consult the
    'dolfyn-src-dir/examples/motion_correct_example.orient'
    """
    )
parser.add_argument(
    '--fixed-head',
    action='store_true',
    help="""
    This specifies that the 'fixed-head' orientation/geometry should be used to
    compute head motion.
    """
    )
parser.add_argument(
    'filename',
    help="The filename(s) of the the Nortek Vector file(s) to be processed (they probably end with '.vec').",
    action='append'
    )

args = parser.parse_args()

if bool(args.fixed_head) != bool(args.O):
    # Either args.fixed_head is True or args.O should be a string.
    if bool(args.O):
        exec( open(args.O).read() ) # ROTMAT and VEC should be in this file.
        rmat = np.array(ROTMAT)
        vec = np.array(VEC)
        del VEC,ROTMAT
    else:
        rmat = np.array([[1,0,0],
                         [0,1,0],
                         [0,0,1]],dtype=np.float32)
        vec = np.array([0, 0, 0.21]) # in meters
else:
    raise Exception("You must either specify --fixed-head, or specify an 'orientation' config file.")

# Instantiate the 'motion correction' object.
mc = avr.correct_motion(accel_filtfreq=args.f,vel_filtfreq=args.F)

# Now loop over the specified file names:
for fnm in args.filename:
    
    dat = avm.read.read_nortek(fnm)

    # Set the geometry
    dat.props['body2head_rotmat']=rmat
    dat.props['body2head_vec']=vec
    # Set matlab 'datenum' time.
    dat.add_data('datenum',dat.mpltime+366.,'main')

    # Perform motion correction.
    if hasattr(dat,'orientmat'):
        print( 'Performing motion correction...' )
        mc(dat) # Perform the motion correction.
        # Compute pitch,roll,heading from orientmat.
        dat.pitch[:],dat.roll[:],dat.heading[:]=avr.orient2euler(dat.orientmat)
    else:
        print( "!!!--Warning--!!! : Orientation matrix ('orientmat') not found. Motion correction cannot be performed on this file" )

    outnm=fnm.rstrip('.vec').rstrip('.VEC')+'.mat'
    print( 'Saving corrected data to %s.' % outnm )
    # Save the data.
    dat.save_mat(outnm,groups=['main','orient'])
    
    del dat

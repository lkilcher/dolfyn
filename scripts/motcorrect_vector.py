#!python

import argparse
import os
import numpy as np
from dolfyn.adv.rotate import orient2euler
import dolfyn.adv.api as avm
from dolfyn.adv.motion import correct_motion

# TODO: add option to rotate into earth or principal frame (include
# principal_angle_True in output).

script_dir = os.path.dirname(__file__)

parser = argparse.ArgumentParser(
    description="""
    Perform motion correction of a Nortek Vector(.vec)
    file and save the output in earth(u: East, v: North, w: up)
    coordinates in units of m / s as a Matlab(TM)(.mat) file.
    """)
parser.add_argument(
    '-f',
    default=0.03333,
    help="""
    Specify the high-pass filter frequency that is applied to the
    acceleration prior to integrating acceleration (Accel) to get
    velocity. Default '0.03333' (Hz) = 30sec.
    """
)

## parser.add_argument(
##     '-F',
##     default=0.01,
##     help="""
##     Specify the high-pass filter frequency that is applied to the integrated
##     acceleration (uacc) to remove drift that remains after integration. Default
##     '0.01' (Hz) = 100sec
##     """
## )

parser.add_argument(
    '-O',
    default=None,
    help="""NOTE: this option is deprecated and will be removed in
    future releases. Use the '<filename>.userdata.json' method
    instead.  Specify the 'orientation' configuration file (default:
    '<filename>.orient', or 'vector.orient', in that
    order). Cable-Head Vector probes the orientation of, and distance
    between, the head to the body is arbitrary. This option specifies
    the file which defines these variables. For more information on
    how to measure these variables, take a look at the
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
    '--mat',
    action='store_true',
    help="""
    Save the earth-frame motion-corrected data in Matlab format (default).
    """
)
## parser.add_argument(
##     '--csv',
##     action='store_true',
##     help="""
##     Save the earth-frame motion-corrected data in csv (comma-separated value) format.
##     """
## )
parser.add_argument(
    '--hdf5',
    action='store_true',
    help="""
    Save the earth-frame motion-corrected data in the dolfyn-structured hdf5 format.
    """
)

## parser.add_argument(
##     '--out-earth',
##     action='store_true',
##     help="""
##     This specifies that the output data should be return in an earth
##     (u:East, v:North, w:up) coordinate system (default: True).
##     """
## )

###########
# I removed this option because the data in a raw file is often
# noisey, which will lead to inaccurate estimates of the principal
# angle. Data should be cleaned prior to rotating into the principal
# frame.
## parser.add_argument(
##     '--out-principal',
##     action='store_false',
##     help="""
##     This specifies that the output data should be returned in a
##     'principal axes' frame (u:streamwise, v:cross-stream, w:up)
##     coordinate system.
##     """
##     )
parser.add_argument(
    'filename',
    help="""The filename(s) of the the Nortek Vector file(s) to be
    processed(they probably end with '.vec').""",
    action='append'
)

args = parser.parse_args()

## if bool(args.out_principal) and bool(args.out_earth):
# raise Exception('--out-principal and --out-earth can not both be
# selected. You must choose one output frame.')
declin = None
if args.fixed_head != bool(args.O):
    # Either args.fixed_head is True or args.O should be a string.
    if bool(args.O):
        exec(open(args.O).read())  # ROTMAT and VEC should be in this file.
        rmat = np.array(ROTMAT)
        vec = np.array(VEC)
        if 'DECLINATION' in vars():
            declin = DECLINATION
        del VEC, ROTMAT
    else:
        rmat = np.array([[1, 0, 0],
                         [0, 1, 0],
                         [0, 0, 1]], dtype=np.float32)
        vec = np.array([0, 0, -0.21])  # in meters
else:
    rmat = None
    vec = None

if not (args.mat or args.hdf5):
    args.mat = True

# Now loop over the specified file names:
for fnm in args.filename:

    dat = avm.read_nortek(fnm)

    if rmat is not None:
        dat.props['body2head_rotmat'] = rmat
    if vec is not None:
        dat.props['body2head_vec'] = vec
    if declin is not None:
        dat.props['declination'] = declin
    if ('body2head_rotmat' not in dat.props or
            'body2head_vec' not in dat.props):
        raise Exception("body2head_rotmat or body2head_vec not found "
                        "in dat.props. These must be specified by either:\n"
                        "  1) defining them in a '.userdata.json' file\n"
                        "  2) using the --fixed-head command-line argument\n"
                        "  3) specifying them in a '.orient' file "
                        "(will be deprecated).")

        # Set matlab 'datenum' time.
        dat.add_data('datenum', dat.mpltime.matlab_datenum, 'main')

    # Perform motion correction.
    if hasattr(dat, 'orientmat'):
        print('Performing motion correction...')
        correct_motion(dat, accel_filtfreq=args.f)  # Perform the motion correction.
        # Compute pitch,roll,heading from orientmat.
        dat.pitch[:], dat.roll[:], dat.heading[:] = orient2euler(dat.orientmat)
    else:
        print("""
        !!!--Warning--!!!: Orientation matrix('orientmat')
        not found. Motion correction cannot be performed on this file
        """)

    if args.mat:
        outnm = fnm.rstrip('.vec').rstrip('.VEC') + '.mat'
        print('Saving to %s.' % outnm)
        # Save the data.
        dat.save_mat(outnm, groups=['main', 'orient'])

    if args.hdf5:
        outnm = fnm.rstrip('.vec').rstrip('.VEC') + '.hdf5'
        print('Saving to %s.' % outnm)
        # Save the data.
        dat.save(outnm,)

    del dat

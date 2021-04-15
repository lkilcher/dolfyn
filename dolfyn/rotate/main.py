from . import x_vector as r_vec
from . import x_awac as r_awac
from . import x_signature as r_sig
from . import x_rdi as r_rdi
import numpy as np
import warnings


# The 'rotation chain'
rc = ['beam', 'inst', 'earth', 'principal']

rot_module_dict = {
    # Nortek instruments
    'vector': r_vec,
    'awac': r_awac,
    'signature': r_sig,
    'ad2cp': r_sig,

    # RDI instruments
    'rdi': r_rdi}


def rotate2(ds, out_frame='earth', inplace=False):
    """Rotate a data dsect to a new coordinate system.

    Parameters
    ----------

    ds : :class:`~dolfyn.Veldata`
      The dolfyn Veldata-data (ADV or ADP) dsect to rotate.

    out_frame : string {'beam', 'inst', 'earth', 'principal'}
      The coordinate system to rotate the data into.

    inplace : bool
      Operate on the input data dsect (True), or return a copy that
      has been rotated (False, default).

    Returns
    -------
    dsout : :class:`~dolfyn.Veldata`
      The rotated data dsect. Note that when ``inplace=True``, the
      input dsect is modified in-place *and* returned (i.e.,
      ``dsout`` is ``ds``).

    Notes
    -----

    This function rotates all variables in ``ds.props['rotate_vars']``.

    """
    csin = ds.coord_sys.lower()
    if csin == 'ship':
        csin = 'inst'

    # Returns True/False if head2inst_rotmat has been set/not-set.
    # Bad configs raises errors (this is to check for those)
    r_vec._check_inst2head_rotmat(ds)

    if out_frame == 'principal' and csin != 'earth':
        warnings.warn(
            "You are attempting to rotate into the 'principal' "
            "coordinate system, but the data dsect is in the {} "
            "coordinate system. Be sure that 'principal_angle' is "
            "defined based on the earth coordinate system." .format(csin))

    rmod = None
    for ky in rot_module_dict:
        if ky in ds.Veldata._make_model:
            rmod = rot_module_dict[ky]
            break
    if rmod is None:
        raise ValueError("Rotations are not defined for "
                         "instrument '{}'.".format(ds.Veldata._make_model))
    if not inplace:
        ds = ds.copy()

    # Get the 'indices' of the rotation chain
    try:
        iframe_in = rc.index(csin)
    except ValueError:
        raise Exception("The coordinate system of the input "
                        "data dsect, '{}', is invalid."
                        .format(ds.coord_sys))
    try:
        iframe_out = rc.index(out_frame.lower())
    except ValueError:
        raise Exception("The specifid output coordinate system "
                        "is invalid, please select one of: 'beam', 'inst', "
                        "'earth', 'principal'.")

    if iframe_out == iframe_in:
        # Should this generate an error?
        return ds

    if iframe_out > iframe_in:
        reverse = False
    else:
        reverse = True

    while ds.coord_sys.lower() != out_frame.lower():
        csin = ds.coord_sys
        if csin == 'ship':
            csin = 'inst'
        inow = rc.index(csin)
        if reverse:
            func = getattr(rmod, rc[inow - 1] + '2' + rc[inow])
        else:
            func = getattr(rmod, rc[inow] + '2' + rc[inow + 1])
        ds = func(ds, reverse=reverse)

    return ds


def calc_principal_heading(vel, tidal_mode=True):
    """
    Compute the principal angle of the horizontal velocity.

    Parameters
    ----------
    vel : np.ndarray (2,...,Nt), or (3,...,Nt)
      The 2D or 3D Veldata array (3rd-dim is ignored in this calculation)

    tidal_mode : bool (default: True)

    Returns
    -------
    p_heading : float or ndarray
      The principal heading(s) in degrees clockwise from North.

    Notes
    -----

    The tidal mode follows these steps:
      1. rotates vectors with negative v by 180 degrees
      2. then doubles those angles to make a complete circle again
      3. computes a mean direction from this, and halves that angle again.
      4. The returned angle is forced to be between 0 and 180. So, you
         may need to add 180 to this if you want your positive
         direction to be in the western-half of the plane.

    Otherwise, this function simply compute the average direction
    using a vector method.

    """
    dt = vel[0] + vel[1] * 1j
    if tidal_mode:
        # Flip all vectors that are below the x-axis
        dt[dt.imag <= 0] *= -1
        # Now double the angle, so that angles near pi and 0 get averaged
        # together correctly:
        dt *= np.exp(1j * np.angle(dt))
        dt = np.ma.masked_invalid(dt)
        # Divide the angle by 2 to remove the doubling done on the previous
        # line.
        pang = np.angle(
            np.mean(dt, -1, dtype=np.complex128)) / 2
    else:
        pang = np.angle(np.mean(dt, -1))
    return (90 - np.rad2deg(pang))

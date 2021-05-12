from . import vector as r_vec
from . import awac as r_awac
from . import signature as r_sig
from . import rdi as r_rdi
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
    """
    Rotate a dataset to a new coordinate system.

    Parameters
    ----------
    ds : xr.Dataset
      The dolfyn dataset (ADV or ADCP) to rotate.

    out_frame : string {'beam', 'inst', 'earth', 'principal'}
      The coordinate system to rotate the data into.

    inplace : bool
      Operate on the input data dataset (True), or return a copy that
      has been rotated (False, default).

    Returns
    -------
    ds_out : |xr.Dataset|
      The rotated dataset
      
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
        ds = ds.copy(deep=True)

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

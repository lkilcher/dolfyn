from . import vector as r_vec
from . import awac as r_awac
from . import signature as r_sig
from . import rdi as r_rdi
import warnings

# The 'rotation chain'
rc = ['beam', 'inst', 'earth', 'principal']

rot_module_dict = {
    # Nortek instruments
    'nortek vector': r_vec,
    'nortek awac': r_awac,
    'nortek signature': r_sig,

    # RDI instruments
    'rdi': r_rdi,
}


def rotate2(obj, out_frame='earth', inplace=False):
    """Rotate a data object to a new coordinate system.

    Parameters
    ----------

    obj : :class:`~dolfyn.Velocity`
      The dolfyn velocity-data (ADV or ADP) object to rotate.

    out_frame : string {'beam', 'inst', 'earth', 'principal'}
      The coordinate system to rotate the data into.

    inplace : bool
      Operate on the input data object (True), or return a copy that
      has been rotated (False, default).

    Returns
    -------
    objout : :class:`~dolfyn.Velocity`
      The rotated data object. Note that when ``inplace=True``, the
      input object is modified in-place *and* returned (i.e.,
      ``objout`` is ``obj``).

    Notes
    -----

    This function rotates all variables in ``obj.props['rotate_vars']``.

    """
    csin = obj.props['coord_sys'].lower()
    if csin == 'ship':
        csin = 'inst'

    if out_frame == 'principal' and csin != 'earth':
        warnings.warn(
            "You are attempting to rotate into the 'principal' "
            "coordinate system, but the data object is in the {} "
            "coordinate system. Be sure that 'principal_angle' is "
            "defined based on the earth coordinate system.")

    rmod = None
    for ky in rot_module_dict:
        if obj._make_model.startswith(ky):
            rmod = rot_module_dict[ky]
            break
    if rmod is None:
        raise ValueError("Rotations are not defined for "
                         "instrument '{}'.".format(obj._make_model))
    if not inplace:
        obj = obj.copy()

    # Get the 'indices' of the rotation chain
    try:
        iframe_in = rc.index(csin)
    except ValueError:
        raise Exception("The coordinate system of the input "
                        "data object, '{}', is invalid."
                        .format(obj.props['coord_sys']))
    try:
        iframe_out = rc.index(out_frame.lower())
    except ValueError:
        raise Exception("The specifid output coordinate system "
                        "is invalid, please select one of: 'beam', 'inst', "
                        "'earth', 'principal'.")

    if iframe_out == iframe_in:
        # Should this generate an error?
        return obj

    if iframe_out > iframe_in:
        reverse = False
    else:
        reverse = True

    while obj.props['coord_sys'].lower() != out_frame.lower():
        csin = obj['props']['coord_sys']
        if csin == 'ship':
            csin = 'inst'
        inow = rc.index(csin)
        if reverse:
            func = getattr(rmod, rc[inow - 1] + '2' + rc[inow])
        else:
            func = getattr(rmod, rc[inow] + '2' + rc[inow + 1])
        func(obj, reverse=reverse)

    return obj

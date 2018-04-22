from .nortek.rotate import vector as r_vec
from .nortek.rotate import awac as r_awac
from .nortek.rotate import signature as r_sig
from .rdi import rotate as r_rdi

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


def rotate(obj, out_frame='earth', inplace=False):
    """Rotate a data object into a new coordinate system.

    Parameters
    ----------

    obj : :class:`Velocity <data.velocity.Velocity>`
      The dolfyn velocity-data (ADV or ADP) object to rotate.

    out_frame : string {'beam', 'inst', 'earth', 'principal'}
      The coordinate system to rotate the data into.

    inplace : bool
      Operate on the input data object (True), or return a copy that
      has been rotated (False, default).

    Returns
    -------
    objout : :class:`Velocity <data.velocity.Velocity>`
      The rotated data object. This is `obj` if inplace is True.

    """
    rmod = None
    for ky in rot_module_dict:
        if obj.make_model.startswith(ky):
            rmod = rot_module_dict[ky]
            break
    if rmod is None:
        raise ValueError("Rotations are not defined for "
                         "instrument '{}'.".format(obj.make_model))
    if not inplace:
        obj = obj.copy()

    # Get the 'indices' of the rotation chain
    csin = obj.props['coord_sys'].lower()
    if csin == 'ship':
        csin = 'inst'
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
        inow = rc.index(csin)
        if reverse:
            func = getattr(rmod, rc[inow - 1] + '2' + rc[inow])
        else:
            func = getattr(rmod, rc[inow] + '2' + rc[inow + 1])
        func(obj, reverse=reverse)

    return obj

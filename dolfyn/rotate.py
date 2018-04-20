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


def rotate(advo, out_frame='earth', inplace=False):
    rmod = None
    for ky in rot_module_dict:
        if advo.make_model.startswith(ky):
            rmod = rot_module_dict[ky]
            break
    if rmod is None:
        raise ValueError("Rotations are not defined for "
                         "instrument '{}'.".format(advo.make_model))
    if not inplace:
        advo = advo.copy()

    # Get the 'indices' of the rotation chain
    csin = advo.props['coord_sys'].lower()
    if csin == 'ship':
        csin = 'inst'
    try:
        iframe_in = rc.index(csin)
    except ValueError:
        raise Exception("The coordinate system of the input "
                        "data object, '{}', is invalid."
                        .format(advo.props['coord_sys']))
    try:
        iframe_out = rc.index(out_frame.lower())
    except ValueError:
        raise Exception("The specifid output coordinate system "
                        "is invalid, please select one of: 'beam', 'inst', "
                        "'earth', 'principal'.")

    if iframe_out == iframe_in:
        # Should this generate an error?
        return advo

    if iframe_out > iframe_in:
        reverse = False
    else:
        reverse = True

    while advo.props['coord_sys'] != out_frame:
        inow = rc.index(csin)
        if reverse:
            func = getattr(rmod, rc[inow - 1] + '2' + rc[inow])
        else:
            func = getattr(rmod, rc[inow] + '2' + rc[inow + 1])
        func(advo, reverse=reverse)

    return advo

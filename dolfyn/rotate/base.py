import numpy as np
from numpy.linalg import det
from .base_nortek import orient2euler, euler2orient


class BadDeterminantWarning(UserWarning):
    """A warning for the determinant is not equal to 1.
    """
    pass


def _find_method(obj, string):
    """Find methods in object that starts with `string`.
    """
    out = []
    for key in dir(obj):
        if key.startswith(string):
            out.append(getattr(obj, key))
    return out


def call_rotate_methods(velobj, rmat, cs_from, cs_to):

    for rot_method in _find_method(velobj, '_rotate_'):
        # Call the method:
        rot_method(rmat, cs_from, cs_to)
    # Now search subgroups
    for subobj in velobj.iter_subgroups():
        for rot_method in _find_method(subobj, '_rotate_'):
            # And call their rotate methods
            rot_method(rmat, cs_from, cs_to)


def rotate_tensor(tensor, rmat):
    return np.einsum('ij...,jlm...,nl...->inm...', rmat, tensor, rmat)


def is_positive_definite(tensor):
    t = np.moveaxis(tensor, [0, 1], [-2, -1])
    val = t[..., 0, 0] > 0
    for idx in [2, 3]:
        val &= np.linalg.det(t[..., :idx, :idx]) > 0
    return val


def _check_rotmat_det(rotmat, thresh=1e-3):
    """Check that the absolute error of the determinant is small.

          abs(det(rotmat) - 1) < thresh

    Returns a boolean array.
    """
    if rotmat.ndim > 2:
        rotmat = np.transpose(rotmat)
    return np.abs(det(rotmat) - 1) < thresh


def _check_declination(advo):
    odata = advo['orient']
    cs = advo.props['coord_sys']
    if 'declination' not in advo.props:
        if 'orientmat' in odata and \
           advo._make_model.startswith('nortek vector'):
            # Vector's don't have p,r,h when they have an orientmat.
            p, r, h = orient2euler(odata['orientmat'])
            odata['pitch'] = p
            odata['roll'] = r
            odata['heading'] = h
        # warnings.warn(
        #     'No declination in adv object.  Assuming a declination of 0.')
        return

    if 'orientmat' in odata and \
       not advo.props.get('declination_in_orientmat', False):
        # Declination is defined as positive if MagN is east of
        # TrueN. Therefore we must rotate about the z-axis by minus
        # the declination angle to get from Mag to True.
        cd = np.cos(-np.deg2rad(advo.props['declination']))
        sd = np.sin(-np.deg2rad(advo.props['declination']))
        # The ordering is funny here because orientmat is the
        # transpose of the inst->earth rotation matrix:
        Rdec = np.array([[cd, -sd, 0],
                         [sd, cd, 0],
                         [0, 0, 1]])
        odata['orientmat'] = np.einsum('ij,kjl->kil',
                                       Rdec,
                                       odata['orientmat'])
        # NOTE: for a moment I thought I needed to do a tensor
        # rotation on orientmat, but that's not the case. It seems
        # like the rotation matrix isn't actually a "tensor".
        # I checked this by showing that the above actually gives the
        # desired result of rotating vectors by the declination.

        advo.props['declination_in_orientmat'] = True
        if advo._make_model.startswith('nortek vector'):
            p, r, h = orient2euler(odata['orientmat'])
            odata['pitch'] = p
            odata['roll'] = r
            odata['heading'] = h
            advo.props['declination_in_heading'] = True

    if 'heading' in odata and \
       not advo.props.get('declination_in_heading', False):

        odata['heading'] += advo.props['declination']
        odata['heading'][odata['heading'] < 0] += 360
        odata['heading'][odata['heading'] > 360] -= 360
        advo.props['declination_in_heading'] = True

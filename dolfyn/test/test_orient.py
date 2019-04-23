from dolfyn.rotate.base import euler2orient, orient2euler
import numpy as np
from dolfyn.test.base import load_tdata as load
from dolfyn.rotate.base import _check_declination


def check_hpr(h, p, r, omatin):
    omat = euler2orient(h, p, r)
    assert np.allclose(omat, omatin), (
        'Orientation matrix different than expected!\nExpected:\n{}\nGot:\n{}'
        .format(np.array(omatin), omat))
    hpr = orient2euler(omat)
    assert np.allclose(hpr, [h, p, r]), (
        "Angles different than specified, orient2euler and euler2orient are "
        "antisymmetric!\nExpected:\n{}\nGot:\n{}"
        .format(hpr, np.array([h, p, r]), ))


def test_hpr_defs():
    """
    These tests confirm that the euler2orient and orient2euler functions
    are consistent, and that they follow the conventions defined in the
    DOLfYN documentation (data-structure.html#heading-pitch-roll), namely:

      - a "ZYX" rotation order. That is, these variables are computed
        assuming that rotation from the earth -> instrument frame happens
        by rotating around the z-axis first (heading), then rotating
        around the y-axis (pitch), then rotating around the x-axis (roll).

      - heading is defined as the direction the x-axis points, positive
        clockwise from North (this is the opposite direction from the
        right-hand-rule around the Z-axis)

      - pitch is positive when the x-axis pitches up (this is opposite the
        right-hand-rule around the Y-axis)

      - roll is positive according to the right-hand-rule around the
        instument's x-axis

    IF YOU MAKE CHANGES TO THESE CONVENTIONS, BE SURE TO UPDATE THE
    DOCUMENTATION.

    """
    check_hpr(0, 0, 0, [[0, 1, 0],
                        [-1, 0, 0],
                        [0, 0, 1], ])

    check_hpr(90, 0, 0, [[1, 0, 0],
                         [0, 1, 0],
                         [0, 0, 1], ])

    check_hpr(90, 0, 90, [[1, 0, 0],
                          [0, 0, 1],
                          [0, -1, 0], ])

    sq2 = 1. / np.sqrt(2)
    check_hpr(45, 0, 0, [[sq2, sq2, 0],
                         [-sq2, sq2, 0],
                         [0, 0, 1], ])

    check_hpr(0, 45, 0, [[0, sq2, sq2],
                         [-1, 0, 0],
                         [0, -sq2, sq2], ])

    check_hpr(0, 0, 45, [[0, 1, 0],
                         [-sq2, 0, sq2],
                         [sq2, 0, sq2], ])

    check_hpr(90, 45, 90, [[sq2, 0, sq2],
                           [-sq2, 0, sq2],
                           [0, -1, 0], ])

    c30 = np.cos(np.deg2rad(30))
    s30 = np.sin(np.deg2rad(30))
    check_hpr(30, 0, 0, [[s30, c30, 0],
                         [-c30, s30, 0],
                         [0, 0, 1], ])


def test_pr_declination():
    # Test to confirm that pitch and roll don't change when you set
    # declination
    declin = 15.37

    dat = load('vector_data_imu01.h5')
    h0, p0, r0 = orient2euler(dat['orient']['orientmat'])

    dat.set_declination(declin)
    h1, p1, r1 = orient2euler(dat['orient']['orientmat'])

    assert np.allclose(p0, p1), "Pitch changes when setting declination"
    assert np.allclose(r0, r1), "Roll changes when setting declination"
    assert np.allclose(h0 + declin, h1), "incorrect heading change when setting declination"

    dat = load('vector_data_imu01.h5')
    dat.props['declination'] = declin
    _check_declination(dat)
    h2, p2, r2 = orient2euler(dat['orient']['orientmat'])
    assert np.allclose(p0, p2), "Pitch changes when setting declination"
    assert np.allclose(r0, r2), "Roll changes when setting declination"
    assert np.allclose(h0, h2 - declin), "heading doesn't change as expected when setting Declination"
    

    
if __name__ == '__main__':
    test_hpr_defs()
    test_pr_declination()

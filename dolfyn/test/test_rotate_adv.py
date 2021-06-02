from dolfyn.test import test_adv as tr
import dolfyn.adv.api as avm
from dolfyn import rotate2, calc_principal_heading, set_declination
from dolfyn.test.base import load_ncdata as load, save_ncdata as save
from dolfyn.rotate.base import euler2orient
import numpy as np
import unittest
from xarray.testing import assert_allclose
from numpy.testing import assert_allclose as assert_ac


def test_inst2head_rotmat():
    # Validated test
    td = tr.dat.copy(deep=True)

    #Swap x,y, reverse z
    td = avm.set_inst2head_rotmat(td, [[0, 1, 0],
                                       [1, 0, 0],
                                       [0, 0,-1]])

    # assert ((td.Veldata.u == tr.dat.Veldata.v).all() and
    #         (td.Veldata.v == tr.dat.Veldata.u).all() and
    #         (td.Veldata.w == -tr.dat.Veldata.w).all()
    #         ), "head->inst rotations give unexpeced results."
    #Coords don't get altered here
    assert_ac(td.Veldata.u.values, tr.dat.Veldata.v.values)
    assert_ac(td.Veldata.v.values, tr.dat.Veldata.u.values)
    assert_ac(td.Veldata.w.values, -tr.dat.Veldata.w.values)

    # Validation for non-symmetric rotations
    td = tr.dat.copy(deep=True)
    R = euler2orient(20, 30, 60, units='degrees') # arbitrary angles
    td = avm.set_inst2head_rotmat(td, R)
    vel1 = td.vel
    # validate that a head->inst rotation occurs (transpose of inst2head_rotmat)
    vel2 = np.dot(R, tr.dat.vel)
    #assert (vel1 == vel2).all(), "head->inst rotations give unexpeced results."
    assert_ac(vel1.values, vel2)
    

def test_rotate_inst2earth(make_data=False):
    td = tr.dat.copy(deep=True)
    td = rotate2(td, 'earth', inplace=True)
    tdm = tr.dat_imu.copy(deep=True)
    tdm = rotate2(tdm, 'earth', inplace=True)

    if make_data:
        save(td, 'vector_data01_rotate_inst2earth.nc')
        save(tdm, 'vector_data_imu01_rotate_inst2earth.nc')
        return

    cd = load('vector_data01_rotate_inst2earth.nc')
    cdm = load('vector_data_imu01_rotate_inst2earth.nc')

    # msg = "adv.rotate.inst2earth gives unexpected results for {}"
    # for t, c, msg in (
    #         (td, cd, msg.format('vector_data01')),
    #         (tdm, cdm, msg.format('vector_data_imu01')),
    # ):
    #     yield data_equiv, t, c, msg
    assert_allclose(td, cd)
    assert_allclose(tdm, cdm)


def test_rotate_earth2inst():
    td = load('vector_data01_rotate_inst2earth.nc')
    td = rotate2(td, 'inst', inplace=True)
    tdm = load('vector_data_imu01_rotate_inst2earth.nc')
    tdm = rotate2(tdm, 'inst', inplace=True)

    cd = tr.dat.copy(deep=True)
    cdm = tr.dat_imu.copy(deep=True)
    # The heading/pitch/roll data gets modified during rotation, so it
    # doesn't go back to what it was.
    cdm = cdm.drop_vars(['heading','pitch','roll'])
    tdm = tdm.drop_vars(['heading','pitch','roll'])

    # msg = "adv.rotate.inst2earth gives unexpected REVERSE results for {}"
    # for t, c, msg in (
    #         (td, cd, msg.format('vector_data01')),
    #         (tdm, cdm, msg.format('vector_data_imu01')),
    # ):
    #     yield data_equiv, t, c, msg
    assert_allclose(td, cd, atol=1e-6)
    assert_allclose(tdm, cdm, atol=1e-6)


def test_rotate_inst2beam(make_data=False):
    td = tr.dat.copy(deep=True)
    td = rotate2(td, 'beam', inplace=True)
    tdm = tr.dat_imu.copy(deep=True)
    tdm = rotate2(tdm, 'beam', inplace=True)

    if make_data:
        save(td, 'vector_data01_rotate_inst2beam.nc')
        save(tdm, 'vector_data_imu01_rotate_inst2beam.nc')
        return

    cd = load('vector_data01_rotate_inst2beam.nc')
    cdm = load('vector_data_imu01_rotate_inst2beam.nc')

    # msg = "adv.rotate.beam2inst gives unexpected REVERSE results for {}"
    # for t, c, msg in (
    #         (td, cd, msg.format('vector_data01')),
    #         (tdm, cdm, msg.format('vector_data_imu01')),
    # ):
    #     yield data_equiv, t, c, msg
    assert_allclose(td, cd, atol=1e-6)
    assert_allclose(tdm, cdm, atol=1e-6)


def test_rotate_beam2inst():
    td = load('vector_data01_rotate_inst2beam.nc')
    td = rotate2(td, 'inst', inplace=True)
    tdm = load('vector_data_imu01_rotate_inst2beam.nc')
    tdm = rotate2(tdm, 'inst', inplace=True)

    cd = tr.dat.copy(deep=True)
    cdm = tr.dat_imu.copy(deep=True)

    # msg = "adv.rotate.beam2inst gives unexpected results for {}"
    # for t, c, msg in (
    #         (td, cd, msg.format('vector_data01')),
    #         (tdm, cdm, msg.format('vector_data_imu01')),
    # ):
    #     yield data_equiv, t, c, msg
    assert_allclose(td, cd, atol=1e-6)
    assert_allclose(tdm, cdm, atol=1e-6)


def test_rotate_earth2principal(make_data=False):
    td = load('vector_data01_rotate_inst2earth.nc')
    td.attrs['principal_heading'] = calc_principal_heading(td['vel'])
    td = rotate2(td, 'principal', inplace=True)
    tdm = load('vector_data_imu01_rotate_inst2earth.nc')
    tdm.attrs['principal_heading'] = calc_principal_heading(tdm['vel'])
    tdm = rotate2(tdm, 'principal', inplace=True)

    if make_data:
        save(td, 'vector_data01_rotate_earth2principal.nc')
        save(tdm, 'vector_data_imu01_rotate_earth2principal.nc')
        return

    cd = load('vector_data01_rotate_earth2principal.nc')
    cdm = load('vector_data_imu01_rotate_earth2principal.nc')

    # msg = "adv.rotate.earth2principal gives unexpected results for {}"
    # for t, c, msg in (
    #         (td, cd, msg.format('vector_data01')),
    #         (tdm, cdm, msg.format('vector_data_imu01')),
    # ):
    #     yield data_equiv, t, c, msg
    assert_allclose(td, cd, atol=1e-6)
    assert_allclose(tdm, cdm, atol=1e-6)


def test_rotate_earth2principal_set_declination():
    declin = 3.875
    td = load('vector_data01_rotate_inst2earth.nc')
    td0 = td.copy(deep=True)
    
    td.attrs['principal_heading'] = calc_principal_heading(td['vel'])
    td = rotate2(td, 'principal', inplace=True)
    td = set_declination(td, declin)
    td = rotate2(td, 'earth', inplace=True)
    
    td0 = set_declination(td0, -1)
    td0 = set_declination(td0, declin)
    td0.attrs['principal_heading'] = calc_principal_heading(td0['vel'])
    td0 = rotate2(td0, 'earth')

    # data_equiv(td0, td,
    #            "Something is wrong with declination "
    #            "handling w/r/t principal_heading.")
    assert_allclose(td0, td, atol=1e-6)
    

class warnings_testcase(unittest.TestCase):
    def test_rotate_warnings(self):
        warn1 = tr.dat.copy(deep=True)
        warn2 = tr.dat.copy(deep=True)
        warn2.attrs['coord_sys'] = 'flow'
        warn3 = tr.dat.copy(deep=True)
        warn3.attrs['inst_model'] = 'ADV'
        
        with self.assertRaises(Exception):
            rotate2(warn1, 'ship')
        with self.assertRaises(Exception):
            rotate2(warn2, 'earth')
        with self.assertRaises(Exception):
            avm.set_inst2head_rotmat(warn3, np.eye(3))
        with self.assertRaises(Exception):
            avm.set_inst2head_rotmat(warn3, np.eye(3))
            avm.set_inst2head_rotmat(warn3, np.eye(3))
        


if __name__=='__main__':
    test_inst2head_rotmat()
    test_rotate_inst2earth()
    test_rotate_earth2inst()
    test_rotate_beam2inst()
    test_rotate_inst2beam()
    test_rotate_earth2principal()
    test_rotate_earth2principal_set_declination()
    unittest.main()
    
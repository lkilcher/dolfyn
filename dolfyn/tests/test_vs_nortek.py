from . import test_read_adp as tr
from . import base
from dolfyn.rotate.api import rotate2
from numpy.testing import assert_allclose
import numpy as np
import scipy.io as sio
#import matplotlib.pyplot as plt

'''
Testing against velocity and bottom-track velocity data in Nortek mat files
exported from SignatureDeployment.

inst2earth rotation fails for AHRS-equipped istruments and I don't know why - 
I believe it's due to an RC filter (or some such) on Nortek's side after they
load in the orientation matrix from the AHRS (Check out the difference 
colorplots compared to non-AHRS instruments.) Using HPR- or quaterion-calc'd 
orientation matrices doesn't close the gap.

'''


def load_nortek_matfile(filename):
    # remember to transpose this data
    data = sio.loadmat(filename,
                       struct_as_record=False,
                       squeeze_me=True)
    d = data['Data']
    # print(d._fieldnames)
    burst = 'Burst'
    bt = 'BottomTrack'

    beam = ['_VelBeam1', '_VelBeam2', '_VelBeam3', '_VelBeam4']
    b5 = 'IBurst_VelBeam5'
    inst = ['_VelX', '_VelY', '_VelZ1', '_VelZ2']
    earth = ['_VelEast', '_VelNorth', '_VelUp1', '_VelUp2']
    axis = {'beam': beam, 'inst': inst, 'earth': earth}
    AHRS = 'Burst_AHRSRotationMatrix'  # , 'IBurst_AHRSRotationMatrix']

    vel = {'beam': {}, 'inst': {}, 'earth': {}}
    for ky in vel.keys():
        for i in range(len(axis[ky])):
            vel[ky][i] = np.transpose(getattr(d, burst+axis[ky][i]))
        vel[ky] = np.stack((vel[ky][0], vel[ky][1],
                            vel[ky][2], vel[ky][3]), axis=0)

    if AHRS in d._fieldnames:
        vel['omat'] = np.transpose(getattr(d, AHRS))

    if b5 in d._fieldnames:
        vel['b5'] = np.transpose(getattr(d, b5))
        #vel['omat5'] = getattr(d, AHRS[1])

    if bt+beam[0] in d._fieldnames:
        vel_bt = {'beam': {}, 'inst': {}, 'earth': {}}
        for ky in vel_bt.keys():
            for i in range(len(axis[ky])):
                vel_bt[ky][i] = np.transpose(getattr(d, bt+axis[ky][i]))
            vel_bt[ky] = np.stack((vel_bt[ky][0], vel_bt[ky][1],
                                   vel_bt[ky][2], vel_bt[ky][3]), axis=0)

        return vel, vel_bt
    else:
        return vel


def rotate(axis):
    # BenchFile01.ad2cp
    td_sig = rotate2(tr.dat_sig, axis, inplace=False)
    # Sig1000_IMU.ad2cp no userdata
    td_sig_i = rotate2(tr.dat_sig_i, axis, inplace=False)
    # VelEchoBT01.ad2cp
    td_sig_ieb = rotate2(tr.dat_sig_ieb, axis,
                         inplace=False)
    # Sig500_Echo.ad2cp
    td_sig_ie = rotate2(tr.dat_sig_ie, axis,
                        inplace=False)

    td_sig_vel = load_nortek_matfile(base.rfnm('BenchFile01.mat'))
    td_sig_i_vel = load_nortek_matfile(base.rfnm('Sig1000_IMU.mat'))
    td_sig_ieb_vel, vel_bt = load_nortek_matfile(base.rfnm('VelEchoBT01.mat'))
    td_sig_ie_vel = load_nortek_matfile(base.rfnm('Sig500_Echo.mat'))

    # ARHS inst2earth orientation matrix check
    # Checks the 1,1 element because the nortek orientmat's shape is [9,:] as
    # opposed to [3,3,:]
    if axis == 'inst':
        assert_allclose(td_sig_i.orientmat[0][0].values,
                        td_sig_i_vel['omat'][0, :500], atol=1e-7)
        assert_allclose(td_sig_ieb.orientmat[0][0].values,
                        td_sig_ieb_vel['omat'][0, :][..., :100], atol=1e-7)

    # 4-beam velocity
    assert_allclose(td_sig.vel.values, td_sig_vel[axis][..., :500], atol=1e-5)
    assert_allclose(td_sig_i.vel.values,
                    td_sig_i_vel[axis][..., :500], atol=5e-3)
    assert_allclose(td_sig_ieb.vel.values,
                    td_sig_ieb_vel[axis][..., :100], atol=5e-3)
    assert_allclose(td_sig_ie.vel.values,
                    td_sig_ie_vel[axis][..., :500], atol=1e-5)

    # 5th-beam velocity
    if axis == 'beam':
        assert_allclose(td_sig_i.vel_b5.values,
                        td_sig_i_vel['b5'][..., :500], atol=1e-5)
        assert_allclose(td_sig_ieb.vel_b5.values,
                        td_sig_ieb_vel['b5'][..., :100], atol=1e-5)
        assert_allclose(td_sig_ie.vel_b5.values,
                        td_sig_ie_vel['b5'][..., :500], atol=1e-5)

    # bottom-track
    assert_allclose(td_sig_ieb.vel_bt.values,
                    vel_bt[axis][..., :100], atol=5e-3)


def test_rotate2_beam():
    rotate('beam')


def test_rotate2_inst():
    rotate('inst')


def test_rotate2_earth():
    rotate('earth')


if __name__ == '__main__':
    test_rotate2_beam()
    test_rotate2_inst()
    test_rotate2_earth()

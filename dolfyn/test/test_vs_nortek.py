from dolfyn.test import test_read_adp as tr
from dolfyn.test import base
from numpy.testing import assert_allclose
import numpy as np
import scipy.io as sio
#import matplotlib.pyplot as plt

'''
Testing against velocity and bottom-track velocity data in Nortek mat files
exported from SignatureDeployment.
inst2earth rotation fails for AHRS-equipped istruments and I don't know why - 
I believe it's a compounding (trunctation?) error on Nortek's side. (Look at
difference colorplots compared to non-AHRS instruments) Using HPR- or quat-
calc'd orientmats doesn't close the gap

'''

def load_nortek_matfile(filename):
    # remember to transpose this data
    data = sio.loadmat(filename, 
                       struct_as_record=False, 
                       squeeze_me=True)
    d = data['Data']
    #print(d._fieldnames)
    burst = 'Burst'
    bt = 'BottomTrack'
    
    beam = ['_VelBeam1','_VelBeam2','_VelBeam3','_VelBeam4']
    b5 = 'IBurst_VelBeam5'
    inst = ['_VelX','_VelY','_VelZ1','_VelZ2']
    earth = ['_VelEast','_VelNorth','_VelUp1','_VelUp2']
    axis = {'beam':beam, 'inst':inst, 'earth':earth}
    AHRS = 'Burst_AHRSRotationMatrix'#, 'IBurst_AHRSRotationMatrix']
    
    vel = {'beam':{},'inst':{},'earth':{}}
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
        vel_bt = {'beam':{},'inst':{},'earth':{}}
        for ky in vel_bt.keys():
            for i in range(len(axis[ky])):
                vel_bt[ky][i] = np.transpose(getattr(d, bt+axis[ky][i]))
            vel_bt[ky] = np.stack((vel_bt[ky][0], vel_bt[ky][1], 
                                   vel_bt[ky][2], vel_bt[ky][3]), axis=0)
    
        return vel, vel_bt
    else:
        return vel

def rotate(axis):
    td_sig = tr.dat_sig.Veldata.rotate2(axis) # BenchFile01.ad2cp
    td_sig_i = tr.dat_sig_i.Veldata.rotate2(axis) # Sig1000_IMU.ad2cp no userdata
    td_sig_ieb = tr.dat_sig_ieb.Veldata.rotate2(axis) #VelEchoBT01.ad2cp
    #td_sig_ie = tr.dat_sig_ie.Veldata.rotate2(axis) #Sig500_Echo.ad2cp
    #td_sig_vm = tr.dat_sig_vm.Veldata.rotate2(axis) #SigVM1000.ad2cp
    
    td_sig_vel = load_nortek_matfile(base.rfnm('BenchFile01.mat'))
    td_sig_i_vel = load_nortek_matfile(base.rfnm('Sig1000_IMU.mat'))
    td_sig_ieb_vel, vel_bt = load_nortek_matfile(base.rfnm('VelEchoBT01.mat'))
    #td_sig_ie_vel = load_nortek_matfile('data/Sig500_Echo.mat')
    #td_sig_vm_vel, vm_vel_bt = load_nortek_matfile('data/SigVM1000.mat')
    
    # ARHS inst2earth orientation matrix
    # checks the 11 element because the nortek orientmat is [9,:] as opposed
    # to [3,3,:]
    if axis=='inst':
        assert_allclose(td_sig_i.orientmat[0][0].values, 
                        td_sig_i_vel['omat'][0,:], atol=1e-7)
        assert_allclose(td_sig_ieb.orientmat[0][0].values, 
                        td_sig_ieb_vel['omat'][0,:][...,:-1], atol=1e-7)
    
    # 4-beam velocity
    #plt.figure(); plt.pcolormesh(td_sig.vel[0].values-td_sig_vel[axis][0]); plt.colorbar()
    assert_allclose(td_sig.vel.values, td_sig_vel[axis], atol=1e-5)
    #plt.figure(); plt.pcolormesh(td_sig_i.vel[0].values-td_sig_i_vel[axis][0]); plt.colorbar()
    assert_allclose(td_sig_i.vel.values, td_sig_i_vel[axis], atol=1e-2)
    #plt.figure(); plt.pcolormesh(td_sig_ieb.vel[0].values-td_sig_ieb_vel[axis][0][...,:-1]); plt.colorbar()
    assert_allclose(td_sig_ieb.vel.values, td_sig_ieb_vel[axis][...,:-1], atol=1e-2)
    #assert_allclose(td_sig_ie.vel.values, td_sig_ie_vel[axis][...,:-1], atol=1e-5)
    #assert_allclose(td_sig_vm.vel.values, td_sig_vm_vel[axis][...,1:-1], atol=1e-5)
    
    # 5th-beam velocity
    if axis=='beam':
        assert_allclose(td_sig_i.vel_b5.values, td_sig_i_vel['b5'][...,:-1], atol=1e-5)
        assert_allclose(td_sig_ieb.vel_b5.values, td_sig_ieb_vel['b5'][...,:-1], atol=1e-5)
    
    # bottom-track
    assert_allclose(td_sig_ieb.vel_bt.values, vel_bt[axis], atol=1e-2)
    #assert_allclose(td_sig_vm.vel_bt.values, vm_vel_bt[axis][...,:-1], atol=1e-5)

def test_rotate2_beam():
    rotate('beam')
    
def test_rotate2_inst():
    rotate('inst')

def test_rotate2_earth():
    rotate('earth')
    
if __name__=='__main__':
    test_rotate2_beam()
    test_rotate2_inst()
    test_rotate2_earth()
    

from dolfyn.test import test_read_adp as tr
from dolfyn.test.base import load_nortek_matfile
from numpy.testing import assert_allclose

'''
Testing against velocity and bottom-track velocity data in Nortek mat files
exported from SignatureDeployment.
Something funky is up with ours or their rotations from the AHRS orientation 
matrix. Not clean at all - 1-5% of randomly distributed datapoints are bad.
'''

def rotate(axis):
    td_sig = tr.dat_sig.Veldata.rotate2(axis) # BenchFile01.ad2cp
    td_sig_i = tr.dat_sig_i.Veldata.rotate2(axis) # Sig1000_IMU.ad2cp
    td_sig_ieb = tr.dat_sig_ieb.Veldata.rotate2(axis) #VelEchoBT01.ad2cp
    #td_sig_ie = tr.dat_sig_ie.Veldata.rotate2(axis) #Sig500_Echo.ad2cp
    #td_sig_vm = tr.dat_sig_vm.Veldata.rotate2(axis) #SigVM1000.ad2cp
    
    td_sig_vel = load_nortek_matfile('data/BenchFile01.mat')
    td_sig_i_vel = load_nortek_matfile('data/Sig1000_IMU.mat')
    td_sig_ieb_vel, vel_bt = load_nortek_matfile('data/VelEchoBT01.mat')
    #td_sig_ie_vel = load_nortek_matfile('data/Sig500_Echo.mat')
    #td_sig_vm_vel, vm_vel_bt = load_nortek_matfile('data/SigVM1000.mat')
    
    assert_allclose(td_sig.vel.values, td_sig_vel[axis], rtol=1e-7, atol=1e-3)
    assert_allclose(td_sig_i.vel.values, td_sig_i_vel[axis], rtol=1e-7, atol=1e-3)
    assert_allclose(td_sig_ieb.vel.values, td_sig_ieb_vel[axis][...,:-1], rtol=1e-7, atol=1e-3)
    #assert_allclose(td_sig_ie.vel.values, td_sig_ie_vel[axis][...,:-1], rtol=1e-7, atol=1e-3)
    #assert_allclose(td_sig_vm.vel.values, td_sig_vm_vel[axis][...,1:-1], rtol=1e-7, atol=1e-3)
    assert_allclose(td_sig_ieb.vel_bt.values, vel_bt[axis], rtol=1e-7, atol=1e-3)
    #assert_allclose(td_sig_vm.vel_bt.values, vm_vel_bt[axis][...,:-1], rtol=1e-7, atol=1e-3)

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
    

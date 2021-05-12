# Start by importing DOLfYN:
import dolfyn as dlfn
import dolfyn.adv.api as avm

# Then read a file containing adv data:
dat = dlfn.read_example('vector_data01.VEC')

# Clean the file using the Goring+Nikora method:
mask = avm.clean.GN2002(dat.vel)
dat_cln = avm.clean.cleanFill(dat, mask, method='cubic')

# Rotate that data from the instrument to earth frame:
# First set the magnetic declination
dat_cln = dat_cln.Veldata.set_declination(10) # 10 degrees East
dat_earth = dlfn.rotate2(dat_cln, 'earth')

# Rotate it into a 'principal axes frame':
# First calculate the principal heading
dat_earth.attrs['principal_heading'] = dlfn.calc_principal_heading(dat_earth.vel)
dat_princ = dlfn.rotate2(dat_earth, 'principal')

# Define an averaging object, and create an 'ensembled' data set:
binner = avm.TurbBinner(n_bin=19200, fs=dat_princ.fs, n_fft=4096)
dat_binned = binner(dat_princ)

# At any point you can save the data:
dlfn.save(dat_binned,'adv_data_rotated2principal.nc')

# And reload the data:
dat_bin_copy = dlfn.load('adv_data_rotated2principal.nc')

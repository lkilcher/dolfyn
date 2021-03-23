# Start by importing DOLfYN:
import dolfyn as dlfn

# Then read a file containing adv data:
dat = dlfn.read('../../../data/vector_data01.VEC')

# Clean the file using the Goring+Nikora method:
dlfn.adv.clean.GN2002(dat)

# Rotate that data from the instrument to earth frame:
# First set the magnetic declination
dat = dlfn.rotate2(dat, 'inst')

dat.set_declination(10) # 10 degrees East
dat = dlfn.rotate2(dat, 'earth')

# Rotate it into a 'principal axes frame':
# First calculate the principal heading
dat.props['principal_heading'] = dlfn.calc_principal_heading(dat.vel)
dat = dlfn.rotate2(dat, 'principal')

# Define an averaging object, and create an 'ensembled' data set:
binner = dlfn.adv.TurbBinner(n_bin=40000, fs=dat.props['fs'], n_fft=4096)
dat_bin = binner(dat)

# At any point you can save the data:
dat_bin.to_hdf5('adv_data_rotated2principal.h5')

# And reload the data:
dat_bin_copy = dlfn.load('adv_data_rotated2principal.h5')

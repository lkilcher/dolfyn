# Start by importing DOLfYN:
import dolfyn as dlfn
import dolfyn.adv.api as api

# Then read a file containing adv data:
dat = dlfn.read_example('vector_data01.VEC')

# Clean the file using the Goring+Nikora method:
mask = api.clean.GN2002(dat.vel)
dat['vel'] = api.clean.clean_fill(dat.vel, mask, npt=12, method='cubic')

# Rotate that data from the instrument to earth frame:
# First set the magnetic declination
dat_cln = dlfn.set_declination(dat, 10)  # 10 degrees East
dat_earth = dlfn.rotate2(dat_cln, 'earth')

# Rotate it into a 'principal axes frame':
# First calculate the principal heading
dat_earth.attrs['principal_heading'] = dlfn.calc_principal_heading(
    dat_earth.vel)
dat_fin = dlfn.rotate2(dat_earth, 'principal')

# Define an averaging object, and create an 'ensembled' data set:
binner = api.ADVBinner(n_bin=9600, fs=dat_fin.fs, n_fft=4096)
dat_binned = binner(dat_fin)

# At any point you can save the data:
#dlfn.save(dat_binned, 'adv_data.nc')

# And reload the data:
#dat_bin_copy = dlfn.load('adv_data.nc')

# To use this module, import it:
from dolfyn.adv import api as adv

# Then read a file containing adv data:
dat = adv.read_nortek('../../../data/vector_data01.VEC')

# Then clean the file using the Goring+Nikora method:
adv.clean.GN2002(dat)

# Then rotate that data from the instrument to earth frame:
adv.rotate.inst2earth(dat)

# Then rotate it into a 'principal axes frame':
adv.rotate.earth2principal(dat)

# Define an averaging object, and create an 'averaged' data set:
binner = adv.turb_binner(n_bin=40000, fs=dat.fs, n_fft=4096)
dat_bin = binner(dat)

# At any point you can save the data:
dat_bin.save('adv_data_rotated2principal.h5')

# And reload the data:
dat_bin_copy = adv.load('adv_data_rotated2principal.h5')

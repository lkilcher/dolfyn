# To get started first import the DOLfYN ADV advanced programming
# interface (API):
import dolfyn.adv.api as avm

# Import matplotlib tools for plotting the data:
from matplotlib import pyplot as plt
import matplotlib.dates as dt
import numpy as np

##############################
# User input and customization

# The file to load:
fname = './data/vector_data_imu01.vec'
# This file is available at:
# http://goo.gl/yckXtG

# This is the vector from the ADV head to the body frame, in meters,
# in the ADV coordinate system.
body2head_vec = np.array([0.48, -0.07, -0.27])

# This is the orientation matrix of the ADV head relative to the body.
# In this case the head was aligned with the body, so it is the
# identity matrix:
body2head_rotmat = np.eye(3)

# The time range of interest.
t_range = [
    # The instrument was in place starting at 12:08:30 on June 12,
    # 2012.
    dt.date2num(dt.datetime.datetime(2012, 6, 12, 12, 8, 30)),
    # The data is good to the end of the file.
    np.inf
]

# This is the filter to use for motion correction:
accel_filter = 0.1

# End user input section.
###############################

# Read a file containing adv data:
dat_raw = avm.read_nortek(fname)

# Crop the data for t_range using DOLfYN's 'subset' method (creates a
# copy):
t_range_inds = (t_range[0] < dat_raw.mpltime) & (dat_raw.mpltime < t_range[1])
dat = dat_raw.subset(t_range_inds)
dat.props['body2head_vec'] = body2head_vec
dat.props['body2head_rotmat'] = body2head_rotmat

# Then clean the file using the Goring+Nikora method:
avm.clean.GN2002(dat)

####
# Create a figure for comparing screened data to the original.
fig = plt.figure(1, figsize=[8, 4])
fig.clf()
ax = fig.add_axes([.14, .14, .8, .74])

# Plot the raw (unscreened) data:
ax.plot(dat_raw.mpltime, dat_raw.u, 'r-', rasterized=True)

# Plot the screened data:
ax.plot(dat.mpltime, dat.u, 'g-', rasterized=True)
bads = np.abs(dat.u - dat_raw.u[t_range_inds])
ax.text(0.55, 0.95,
        "%0.2f%% of the data were 'cleaned'\nby the Goring and Nikora method."
        % (np.float(sum(bads > 0)) / len(bads) * 100),
        transform=ax.transAxes,
        va='top',
        ha='left',
        )

# Add some annotations:
ax.axvspan(dt.date2num(dt.datetime.datetime(2012, 6, 12, 12)),
           t_range[0], zorder=-10, facecolor='0.9',
           edgecolor='none')
ax.text(0.13, 0.9, 'Mooring falling\ntoward seafloor',
        ha='center', va='top', transform=ax.transAxes,
        size='small')
ax.text(t_range[0] + 0.0001, 0.6, 'Mooring on seafloor',
        size='small',
        ha='left')
ax.annotate('', (t_range[0] + 0.006, 0.3),
            (t_range[0], 0.3),
            arrowprops=dict(facecolor='black', shrink=0.0),
            ha='right')

# Finalize the figure
# Format the time axis:
tkr = dt.MinuteLocator(interval=5)
frmt = dt.DateFormatter('%H:%M')
ax.xaxis.set_major_locator(tkr)
ax.xaxis.set_minor_locator(dt.MinuteLocator(interval=1))
ax.xaxis.set_major_formatter(frmt)
ax.set_ylim([-3, 3])

# Label the axes:
ax.set_ylabel('$u\,\mathrm{[m/s]}$', size='large')
ax.set_xlabel('Time [June 12, 2012]')
ax.set_title('Data cropping and cleaning')
ax.set_xlim([dt.date2num(dt.datetime.datetime(2012, 6, 12, 12)),
             dt.date2num(dt.datetime.datetime(2012, 6, 12, 12, 30))])

# Save the figure:
fig.savefig('./fig/crop_data.pdf')
# end cropping figure
####

dat_cln = dat.copy()

# Perform motion correction (including rotation into earth frame):
avm.motion.correct_motion(dat, accel_filter)

# Rotate the uncorrected data into the earth frame,
# for comparison to motion correction:
avm.rotate.inst2earth(dat_cln)

#ax.plot(dat.mpltime, dat.u, 'b-')

# Then rotate it into a 'principal axes frame':
avm.rotate.earth2principal(dat)
avm.rotate.earth2principal(dat_cln)

# Average the data and compute turbulence statistics
dat_bin = avm.calc_turbulence(dat, n_bin=19200,
                              n_fft=4096)
dat_cln_bin = avm.calc_turbulence(dat_cln, n_bin=19200,
                                  n_fft=4096)

# At any point you can save the data:
dat_bin.save('adv_data_rotated2principal.h5')

# And reload the data:
dat_bin_copy = avm.load('adv_data_rotated2principal.h5')

####
# Figure to look at spectra
fig2 = plt.figure(2, figsize=[6, 6])
fig2.clf()
ax = fig2.add_axes([.14, .14, .8, .74])

ax.loglog(dat_bin.freq, dat_bin.Suu_hz.mean(0),
          'b-', label='motion corrected')
ax.loglog(dat_cln_bin.freq, dat_cln_bin.Suu_hz.mean(0),
          'r-', label='no motion correction')

# Add some annotations
ax.axhline(1.7e-4, color='k', zorder=21)
ax.text(2e-3, 1.7e-4, 'Doppler noise level', va='bottom', ha='left',)

ax.text(1, 2e-2, 'Motion\nCorrection')
ax.annotate('', (3.6e-1, 3e-3), (1, 2e-2),
            arrowprops={'arrowstyle': 'fancy',
                        'connectionstyle': 'arc3,rad=0.2',
                        'facecolor': '0.8',
                        'edgecolor': '0.6',
                        },
            ha='center',
            )

ax.annotate('', (1.6e-1, 7e-3), (1, 2e-2),
            arrowprops={'arrowstyle': 'fancy',
                        'connectionstyle': 'arc3,rad=0.2',
                        'facecolor': '0.8',
                        'edgecolor': '0.6',
                        },
            ha='center',
            )

# Finalize the figure
ax.set_xlim([1e-3, 20])
ax.set_ylim([1e-4, 1])
ax.set_xlabel('frequency [hz]')
ax.set_ylabel('$\mathrm{[m^2s^{-2}/hz]}$', size='large')

f_tmp = np.logspace(-3, 1)
ax.plot(f_tmp, 4e-5 * f_tmp ** (-5. / 3), 'k--')

ax.set_title('Velocity Spectra')
ax.legend()
ax.axvspan(1, 16, 0, .2, facecolor='0.8', zorder=-10, edgecolor='none')
ax.text(4, 4e-4, 'Doppler noise', va='bottom', ha='center',
        #bbox=dict(facecolor='w', alpha=0.9, edgecolor='none'),
        zorder=20)

fig2.savefig('./fig/motion_vel_spec.pdf')

import xarray as xr 
import dolfyn as dlfn
from dolfyn.data.time import num2date


dat = dlfn.load(f'dolfyn/test/data/RDI_test01.h5')

time = num2date(dat.mpltime)
beams = list(range(dat.vel.shape[0]))
bins = dat.range


ori1, ori2 = ['E','N','U'], ['X','Y','Z']

#Dims = np.array(['time','beams','bins','ori1','ori2'])
#Coords = [time,beams,bins,ori1,ori2]
#coorLen = np.array([len(x) for x in Coords])

da = {}

for newky, oldky in [('vel', 'vel'),
                     ('corr', 'signal.corr'),
                     ('echo', 'signal.echo'),
                     ('percent_good', 'signal.prcnt_gd'),
                     ]:
    da[newky] = xr.DataArray(
        dat[oldky],
        dims=['beams', 'range', 'time'],
        coords={'beams': beams, 'range': bins, 'time': time},
    )

da['vel'].attrs['units'] = 'm/s'

da['depth'] = xr.DataArray(
    dat['depth_m'],
    dims=['time'], coords={'time': time},
    attrs={'units': 'm'},
)
da['temp'] = xr.DataArray(
    dat.env.temperature_C,
    dims=['time'], coords={'time': time},
    attrs={'units': 'C'},)
da['salinity'] = xr.DataArray(
    dat.env.salinity,
    dims=['time'], coords={'time': time},
    attrs={'units': 'psu'},
)
da['orientmat'] = xr.DataArray(
    dat.orient.orientmat,
    dims=['inst', 'earth', 'time'], coords={'inst': ori2, 'earth': ori1, 'time': time},
)
for ky in ['heading', 'pitch', 'roll']:
    da[ky + '_raw'] = xr.DataArray(
        dat['orient.raw'][ky],
        dims=['time', ], coords={'time': time},
        attrs={'units': 'deg'},
    )
    da[ky + '_std_raw'] = xr.DataArray(
        dat['orient.raw'][ky + '_std'],
        dims=['time', ], coords={'time': time},
        attrs={'units': 'deg'},
    )
da['heading_raw'].attrs['units'] = 'degrees Magnetic'

out = xr.Dataset(da)
out.attrs = dat.props
out.attrs['has imu'] = int(out.attrs['has imu'])
out.attrs['rotate_vars'] = list(out.attrs['rotate_vars'])
for ky in dat.config.keys():
    out.attrs['_config_' + ky] = dat.config[ky]

out.to_netcdf('tmp/RDI_test01.h5')

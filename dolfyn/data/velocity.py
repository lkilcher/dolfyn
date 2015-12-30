# from .base import np, TimeBased, ma, DataError
from base import ma
# from ..io.main import Saveable
# import h5py as h5
from .binned import TimeBinner, rad_hz
# from .time import num2date
from pycoda.base import data
import numpy as np


class Velocity(data):

    @property
    def u(self, ):
        return self['vel'][0]

    @property
    def v(self, ):
        return self['vel'][1]

    @property
    def w(self, ):
        return self['vel'][2]

    @property
    def U(self, ):
        return self['vel'][0] + self['vel'][1] * 1j


class VelBindatTke(data):

    @property
    def Ecoh(self,):
        """
        Niel Kelley's "coherent energy", i.e. the rms of the stresses.
        """
        # Why did he do it this way, instead of the sum of the magnitude of the
        # stresses?
        return np.sqrt((self['stress'] ** 2).sum(0))

    def Itke(self, thresh=0):
        """
        Turbulence intensity.

        Ratio of standard deviation of velocity magnitude to velocity
        magnitude.
        """
        return np.ma.masked_where(self.U_mag < thresh,
                                  np.sqrt(self.tke) / self.U_mag)

    def I(self, thresh=0):
        """
        Turbulence intensity.

        Ratio of standard deviation of velocity magnitude to velocity
        magnitude.
        """
        return np.ma.masked_where(self.U_mag < thresh,
                                  self.sigma_Uh / self.U_mag)

    @property
    def tke(self,):
        """
        The turbulent kinetic energy (sum of the three components).
        """
        return self['vel2'].sum(0)

    @property
    def upvp_(self,):
        """
        u'v' Reynolds stress
        """
        return self['stress'][0]

    @property
    def upwp_(self,):
        """
        u'w' Reynolds stress
        """
        return self['stress'][1]

    @property
    def vpwp_(self,):
        """
        v'w' Reynolds stress
        """
        return self['stress'][2]

    @property
    def upup_(self,):
        """
        u'u' component of the tke.
        """
        return self['vel2'][0]

    @property
    def vpvp_(self,):
        """
        v'v' component of the tke.
        """
        return self['vel2'][1]

    @property
    def wpwp_(self,):
        """
        w'w' component of the tke.
        """
        return self['vel2'][2]


class VelBinnerTke(TimeBinner):

    def calc_tke(self, veldat, noise=[0, 0, 0]):
        """Calculate the tke (variances of u,v,w).

        Parameters
        ----------
        veldat : a velocity data array. The last dimension is assumed
                 to be time.

        noise : a three-element vector of the noise levels of the
                velocity data for ach component of velocity.

        Returns
        -------
        out : An array of tke values.
        """
        out = np.mean(self.detrend(veldat) ** 2,
                      -1, dtype=np.float64).astype('float32')
        out[0] -= noise[0] ** 2
        out[1] -= noise[1] ** 2
        out[2] -= noise[2] ** 2
        return out

    def calc_stress(self, veldat):
        """Calculate the stresses (cross-covariances of u,v,w).

        Parameters
        ----------
        veldat : a velocity data array. The last dimension is assumed
                 to be time.

        Returns
        -------
        out : An array of stress values.
        """
        out = np.empty(self._outshape(veldat.shape)[:-1], dtype=np.float32)
        out[0] = np.mean(self.detrend(veldat[0]) * self.detrend(veldat[1]),
                         -1, dtype=np.float64
                         ).astype(np.float32)
        out[1] = np.mean(self.detrend(veldat[0]) * self.detrend(veldat[2]),
                         -1, dtype=np.float64
                         ).astype(np.float32)
        out[2] = np.mean(self.detrend(veldat[1]) * self.detrend(veldat[2]),
                         -1, dtype=np.float64
                         ).astype(np.float32)
        return out


class VelBindatSpec(VelBindatTke):

    @property
    def freq(self,):
        """
        Frequency [Hz].
        """
        return self.omega / rad_hz


class VelBinnerSpec(VelBinnerTke):

    def calc_vel_psd(self, veldat, fs=None,
                     rotate_u=False, noise=[0, 0, 0],
                     n_pad=None, window='hann'):
        """
        Calculate the psd of velocity.

        Parameters
        ----------
        veldat   : np.ndarray
          The raw velocity data.
        fs : float (optional)
          The sample rate (default: from the binner).
        rotate_u : bool (optional)
          If True, each 'bin' of horizontal velocity is rotated into
          its principal axis prior to calculating the psd.  (default:
          False).
        noise : list(3 floats) (optional)
          Noise level of each component's velocity measurement (default to 0).
        n_pad : int
          The number of values to pad with zero
        """
        fs = self._parse_fs(fs)
        if rotate_u:
            tmpdat = self.reshape(veldat[0] + 1j * veldat[1])
            tmpdat *= np.exp(-1j * np.angle(tmpdat.mean(-1)))
            if noise[0] != noise[1]:
                print(
                    'Warning: noise levels different for u,v. This means \
                    noise-correction cannot be done here when rotating \
                    velocity.')
                noise[0] = noise[1] = 0
            datu = self.psd(tmpdat.real, fs, noise=noise[0],
                            n_pad=n_pad, window=window)
            datv = self.psd(tmpdat.imag, fs, noise=noise[1],
                            n_pad=n_pad, window=window)
        else:
            datu = self.psd(veldat[0], fs, noise=noise[0],
                            n_pad=n_pad, window=window)
            datv = self.psd(veldat[1], fs, noise=noise[1],
                            n_pad=n_pad, window=window)
        datw = self.psd(veldat[2], fs, noise=noise[2],
                        n_pad=n_pad, window=window)
        out = np.empty([3] + list(datw.shape), dtype=np.float32)
        if ma.valid:
            if self.hz:
                units = ma.unitsDict({'s': -2, 'm': -2, 'hz': -1})
            else:
                units = ma.unitsDict({'s': -1, 'm': -2})
            out = ma.marray(out,
                            ma.varMeta('S_{%s%s}', units,
                                       veldat.meta.dim_names + ['freq'])
                            )
        out[:] = datu, datv, datw
        return out

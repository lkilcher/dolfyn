import numpy as np


def calc_epsilon_LT83(spec, omega, U_mag, omega_range=[6.28, 12.57]):
    r"""
    Calculate the dissipation rate from the spectrum.

    Parameters
    ----------

    spec : |np.ndarray| (...,n_time,n_f)
      The spectrum array [m^2/s]

    omega : |np.ndarray| (n_f)
      The frequency array [rad/s]

    U_mag : |np.ndarray| (...,n_time)
      The velocity magnitude [m/s]

    omega_range : iterable(2)
      The range over which to integrate/average the spectrum.

    Returns
    -------
    epsilon : np.ndarray (...,n_time)
      The dissipation rate.

    Notes
    -----

    This uses the `standard` formula for dissipation:

    .. math:: S(k) = \alpha \epsilon^{2/3} k^{-5/3}

    where :math:`\alpha = 0.5` (1.5 for all three velocity
    components), `k` is wavenumber and `S(k)` is the turbulent
    kinetic energy spectrum.

    With :math:`k \rightarrow \omega / U` then--to preserve variance--
    :math:`S(k) = U S(\omega)` and so this becomes:

    .. math:: S(\omega) = \alpha \epsilon^{2/3} \omega^{-5/3} U^{2/3}

    LT83 : Lumley and Terray "Kinematics of turbulence convected
    by a random wave field" JPO, 1983, 13, 2000-2007.

    """
    inds = (omega_range[0] < omega) & (omega < omega_range[1])
    a = 0.5
    f_shp = [1] * (spec.ndim - 1) + [inds.sum()]
    return np.mean(spec[..., inds] *
                   (omega[inds].reshape(f_shp)) ** (5 / 3) / a,
                   axis=-1) ** (3 / 2) / U_mag

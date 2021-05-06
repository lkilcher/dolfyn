from .base import ADVdata
import numpy as np
from dolfyn.data.time import num2date


class multi_sync(ADVdata):

    """
    A base class for multiple, sync'd advs.
    """
    # Is this useful?

    @property
    def n_inst(self,):
        return self.u.shape[0]

    def __repr__(self,):
        dt = num2date(self.mpltime[0])
        tm = [self.mpltime[0], self.mpltime[-1]]
        return ("%0.2fh sync'd %d-ADV record, started: %s" %
                ((tm[-1] - tm[0]) * 24,
                 self.n_inst,
                 dt.strftime('%b %d, %Y %H:%M')))


def merge_lag(adv_list, lag=[0]):
    """
    Merge a adv objects based on a predefined lag.

    Parameters
    ----------
    adv_list : iterable(ADVdata)
      An iterable of :class:`ADVdata <dolfyn.adv.base.ADVdata>`
      objects to be merged.
    lag : iterable(ints), len(adv_list)
      An iterable of the lag, in timesteps.

    Returns
    -------
    adv_sync : :class:`multi_sync`
      A multi-adv data object.

    Notes
    -----

    Each :class:`ADVdata <dolfyn.adv.base.ADVdata>` in `adv_list` must
    have the same timestep (sample rate), and have the same data
    attributes.

    """
    out = multi_sync()
    mx = np.inf
    ndat = len(adv_list)
    for a, l in zip(adv_list, lag):
        mx = np.min([len(a) - l, mx])
    for nm, dat, grpnm in a.iter_wg():
        out.init_data((ndat, mx), nm, dtype=dat.dtype, group=grpnm, )
    for idx, (a, l) in enumerate(zip(adv_list, lag)):
        for nm, dat in a:
            getattr(out, nm)[idx,:] = dat[l:mx + l]
    a._copy_props(out)
    a.props['DeltaT'] = np.diff(out.mpltime, axis=0).mean()
    out.mpltime = out.mpltime.mean(0)
    return out


def merge_syncd(adv_list, sync_on='ensemble'):
    """
    Merge adv objects based on a data attribute.

    Parameters
    ----------
    adv_list : iterable(ADVdata)
      An iterable of :class:`ADVdata <dolfyn.adv.base.ADVdata>`
      objects to be merged.

    sync_on : string
      The attribute name to sync the data on.

    Returns
    -------
    adv_sync : :class:`multi_sync`
      A multi-adv data object.

    Notes
    -----

    Each :class:`ADVdata <~dolfyn.adv.base.ADVdata>` in `adv_list` must
    have the same timestep (sample rate), and have the same data
    attributes.

    """
    out = multi_sync()
    mn = 0
    mx = np.inf
    ndat = len(adv_list)
    if not sync_on == 'straight':
        for a in adv_list:
            # First find the min and max indices that are consistent across all
            # data sets:
            mn = np.max((mn, np.min(getattr(a, sync_on))))
            mx = np.min((mx, np.max(getattr(a, sync_on))))
    else:
        for a in adv_list:
            mx = np.min((mx, len(a.mpltime)))

    # Now initialize the data object.
    for nm, dat, grpnm in a.iter_wg():
        out.init_data((ndat, mx - mn), nm, dtype=dat.dtype, group=grpnm)
    for idx, a in enumerate(adv_list):
        if not sync_on == 'straight':
            inds = getattr(a, sync_on)
            i0 = np.nonzero(mn == inds)[0]
            ie = np.nonzero(mx == inds)[-1]
        else:
            i0 = mn
            ie = mx
        # Now join the data sets:
        for nm, dat in a:
            getattr(out, nm)[idx,:] = dat[i0:ie]
    if not sync_on == 'straight':
        setattr(out, sync_on, getattr(out, sync_on)[0])
    a._copy_props(out)
    return out

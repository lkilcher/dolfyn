from base import adv_raw,np

class multi_sync(adv_raw):
    """
    A base class for multiple, sync'd advs.
    """
    @property
    def n_inst(self,):
        return self.u.shape[0]
        
    def __repr__(self,):
        if (not hasattr(self,'time')) or self.time[0]<1:
            print( 'Warning: no time information!' )
            dt=tbx.num2date(693596)
            tm=np.array([0,0])
        else:
            dt=tbx.num2date(self.mpltime[0])
            tm=[self.mpltime[0],self.mpltime[-1]]
        return "%0.2fh sync'd %d-ADV record, started: %s" % ((tm[-1]-tm[0])*24,self.n_inst,dt.strftime('%b %d, %Y %H:%M'))


def merge_lag(avds,lag=[0]):
    """
    Merge a set of adv objects based on a predefined lag.
    """
    out=multi_sync()
    mx=np.inf
    ndat=len(avds)
    for avd,l in zip(avds,lag):
        mx=np.min([len(avd)-l,mx])
    for nm,dat,grpnm in avd.iter_wg():
        out.init_data((ndat,mx),nm,dtype=dat.dtype,group=grpnm,meta=(ma and getattr(dat,'meta',None)))
        if ma.valid and hasattr(dat,'meta'):
            getattr(out,nm).meta.dim_names=['inst']+dat.meta.dim_names
    for idx,(avd,l) in enumerate(zip(avds,lag)):
        for nm,dat in avd:
            getattr(out,nm)[idx,:]=dat[l:mx+l]
    avd._copy_props(out)
    avd.props['DeltaT']=np.diff(out.mpltime,axis=0).mean()
    out.mpltime=out.mpltime.mean(0)
    return out


def merge_syncd(avds,sync_on='ensemble'):
    """
    Merge a list of adv objects
    """
    out=multi_sync()
    mn=0
    mx=np.inf
    ndat=len(avds)
    if not sync_on=='straight':
        for avd in avds:
            # First find the min and max indices that are consistent across all data sets:
            mn=np.max((mn,np.min(getattr(avd,sync_on))))
            mx=np.min((mx,np.max(getattr(avd,sync_on))))
    else:
        for avd in avds:
            mx=np.min((mx,len(avd.mpltime)))
    
    # Now initialize the data object.
    for nm,dat,grpnm in avd.iter_wg():
        out.init_data((ndat,mx-mn),nm,dtype=dat.dtype,group=grpnm)
    for idx,avd in enumerate(avds):
        if not sync_on=='straight':
            inds=getattr(avd,sync_on)
            i0=np.nonzero(mn==inds)[0]
            ie=np.nonzero(mx==inds)[-1]
        else:
            i0=mn
            ie=mx
        # Now join the data sets:
        for nm,dat in avd:
            getattr(out,nm)[idx,:]=dat[i0:ie]
    if not sync_on=='straight':
        setattr(out,sync_on,getattr(out,sync_on)[0])
    avd._copy_props(out)
    return out
            
            

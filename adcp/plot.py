import ptools as pt

class adcp_fig(pt.figobj):
    ## def sax_params(self,**kwargs):
    ##     if not kwargs.has_key('h'):
    ##         kwargs['h']=[.14,.93,.1] 
    ##     if not kwargs.has_key('v'):
    ##         kwargs['v']=[.14,.93,.1]
    ##     return kwargs

    def __init__(self,data,fignum,inds=slice(None),**kwargs):
        self.data=data
        self.inds=inds
        super(adcp_fig,self).__init__(fignum,**kwargs)
        #self.ax=self.sax.ax[0,:]

class prof_fig(adcp_fig):
    
    def plot_mean(self,name,ax,**kwargs):
        ax.plot(self.data[name][:,self.inds].mean(1),self.data.z,**kwargs)


class pcol_fig(adcp_fig):
    def __init__(self,data,fignum,inds=slice(None),**kwargs):
        self.data=data
        self.inds=inds
        super(adcp_fig,self).__init__(fignum,**kwargs)
        self.ax=self.sax.ax[:,0]
    nax=(3,1)
    def pcol_all(self,**kwargs):
        for ax,vr in zip(self.ax,['u','v','w']):
            ax.cpcolor(self.data.time[self.inds],self.data.z,self.data[vr][:,self.inds],cmap=pt.mycmap.redblue,vmin=-2,vmax=2)


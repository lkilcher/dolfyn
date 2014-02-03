#import base as adv
import ptools as pt
reload(pt)
import numpy as np
import tools as tbx

z_adv=4.6# meters, this number is the real number.
z_adv=10# this number fits the spectra best.

phi_m=5.7
phi_eps=(1+2.5)**(3./2.)

phi_m=1
phi_eps=1


    


class psd(object):
    lbl_pos='ul'
    plot_kws={'color':'r','linestyle':'-','rasterized':False}
    
    def __init__(self,specobj,delta,axs,vrs=['Suu','Svv','Sww'],**kwargs):
        self.data=specobj
        self.vars=vrs
        self.ax=axs
        self.delta=delta
        self.inds=delta(specobj)
        self.plot_kws.update(kwargs)
        self.mean_lines=[]
        self.all_lines=[]
        
    def label(self,):
        for ax,vr in zip(self.ax,self.vars):
            ax.annoteCorner(self.data.label(vr),self.lbl_pos,offset=8)

    def xlabel(self,):
        self.ax[-1].set_xlabel(self.data.xlbl)
    
    def plot_kwds(self,**kwargs):
        kws=self.plot_kws.copy()
        kws.update(self.delta.attrs)
        kws.update(kwargs)
        return kws
    
    def plot_mean(self,**kwargs):
        kws=self.plot_kwds(**kwargs)
        if not kws.has_key('zorder'):
            kws['zorder']=10
        for ax,vr in zip(self.ax,self.vars):
            self.mean_lines.extend(ax.plot(self.data.freq_norm(self.inds),self.data.mean_spec(vr,self.inds),**kws))

    def plot_all(self,**kwargs):
        if not kwargs.has_key('color'):
            kwargs['color']='y'
        kws=self.plot_kwds(kwargs)
        if not kws.has_key('zorder'):
            kws['zorder']=1
        for ax,vr in zip(self.ax,self.vars):
            self.all_lines.extend(ax.plot(self.data.freq_norm(self.inds),getattr(self.data,vr)[self.inds,:],**kws))

    def showL(self,L=[0.1,1,10]):
        u=np.abs(self.data.u[self.inds].mean())
        for ax in self.ax:
            vl=2*np.pi*u/(np.array(L))/self.data.freqNorm[self.inds,:].mean(0)
            ax.vln(vl,color='b',linestyle='-')
            for l,v in zip(L,vl):
                ax.offset_text(v,.95,(r'$%g\mathrm{m}$' % l),offset=(3,0),color='b',ha='left',va='top',transform='DataXAxesY',clip_on=True,fontsize='x-small')

    def show_spec(self,specfunc,lnstyle,tag=None,**kwargs):
        for ax,vr in zip(self.ax,self.vars):
            spec=specfunc(self.inds)
            if spec is None:
                return
            if self.data.specNorm.__class__ is dict:
                ax.plot(self.data.freq_norm(self.inds),spec[vr]/self.data.specNorm[vr[1]][self.inds].mean(0),lnstyle,**kwargs)
            else:
                ax.plot(self.data.freq_norm(self.inds),spec[vr]/self.data.specNorm[self.inds].mean(0),lnstyle,**kwargs)

class psd_fig_base(pt.figobj):
    hspace=1#inches
    drawlabels=True
    
    def sax_params(self,**kwargs):
        if not kwargs.has_key('h'):
            kwargs['h']=self.sax_h
        if not kwargs.has_key('v'):
            kwargs['v']=self.sax_v
        return kwargs

    def plot_power(self,power=-5./3.,factor=.01,**kwargs):
        xdt=np.array([1e-10,1e10])
        ydt=factor*xdt**power
        for ax in self.ax.flatten():
            ax.plot(xdt,ydt,**kwargs)
    
    def calcFigSize(self,axsize):
        figsize=[]
        tmp=pt.calcFigSize(self.nax[1],ax=[axsize,self.hspace],frm=[.8,.2])
        self.sax_h=tmp[1]
        figsize.append(tmp[0])
        tmp=pt.calcFigSize(self.nax[0],ax=[axsize,.2],frm=[.7,.4])
        self.sax_v=tmp[1]
        figsize.append(tmp[0])
        return figsize

    def showL(self,L=[10,1,.1]):
        for plt in self.plts[0]:
            plt.showL(L)

    def show_spec(self,spec_func,lnstyle='k--',tag='smooth',zorder=11,**kwargs):
        for plt in self.plts[0]:
            plt.show_spec(spec_func,lnstyle=lnstyle,tag=tag,zorder=zorder,**kwargs)

    ## #def show_spec(self,specobj,):
        
    ## def show_smooth(self,z_adv=10,lnstyle='k--',tag='smooth',zorder=11,**kwargs):
    ##     for plt in self.plts[0]:
    ##         plt.show_spec(plt.specmodel_smooth(z_adv=z_adv),lnstyle,tag=tag,zorder=11,**kwargs)

    ## def show_kilcher_bbl(self,normobj,lnstyle='k-',tag='smooth',zorder=11,**kwargs):
    ##     for plt in self.plts[0]:
    ##         plt.show_spec(plt.specmodel_kilcher_bbl(normobj),lnstyle,tag=tag,zorder=11,**kwargs)

    ## def show_IEC_Kaimal(self,z_adv=10,lnstyle='b--',tag='Kaimal',zorder=11,**kwargs):
    ##     for plt in self.plts[0]:
    ##         plt.show_spec(plt.specmodel_IEC_Kaimal(z_adv=z_adv),lnstyle,tag=tag,zorder=11,**kwargs)
    
    ## def show_IEC_VKM(self,z_adv=10,lnstyle='b-',tag='VKM',zorder=11,**kwargs):
    ##     for plt in self.plts[0]:
    ##         plt.show_spec(plt.specmodel_IEC_VKM(z_adv=z_adv),lnstyle,tag=tag,zorder=11,**kwargs)

    def plot_mean(self,**kwargs):
        for plt in self.plts.flatten():
            plt.plot_mean(**kwargs)

    def plot_all(self,**kwargs):
        for plt in self.plts.flatten():
            plt.plot_all(**kwargs)
    
    def title(self,string=None):
        if string is None:
            string=self._title
        self.fig.text(0.5,.99,string,ha='center',va='top')
        #self.ax[0,0].set_title(string)
        self.fig.canvas.set_window_title(string.strip('$'))

class compare_spec(psd_fig_base):
    #sax_h=[.2,.94,.16]
    #sax_v=[.07,.94,.03]
    hspace=.2
    fontsize=14

    def titles(self,):
        for ax,dls in zip(self.ax[0,:],self.deltas):
            ind=0
            if len(dls)>1 and dls[0].range[0]==-dls[1].range[1] and dls[0].range[1]==-dls[1].range[0]:
                if dls[0].range[0]<0:
                    ind=1
            ax.set_title(dls[ind].latexstr)

    def num_avg(self,):
        for ax,dls in zip(self.ax[0,:],self.deltas):
            for idx,dl in enumerate(dls):
                ax.annoteCorner('%d' % dl(self.data).sum(),(1,1),offset=(-20+16*idx,-6),color=dl.attrs['color'],ha='right',va='top')
    
    def __repr__(self,):
        return '<compare_spec>: %s, %d velocity ranges, %dx%d axes.' % (self._title.strip('$'),len(self.deltas),self.nax[0],self.nax[1])

    def __init__(self,advb,deltas,fignum,vrs=['Suu','Svv','Sww'],axsize=2,title='*NoTitle*',**kwargs):
        self._title=title
        self.deltas=deltas
        self.nax=(len(vrs),len(deltas))
        self.data=advb
        figsize=self.calcFigSize(axsize)
        self.initFig(fignum,figsize=figsize,**kwargs)
        self.saxes(self.nax)
        self.ax=self.sax.ax
        self.plts=np.empty((len(deltas[0]),len(deltas)),dtype='O')
        for idx,dls in enumerate(deltas):
            for id,dl in enumerate(dls):
                self.plts[id,idx]=psd(advb,dl,self.sax.ax[:,idx],vrs)
        

    def __exit__(self,type,value,traceback):
        for ax in self.ax.flatten():
            ax.set_xscale('log')
            ax.set_yscale('log')
        self.sax.hide(ax=self.sax.ax[-1,0])
        self.sax.hide('yticklabels',ax=self.sax.ax[-1,0])
        plt=self.plts[0,0]
        if self.drawlabels:
            plt.label()
        plt.xlabel()
        if plt.data.units_spec is not None:
            self.ax[-1,0].set_ylabel('$\mathrm{['+plt.data.units_spec+']}$',labelpad=1)
        if hasattr(plt.data,'xlim'):
            self.ax[-1,0].set_xlim(plt.data.xlim)
        if hasattr(plt.data,'ylim'):
            self.ax[-1,0].set_ylim(plt.data.ylim)
        self.titles()
        
class psd_fig(psd_fig_base):
    sax_h=[.2,.94,.16]
    sax_v=[.07,.94,.03]
    fontsize=14
    
    def __repr__(self,):
        return '<psd_fig>: %s, %dx%d axes.' % (self._title.strip('$'),self.nax[0],self.nax[1])
    
    def __init__(self,specobj,deltas,fignum,vrs=None,axsize=None,figsize=None,title=None,**kwargs):
        if specobj.__class__ is not list:
            specobj=[specobj]
        if vrs is None:
            vrs=specobj[0].specvars
        self.nax=(len(vrs),len(specobj))
        self.data=specobj
        if deltas.__class__ is not list():
            self.deltas=[deltas]
        else:
            self.deltas=deltas
        if title is None:
            self._title=self.deltas[0].latexstr
        if axsize is not None:
            figsize=self.calcFigSize(axsize)
        elif figsize is not None:
            pass
            #Need to add some constraints here?
        self.initFig(fignum,figsize=figsize,**kwargs)
        share=np.tile(np.arange(self.nax[1],dtype='int8'),(self.nax[0],1))+1
        self.saxes(self.nax,sharex=share,sharey=share)
        self.plts=np.empty((len(self.deltas),len(specobj)),dtype='O')
        for idx,dat in enumerate(specobj):
            for id,dlta in enumerate(self.deltas):
                self.plts[id,idx]=psd(dat,dlta,self.sax.ax[:,idx],vrs)
        self.ax=self.sax.ax

    def __exit__(self,type,value,traceback):
        #lbls=[r'$S_{uu}$',r'$S_{vv}$',r'$S_{ww}$']
        for ax in self.ax.flatten():
            ax.set_xscale('log')
            ax.set_yscale('log')
        self.sax.hide(ax=self.sax.ax[-1,:])
        self.sax.hide('yticklabels',ax=self.sax.ax[-1,:])
        for idx,plt in enumerate(self.plts[0]):
            plt.label()
            plt.xlabel()
            if plt.data.units_spec is not None:
                self.ax[-1,idx].set_ylabel('$\mathrm{['+plt.data.units_spec+']}$',labelpad=1)
            if hasattr(plt.data,'xlim'):
                self.ax[-1,idx].set_xlim(plt.data.xlim)
            if hasattr(plt.data,'ylim'):
                self.ax[-1,idx].set_ylim(plt.data.ylim)

def velranges2deltas(varname,vel_rngs,**kwargs):
    for vlrng in iter_velrngs(vel_rngs):
        yield tbx.delta(varname,vlrng,**kwargs)

def iter_velrngs(vel_rngs):
    for idx in range(len(vel_rngs)-1):
        if np.isnan(vel_rngs[idx]+vel_rngs[idx+1]):
            continue
        yield min(vel_rngs[idx:idx+2]),max(vel_rngs[idx:idx+2])

def velrngs2inds(dat,vlrngs):
    for vlrng in iter_velrngs(vlrngs):
        yield tbx.within(dat,vlrng),vlrng

def multi_psds(data,fig0,vel_rngs,plot_types=[psd],axsize=2,show_all_psd=True):
    figs=[]
    for idx,(inds,vlrng,) in enumerate(velrngs2inds(data.u,vel_rngs)):
        vl=np.mean(vlrng)
        if sum(inds)==0:
            continue
        with psd_fig(data,inds,fig0+idx,plot_types=plot_types,axsize=axsize,title=('$%0.1f<u<%0.1f$' % vlrng)) as fg:
            fg.plot_mean()
            if show_all_psd:
                fg.plot_all()
            fg.show_smooth(z_adv=z_adv)
            fg.show_kilcher_bbl(z_adv=z_adv)
            #fg.show_IEC_Kaimal(z_adv=z_adv)
            #fg.show_IEC_VKM(z_adv=z_adv)
            fg.showL()
            fg.title()
        figs.append(fg)
    return figs


class time_fig(pt.figobj):

    def zeroLine(self,color='k',linestyle='-',**kwargs):
        for ax in self.ax:
            ax.hln(0,color=color,linestyle=linestyle,**kwargs)

    def patch_ebbflood(self,var='u',val=0.3):
        for ax in self.ax:
            dat=getattr(self.data,var)
            if len(dat.shape)>1:
                dat=dat[:].mean(0)
            ax.fill_between(self.data.time,np.ones_like(self.data.time),where=dat>val,facecolor='r',zorder=-10,transform=ax.transDataXAxesY,edgecolor='none',alpha=.2)
            ax.fill_between(self.data.time,np.ones_like(self.data.time),where=dat<-val,facecolor='b',zorder=-10,transform=ax.transDataXAxesY,edgecolor='none',alpha=.2)

    def title(self,title=None):
        if title is None:
            title=self._title
        self.ax[0].set_title(title)
        self.fig.canvas.set_window_title(('Figure %d: ' % (self.fig.number))+title)
    
    def __init__(self,advb,fignum,vrs=['u','v','w'],title='*NoTitle*',**kwargs):
        self._title=title
        self.vars=vrs
        nax=self.nax=(len(vrs),1)
        self.data=advb
        self.inds=advb.inds
        if kwargs.has_key('figsize'):
            self.figsize=kwargs.pop('figsize')
        else:
            self.figsize=[8,5]
        if not kwargs.has_key('saxparams'):
            kwargs['saxparams']={}
        kwargs['saxparams']['sharey']=False
        kwargs['figsize']=self.figsize
        super(time_fig,self).__init__(fignum,nax,**kwargs)
        
    def sax_params(self,**kwargs):
        if not kwargs.has_key('h'):
            kwargs['h']=[.18,.94,.05]
        if not kwargs.has_key('v'):
            kwargs['v']=[.14,.9,.05]
        return kwargs

    def plot(self,ax,name,**kwargs):
        ylbl_args={'rotation':'vertical','fontsize':'medium','rotation':'horizontal','fontsize':'x-large',}
        ax.plot(self.data.time,getattr(self.data,name)[:].T,label=self.data[name].meta.get_label() if hasattr(self.data[name],'meta') else None,**kwargs)
        
    def plot_all(self,**kwargs):
        ylbl_args={'rotation':'vertical','fontsize':'medium','rotation':'horizontal','fontsize':'x-large',}
        for ax,vr in zip(self.ax,self.vars):
            if vr is None:
                continue
            if not hasattr(self.data,vr):
                continue
            self.plot(ax,vr,**kwargs)
            if hasattr(self.data[vr],'meta'):
                ax.set_ylabel(self.data[vr].meta.ylabel,**ylbl_args)
            
    ylim={'u':[-2,2],
          'v':[-.5001,.5001],
          'w':[-.5001,.5001],
          }
    yticks={'u':np.arange(-3,3),
            'v':np.arange(-.6,.6,.2),
            'w':np.arange(-.6,.6,.2),
            }
    def __exit__(self,type,value,traceback):
        self.sax.hide()
        self.title(self._title)
        self.ax[-1].set_xlabel(self.data.props['time_label'])
        self.ax[-1].set_xticks(np.arange(-100,100))
        self.ax[-1].set_xticks(np.arange(-100,100,.25),minor=True)
        for ax,vr in zip(self.ax,self.vars):
            if self.yticks.has_key(vr):
                ax.yaxis.grid(True)
                ax.set_yticks(self.yticks[vr])
            if self.ylim.has_key(vr):
                ax.set_ylim(self.ylim[vr])
        if hasattr(self.data,'time_lim'):
            ax.set_xlim(self.data.time_lim)

class vsTime(time_fig):
    """
    A class for plotting velocity versus time.
    """
    
    def __init__(self,fignum,vrs=['u','v','w'],inds=slice(None),title='*NoTitle*',**kwargs):
        """
        """
        self._title=title
        self.vars=vrs
        nax=self.nax=(len(vrs),1)
        if kwargs.has_key('figsize'):
            self.figsize=kwargs.pop('figsize')
        else:
            self.figsize=[8,5]
        if not kwargs.has_key('saxparams'):
            kwargs['saxparams']={}
        kwargs['saxparams']['sharey']=False
        kwargs['figsize']=self.figsize
        super(time_fig,self).__init__(fignum,nax,**kwargs)
        self.nax={nm:self.sax.ax[idx,0] for idx,nm in enumerate(vrs)}
        self.set_xlim=self.ax[0].set_xlim
        self.inds=inds
        
    def plot(self,datobj,**kwargs):
        for nm,ax in self.nax.iteritems():
            ax.plot(datobj.time[self.inds],getattr(datobj,nm)[self.inds],**kwargs)

    def __exit__(self,type,value,traceback):
        self.sax.hide()
        self.title(self._title)
        #self.ax[-1].set_xlabel(self.data.props['time_label'])
        self.ax[-1].set_xticks(np.arange(-100,100))
        self.ax[-1].set_xticks(np.arange(-100,100,.25),minor=True)
        for ax,vr in zip(self.ax,self.vars):
            if self.yticks.has_key(vr):
                ax.yaxis.grid(True)
                ax.set_yticks(self.yticks[vr])
            if self.ylim.has_key(vr):
                ax.set_ylim(self.ylim[vr])
        #if hasattr(self.data,'time_lim'):
        #    ax.set_xlim(self.data.time_lim)

def plot_stresses(advb,patchvar='u'):
    with time_fig(advb,802,title='Cross Correlations (Stresses)',vrs=['upwp_','upvp_','vpwp_']) as fgnow:
        fgnow.plot_all()
        fgnow.zeroLine('r','-')
        fgnow.patch_ebbflood(var=patchvar,val=0.4)
        fgnow.ax[0].set_ylim([-.015,.015])
        fgnow.ax[1].set_ylim([-.015,.015])
        fgnow.ax[2].set_ylim([-.005,.005])
        return fgnow

def plot_acorrs(advb,patchvar='u'):
    with time_fig(advb,801,title='Auto Correlations (Energy)',vrs=['upup_','vpvp_','wpwp_']) as fgnow:
        fgnow.plot_all()
        fgnow.patch_ebbflood(var=patchvar,val=0.4)
        fgnow.ax[0].set_ylim([1e-3,3e-1])
        fgnow.ax[1].set_ylim([1e-3,3e-1])
        fgnow.ax[2].set_ylim([1e-3,3e-1])
        fgnow.sax.set_yscale('log')
    return fgnow

def plot_vel(advb,patchvar='u'):
    with time_fig(advb,800,title='Velocity') as fgnow:
        fgnow.plot_all()
        fgnow.zeroLine('r','-')
        fgnow.patch_ebbflood(var=patchvar,val=0.4)
    return fgnow



def show_long_spec():
    advd.n_fft=2**18
    advd.Suu=advd.psd('u')
    advd.Svv=advd.psd('v')
    advd.Sww=advd.psd('w')
    advd.freq=tbx.psd_freq(advd.n_fft,advd.fs)

    figure(301)
    clf()
    sax=pt.saxes((3,1))
    sax.drawall()
    sax.ax[0,0].plot(advd.freq*2*np.pi,advd.Suu.real,'y-')
    sax.ax[1,0].plot(advd.freq*2*np.pi,advd.Svv.real,'y-')
    sax.ax[2,0].plot(advd.freq*2*np.pi,advd.Sww.real,'y-')
    for ax in sax.ax[:,0]:
        ax.set_xscale('log')
        ax.set_yscale('log')
    ax.set_xlim([8e-3,1e2])
    ax.set_ylim([1e-6,1e1])

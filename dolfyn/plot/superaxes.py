import matplotlib as mpl
import numpy as np
import new
import matplotlib.pylab as pylab
transforms = mpl.transforms
Axes = mpl.axes.Axes
rcParams = mpl.rcParams
from . import basefuncs as bf


def axes(*args, **kwargs):
    """
    Add an axes at position rect specified by:

    - ``axes()`` by itself creates a default full ``subplot(111)`` window axis.

    - ``axes(rect, axisbg='w')`` where *rect* = [left, bottom, width,
      height] in normalized (0, 1) units.  *axisbg* is the background
      color for the axis, default white.

    - ``axes(h)`` where *h* is an axes instance makes *h* the current
      axis.  An :class:`~matplotlib.axes.Axes` instance is returned.

    =======   ============   ================================================
    kwarg     Accepts        Desctiption
    =======   ============   ================================================
    axisbg    color          the axes background color
    frameon   [True|False]   display the frame?
    sharex    otherax        current axes shares xaxis attribute with otherax
    sharey    otherax        current axes shares yaxis attribute with otherax
    polar     [True|False]   use a polar axes?
    =======   ============   ================================================

    Examples
    --------

    * :file:`examples/pylab_examples/axes_demo.py` places custom axes.
    * :file:`examples/pylab_examples/shared_axis_demo.py` uses
      *sharex* and *sharey*.

    Notes
    -----

    This was copied from the pyplot axes function. Several methods
    have been added to the axes.

    """

    nargs = len(args)
    if nargs == 0:
        args = [[.1, .1, .8, .8]]
    if nargs > 1:
        raise TypeError('Only one non keyword arg to axes allowed')
    arg = args[0]

    axd = {}
    newd = {}
    newd['lw'] = rcParams['axes.linewidth']
    try:
        axd['axisbg'] = kwargs.pop('axisbg')
    except:
        pass
    for nm in ['axisbg', 'frameon', 'sharex', 'sharey', 'polar', ]:
        if nm in kwargs:
            axd[nm] = kwargs.pop(nm)
    if 'ticksize' in kwargs:
        newd['xticksize'] = kwargs.get('ticksize')
        newd['yticksize'] = kwargs.pop('ticksize')
    for nm in [('lw', 'linewidth'), 'linewidth', 'xticksize',
               'yticksize', ('fs', 'fontsize'), 'fontsize',
               'xlocation', 'ylocation']:
        if nm.__class__ is tuple:
            ky = nm[0]
            nm = nm[1]
        else:
            ky = nm
            nm = nm
        if ky in kwargs:
            newd[nm] = kwargs.pop(ky)
    if ('fig' not in kwargs) and ('figure' not in kwargs):
        fig = pylab.gcf()
    elif 'figure' in kwargs:
        fig = kwargs.pop('figure')
    else:
        fig = kwargs.pop('fig')

    if isinstance(arg, mpl.axes.Axes):
        a = fig.sca(arg)
    else:
        rect = arg
        a = fig.add_axes(rect, **axd)
        a.set(**kwargs)

        if 'xlocation' in newd:
            a.xaxis.set_ticks_position(newd['xlocation'])
            if newd['xlocation'] == 'top':
                a.spines['bottom'].set_visible(False)
            elif newd['xlocation'] == 'bottom':
                a.spines['top'].set_visible(False)
        if 'ylocation' in newd:
            a.yaxis.set_ticks_position(newd['ylocation'])
            if newd['ylocation'] == 'right':
                a.spines['left'].set_visible(False)
            elif newd['ylocation'] == 'left':
                a.spines['right'].set_visible(False)
        if 'lw' in newd:
            for sp in a.spines:
                a.spines[sp].set_linewidth(newd['lw'])
            for tck in a.xaxis.get_ticklines():
                tck.set_mew(newd['lw'])
            for tck in a.yaxis.get_ticklines():
                tck.set_mew(newd['lw'])
        if 'xticksize' in newd:
            for tck in a.xaxis.get_ticklines():
                tck.set_ms(newd['xticksize'])
        if 'yticksize' in newd:
            for tck in a.yaxis.get_ticklines():
                tck.set_ms(newd['yticksize'])
        if 'fontsize' in newd:
            for tklbl in a.xaxis.get_ticklabels():
                tklbl.set_fontsize(newd['fontsize'])
            for tklbl in a.yaxis.get_ticklabels():
                tklbl.set_fontsize(newd['fontsize'])

    a.transAxesXDataY = transforms.blended_transform_factory(
        a.transAxes, a.transData)
    a.transDataXAxesY = transforms.blended_transform_factory(
        a.transData, a.transAxes)

    a.setaxesframe = new.instancemethod(bf._setaxesframe, a, Axes)
    a.annoteCorner = new.instancemethod(bf.annoteCorner, a, Axes)
    a.offset_text = new.instancemethod(bf.offset_text, a, Axes)
    a.cpcolor = new.instancemethod(bf.cpcolor, a, Axes)
    a.cbar = new.instancemethod(bf.cbar, a, Axes)
    a.labelax = new.instancemethod(bf.labelax, a, Axes)
    a.skip_ticklabels = new.instancemethod(bf.skip_ticklabels, a, Axes)
    a.errorshadex = new.instancemethod(bf.errorshadex, a, Axes)
    # a.plot_specobj=new.instancemethod(plot_specobj,a,Axes)

    pylab.draw_if_interactive()
    return a


class disperse(dict):

    """
    This dict subclass is for dispersing axgroup properties passed to
    an axgroup.<some_method> across the individual calls to each
    axes.<some_method>.
    """
    pass


class dispersable(object):

    """
    A descriptor class for defining dispersable objects.
    """

    def __init__(self, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return dispersable
        return disperse([(ax, getattr(ax, self.name)) for ax in instance])

    def __set__(self, instance):
        raise AttributeError("Can't set attribute.")


class axgroup(object):

    """
    The axgroup class provides a group interface to axes - level methods.

    Many axes - level methods are defined here. These methods simply
    perform the same operation on each axes in the group. These
    methods are poorly documented here, refer to the documentation at
    the axes level for details(unless otherwise specified methods
    here simply pass arguments through to each call at the axes
    level).

    Parameters
    ----------

    axes:
        iterable
      A list, tuple or np.ndarray of axes objects that will be
      included in the group.

    """

    transAxesXDataY = dispersable("transAxesXDataY")
    transDataXAxesY = dispersable("transDataXAxesY")
    transAxes = dispersable("transAxes")
    transData = dispersable("transData")
    transLimits = dispersable("transLimits")

    def _disperse_kwargs(self, **kwargs):
        out = dict(**kwargs)
        for ax in self:
            for ky, val in list(kwargs.items()):
                if val.__class__ is disperse:
                    if len(val) != len(self):
                        raise Exception("The length of dispersable \
                        kwargs must match the length of the axgroup")
                    out[ky] = val[ax]
            yield ax, out

    def flatten(self,):
        return axgroup(self.axes.flatten())

    @property
    def flat(self,):
        return self.flatten()

    def to_list(self,):
        return list(self.flat)

    def to_set(self,):
        return set(self.flat)

    def __iter__(self,):
        for ax in self.axes.flatten():
            yield ax

    def __init__(self, axes):
        if set not in axes.__class__.__mro__:
            axes = np.array(axes)
        self.axes = axes

    alphNumAxes = bf.alphNumAxes

    @property
    def size(self,):
        """
        The size of the axes array.
        """
        return self.axes.size

    @property
    def shape(self,):
        """
        The shape of the axes array.
        """
        return self.axes.shape

    @property
    def ax(self,):
        """
        A shortcut to 'self.axes'
        """
        return self.axes

    def __repr__(self,):
        return '<axgroup: %s>' % self.axes.__repr__()

    def __len__(self,):
        return len(self.axes)

    def __getitem__(self, val):
        if hasattr(val, '__len__'):
            for v in val:
                if v.__class__ is slice:
                    return axgroup(self.axes[val])
        elif val.__class__ is slice:
            return axgroup(self.axes[val])
        return self.axes[val]

    def text(self, *args, **kwargs):
        """
        Place text on all axes in the group.
        """
        for ax, kws in self._disperse_kwargs(**kwargs):
            ax.text(*args, **kwargs)

    def annotate(self, *args, **kwargs):
        """
        Annotate all axes in the group.
        """
        for ax, kws in self._disperse_kwargs(**kwargs):
            ax.annotate(*args, **kwargs)

    def xgrid(self, b=None, **kwargs):
        """
        Set the xgrid for all axes in the group.
        """
        for ax, kws in self._disperse_kwargs(**kwargs):
            ax.xaxis.grid(b, **kws)

    def ygrid(self, b=None, **kwargs):
        """
        Set the ygrid for all axes in the group.
        """
        for ax, kws in self._disperse_kwargs(**kwargs):
            ax.yaxis.grid(b, **kws)

    def axhspan(self, *args, **kwargs):
        """
        Add a horizontal span(rectangle) across the axes in the group.
        """
        for ax, kws in self._disperse_kwargs(**kwargs):
            ax.axhspan(*args, **kws)

    def axvspan(self, *args, **kwargs):
        """
        Add a vertical span(rectangle) across the axes in the group.
        """
        for ax, kws in self._disperse_kwargs(**kwargs):
            ax.axvspan(*args, **kws)

    def axhline(self, y=0, *args, **kwargs):
        """
        Add a horizontal line across the axes in the group.
        """
        for ax, kws in self._disperse_kwargs(**kwargs):
            ax.axhline(y, *args, **kws)

    def axvline(self, x=0, *args, **kwargs):
        """
        Add a vertical line across the axes in the group.
        """
        for ax, kws in self._disperse_kwargs(**kwargs):
            ax.vln(x, *args, **kws)

    def fill_between(self, *args, **kwargs):
        """
        Make filled polygons between two curves for all axes in the group.
        """
        for ax, kws in self._disperse_kwargs(**kwargs):
            ax.fill_between(*args, **kws)

    def fill_betweenx(self, *args, **kwargs):
        """
        Make filled polygons between two horizontal curves for all
        axes in the group.
        """
        for ax, kws in self._disperse_kwargs(**kwargs):
            ax.fill_betweenx(*args, **kws)

    def set_xscale(self, val):
        """
        Set the xscale {'linear', 'log', 'symlog'} for each axes in the group.
        """
        for ax in self:
            ax.set_xscale(val)

    def set_yscale(self, val):
        """
        Set the yscale {'linear', 'log', 'symlog'} for each axes in the group.
        """
        for ax in self:
            ax.set_yscale(val)

    def set_xlim(self, *args, **kwargs):
        """
        Set the xlimits for each axes in the group.
        """
        for ax, kws in self._disperse_kwargs(**kwargs):
            ax.set_xlim(*args, **kws)

    def set_ylim(self, *args, **kwargs):
        """
        Set the ylimits for each axes in the group.
        """
        for ax, kws in self._disperse_kwargs(**kwargs):
            ax.set_ylim(*args, **kws)

    def set_xticks(self, *args, **kwargs):
        """
        Set the xticks for each axes in the group.
        """
        for ax, kws in self._disperse_kwargs(**kwargs):
            ax.set_xticks(*args, **kws)

    def set_yticks(self, *args, **kwargs):
        """
        Set the yticks for each axes in the group.
        """
        for ax, kws in self._disperse_kwargs(**kwargs):
            ax.set_yticks(*args, **kws)

    def set_title(self, lbls, *args, **kwargs):
        """
        Set the ylabel for each axes in the group.

        `lbls` can be a list of labels the same length as the axgroup,
        or if it is a string(or length 1 list) it specifies a single
        label that will be placed on each axis.

        """
        if lbls.__class__ is str:
            lbls = [lbls]
        elif lbls.__class__ is not list:
            lbls = list(lbls)
        if len(lbls) == 1:
            lbls = lbls * len(self)
        for ax, lbl in zip(self, lbls):
            ax.set_title(lbl, *args, **kwargs)

    def set_ylabel(self, lbls, *args, **kwargs):
        """
        Set the ylabel for each axes in the group.

        `lbls` can be a list of labels the same length as the axgroup,
        or if it is a string(or length 1 list) it specifies a single
        label that will be placed on each axis.

        """
        if lbls.__class__ is str:
            lbls = [lbls]
        elif lbls.__class__ is not list:
            lbls = list(lbls)
        if len(lbls) == 1:
            lbls = lbls * len(self)
        for ax, lbl in zip(self, lbls):
            ax.set_ylabel(lbl, *args, **kwargs)

    def set_xlabel(self, lbls, *args, **kwargs):
        """
        Set the xlabel for each axes in the group.

        `lbls` can be a list of labels the same length as the axgroup,
        or if it is a string(or length 1 list) it specifies a single
        label that will be placed on each axis.

        """
        if lbls.__class__ is str:
            lbls = [lbls]
        elif lbls.__class__ is not list:
            lbls = list(lbls)
        if len(lbls) == 1:
            lbls = lbls * len(self)
        for ax, lbl in zip(self, lbls):
            ax.set_xlabel(lbl, *args, **kwargs)

    def plot(self, *args, **kwargs):
        """
        Plot data on all axes in the group.
        """
        for ax, kws in self._disperse_kwargs(**kwargs):
            ax.plot(*args, **kwargs)

    def loglog(self, *args, **kwargs):
        """
        Loglog plot on all axes in the group.
        """
        for ax, kws in self._disperse_kwargs(**kwargs):
            ax.loglog(*args, **kwargs)

    def semilogx(self, *args, **kwargs):
        """
        Semilogx plot on all axes in the group.
        """
        for ax, kws in self._disperse_kwargs(**kwargs):
            ax.semilogx(*args, **kwargs)

    def semilogy(self, *args, **kwargs):
        """
        Semilogy plot on all axes in the group.
        """
        for ax, kws in self._disperse_kwargs(**kwargs):
            ax.semilogy(*args, **kwargs)

    def offset_text(self, x, y, s, offset=(0, 0), *args, **kwargs):
        """
        Place offset_text in all axes in the group.
        """
        for ax, kws in self._disperse_kwargs(**kwargs):
            ax.offset_text(x, y, s, offset=offset, *args, **kwargs)

    def hide_xticklabels(self, exclude=None, hide=True):
        """
        Hide the xticklabels of the axes in this group.

        Parameters
        ----------
        exclude : list of axes or an axes
          These are excluded from hiding.

        hide : bool
          set hide=False to show these ticklabels.

        """
        axs = self
        if exclude is not None:
            axs = list(axs.to_set() - set(exclude))
        for ax in axs:
            pylab.setp(ax.get_xticklabels(), visible=(not hide))

    def hide_yticklabels(self, exclude=None, hide=True):
        """
        Hide the yticklabels of the axes in this group.

        Parameters
        ----------
        exclude : list of axes or an axes
          These are excluded from hiding.

        hide : bool
          set hide=False to show these ticklabels.

        """
        axs = self
        if exclude is not None:
            axs = list(axs.to_set() - set(exclude))
        for ax in axs:
            pylab.setp(ax.get_yticklabels(), visible=(not hide))

    def hide(self, objs='xticklabels', ax=None):
        """
        Hide `objs` on all axes of this group * except* for those
        specified in `ax`.

        Parameters
        ----------
        objs :
            str {'xticklabels', 'yticklabels', 'minorxticks', 'minoryticks'}
          or a list of these.
        ax   :
            axes, optional (default: hide all)
               The axes(or list of axes) on which these items should
               not be hidden.

        Examples
        --------
        Hide the xticklabels on all axes except ax0:
            :
            hide('xticklabels', self.ax0)

        To hide all xticklabels, simply do:
           hide('xticklabels')

        See also
        --------
        antiset

        """
        if objs.__class__ is str:
            objs = [objs]
        types = {'x': ['xticklabels', 'minorxticks'],
                 'y': ['yticklabels', 'minoryticks']}
        for obj in objs:
            if ax.__class__ is str and ax == 'all':
                axs = self.flat
            else:
                if ax is None:
                    if obj in types['x'] and hasattr(self, '_xlabel_ax'):
                        ax = self._xlabel_ax
                    elif obj in types['y'] and hasattr(self, '_ylabel_ax'):
                        ax = self._ylabel_ax
                    else:  # This gives default behavior?
                        ax = []
                if not hasattr(ax, '__len__'):
                    ax = [ax]
                axs = list(self.to_set() - set(ax))
            for axn in axs:
                if obj == 'xticklabels':
                    pylab.setp(axn.get_xticklabels(), visible=False)
                elif obj == 'yticklabels':
                    pylab.setp(axn.get_yticklabels(), visible=False)
                elif obj == 'minorxticks':
                    pylab.setp(axn.xaxis.get_minorticklines(), visible=False)
                elif obj == 'minoryticks':
                    pylab.setp(axn.yaxis.get_minorticklines(), visible=False)
                else:
                    error

    def set(self, **kwargs):
        """
        Set an attribute for each axes in the group.
        """
        pylab.setp(self.ax.flatten(), **kwargs)

    def antiset(self, ax, **kwargs):
        # Some backwards compatability stuff:
        if 'xticklabels' in kwargs and kwargs['xticklabels'] == '':
            kwargs.pop('xticklabels')
            self.hide('xticklabels', ax)
        if 'yticklabels' in kwargs and kwargs['yticklabels'] == '':
            kwargs.pop('yticklabels')
            self.hide('yticklabels', ax)
        if 'minorxticks' in kwargs and not kwargs['minorxticks']:
            kwargs.pop('minorxticks')
            self.hide('minorxticks', ax)
        if 'minoryticks' in kwargs and not kwargs['minoryticks']:
            kwargs.pop('minoryticks', ax)
            self.hide('minoryticks', ax)

        if len(kwargs) == 0:
            return
        # The meat:
        if not hasattr(ax, '__len__'):
            ax = [ax]
        pylab.setp(list(set(self.ax.flatten()) - set(ax)), **kwargs)


class axSharer(object):

    """
    A class for handling sharing of axes.
    """

    def map_vals(self,):
        return set(self.map.flatten())

    def __init__(self, saxes, share_map=False):
        self.saxes = saxes
        self.map = np.zeros(saxes.n, dtype=np.uint16)
        self.map[:] = share_map
        self._share_ax = {}

    def __getitem__(self, ind):
        return self.map[ind]

    def __setitem__(self, ind, val):
        self.map[ind] = val

    def __call__(self, iv, ih):
        """
        Returns the 'prime' axes to be shared for the axes at
        grid-point (iv, ih).

        Parameters
        ----------
        (iv,ih) :
            The index of the axgrid for which you want the shareax.

        Returns
        -------
        shareax :
            :class:`axes`, or :class:`None`.
                  `None` if the axis does not share an axes, or one
                  has not yet been created that it matches.
        """
        mapVal = self.map[iv, ih]
        if not mapVal:  # mapVal==0 do not share axes.
            return
        elif mapVal in self._share_ax:
            # The mapVal is already in the _share_ax dictionary
            return self._share_ax[mapVal]
        else:
            axs = self.saxes.axes[self.map == mapVal]
            if np.any(axs):
                # An axis for this mapVal has been created. Add it to
                # the _share_ax dict.
                self._share_ax[mapVal] = axs[np.nonzero(axs)][0]
                return self._share_ax[mapVal]
            else:  # No axis exists yet for this mapVal.
                return


class axSpacer(object):

    """
    Defines the position and size of axes in either the horizontal or
    vertical direction.

    Parameters
    ----------
    axsize :
        array_like(n,float)
             An array specifying the size of each axes in inches.
    gap    :
        array_like(n+1,float)
             An array specifying the spacing in inches between
             axes. The first element is the distance from the
             left /bottom of the figure to the first axes, the last
             element is the distrance from the right /top of the figure
             to the last axes.
    vertical :
        bool (default: False)
               A flag specifying that this is a 'vertical' axSpacer
               (flips ordering of axes positions so that the first
               axes is at the top of the figure).

    """

    def __init__(self, axsize=[1, 1], gap=[.7, .2, .2], vertical=False):
        self.axsize = axsize
        self.gap = gap
        # self.units=units # Add support for units other than inches.
        self.vertical = vertical

    @property
    def axsize_(self,):
        """
        The figure -units axes sizes, array_like.
        """
        return self.axsize / self.totsize

    @axsize_.setter
    def axsize_(self, val):
        self.axsize = val * self.totsize

    @property
    def gap_(self,):
        """
        The figure -units gap between axes, array_like.
        """
        return self.gap / self.totsize

    @gap_.setter
    def gap_(self, val):
        self.gap = val * self.totsize

    @property
    def pos_(self,):
        """
        The figure -units position of the axes, array_like.
        """
        return self.pos / self.totsize

    @property
    def n(self):
        """
        The number of axes described by this axSpacer.
        """
        return len(self.axsize)

    def __len__(self,):
        return self.n

    @property
    def axsize(self,):
        """
        The axes size, in inches.
        """
        return self.__axsize

    @axsize.setter
    def axsize(self, val):
        self.__axsize = np.array(val)

    @property
    def gap(self):
        """
        The gap between axes, in inches.
        """
        return self.__gap

    @gap.setter
    def gap(self, val):
        self.__gap = np.array(val)

    def __iter__(self,):
        for pos, wid in zip(self.pos_, self.axsize_):
            yield pos, wid

    @property
    def pos(self):
        if self.vertical:
            return (np.cumsum(self.axsize + self.gap[:-1]) - self.axsize)[::-1]
        else:
            return np.cumsum(self.axsize + self.gap[:-1]) - self.axsize

    @property
    def totsize(self,):
        return self.axsize.sum() + self.gap.sum()

    @totsize.setter
    def totsize(self, val):
        self.__axsize *= val / self.totsize
        self.__gap *= val / self.totsize

    @property
    def frame(self,):
        """
        The bounding 'frame' around the axes, in inches.
        """
        return self.gap[[0, -1]]


def axvec2axSpacer(n, vec, vertflag, rel=False):
    """
    Returns an :
        class:`axSpacer` corresponding to the `n` axes based
    on the axes vector `vec`.

    Parameters
    ----------

    n :
        int
      The number of axes.

    vec :
        iterable(3)
      The (left/bottom, right/top,gap) surrounding and between the
      axes.

    vertflag :
        bool, optional (default: False)
      Specifies this is for vertical(True) or horizontal spacing.

    rel :
        iterable(`n`), optional
      This specifies the relative width of each of the axes. By
      default all axes are the same width.

    Returns
    -------
    axSpacer :
        :class:`axSpacer`
      The axes spacer object corresponding to the specified inputs.

    Notes
    -----

    The units of the returned axSpacer match that of the input `vec`.

    """
    if rel.__class__ is False.__class__ and not rel:
        # Default value.
        rel = np.ones(n)
    wd = (((vec[1] - vec[0]) + vec[2]) / n - vec[2]) * rel / rel.mean()
    gap = np.empty((len(wd) + 1), dtype=wd.dtype)
    gap[0] = vec[0]
    gap[1:-1] = vec[2]
    gap[-1] = vec[1]
    return axSpacer(wd, gap, vertflag)


class axPlacer(object):

    """
    Axes placers contain the information on where axes objects should
    be placed in a figure object.

    Parameters
    ----------
    vSpacer :
        :class:`axSpacer`
              The vertical axes spacer object.
    hSpacer :
        :class:`axSpacer`
              The horizontal axes spacer object.
    """

    def __init__(self, vSpacer, hSpacer):
        if not vSpacer.vertical:
            raise Exception("The vSpacer must have property `vertical`=True")
        self.vSpacer = vSpacer
        self.hSpacer = hSpacer

    @property
    def n(self,):
        return self.vSpacer.n, self.hSpacer.n

    def __call__(self, iv, ih):
        return (self.hSpacer.pos_[ih],
                self.vSpacer.pos_[iv],
                self.hSpacer.axsize_[ih],
                self.vSpacer.axsize_[iv])

    @property
    def figSize(self,):
        """
        Width x Height in inches.
        """
        return (self.hSpacer.totsize, self.vSpacer.totsize)

    def __iter__(self,):
        for iv in range(self.n[0]):
            for ih in range(self.n[1]):
                yield self(iv, ih)

    @property
    def axes_positions(self,):
        """
        Returns a list of location tuples(left, bottom, width,
        height) for axes objects.
        """
        return list(self.__iter__())


def simpleAxSpacer(n, axsize, gap, frm=np.array([.5, .5]), vertical=False):
    """
    calculates the width (or height) of a figure with *n * subplots.
    Specify the width (height) of each subplot with *ax[0] *, the space
    between subplots with *ax[1] *, and the left/right (bottom/top)
    spacing with *frame[0] */*frame[1]*.

    See also:
        saxes, axes, calcAxesSize
    """
    gap = np.ones(n + 1) * gap
    gap[0] = frm[0]
    gap[-1] = frm[1]
    return axSpacer(np.ones(n) * axsize, gap, vertical=vertical)


class saxes(axgroup):

    """
    Create an axes group object using S(uper)AXES.

    Parameters
    ----------

    Use keyword argument fig =<figure object> to specify the figure in
    which to create the axes.

    Notes
    -----
    n =(3,4) to set up a 3x4 array of axes.

    n =(3,[1,1,1,.5]) to set up a 3x4 array of axes with the last
    column half the width of the others.

    n =([1,1,1.5],[1,1,1,.5]) to set up a 3x4 array of axes with the
    last row 1.5 times as tall and the last column half as wide.

    h =(.1,.9,.05) to create the horizontal frame box at .1 and .9, with
    gaps of .05 between each axes.

    v =(.1,.9,.05) similarly for the vertical frame/gap.

    drawax =L, where L is a logical array of the axes you actually want to
    draw(default is all of them).

    sharex =True, chooses whether the axes share an xaxis.
    sharey =True, chooses whether the axes share a yaxis.

    """

    def __init__(self, axPlacer, **kwargs):
        self.axes = np.empty(axPlacer.n, dtype='object')
        self.linewidth = kwargs.pop('linewidth', rcParams['axes.linewidth'])
        self.axPlacer = axPlacer
        self.sharex = axSharer(self, kwargs.pop('sharex', False))
        self.sharey = axSharer(self, kwargs.pop('sharey', False))
        self.drawax = np.ones(axPlacer.n, dtype='bool')
        for key in kwargs:
            setattr(self, key, kwargs[key])

    @property
    def n(self,):
        return self.axPlacer.n

    def set_ylabel_pos(self, pos, axs=None,):
        if axs is None:
            axs = self.ax.flatten()
        for ax in axs:
            ax.yaxis.set_label_coords(pos, 0.5)

    def xlabel(self, *args, **kwargs):
        """
        This is different than 'set_xlabel' because it sets the xlabel
        only for the 'self._xlabel_ax'.
        """
        self._xlabel_ax.set_xlabel(*args, **kwargs)

    def ylabel(self, *args, **kwargs):
        """
        This is different than 'set_ylabel' because it sets the ylabel
        only for the 'self._ylabel_ax'.
        """
        self._ylabel_ax.set_ylabel(*args, **kwargs)

    def _iter_axinds(self,):
        for iv in range(self.n[0]):
            for ih in range(self.n[1]):
                yield iv, ih

    def drawall(self, **kwargs):
        if not self.n == self.drawax.shape:
            self.drawax = np.ones(self.n, dtype='bool')
        if 'lw' in kwargs:
            kwargs['linewidth'] = kwargs.pop('lw', self.linewidth)
        if 'linewidth' not in kwargs:
            kwargs['linewidth'] = self.linewidth
        else:
            self.linewidth = kwargs['linewidth']

        inter = pylab.isinteractive()
        pylab.interactive(False)
                          # wait to draw the axes, until they've all been
                          # created.
        for iv, ih in self._iter_axinds():
            if self.drawax[iv, ih]:
                self.ax[iv, ih] = axes(self.axPlacer(iv, ih),
                                       sharex=self.sharex(iv, ih),
                                       sharey=self.sharey(iv, ih),
                                       **kwargs)
                self.ax[iv, ih].hold(True)
        self._xlabel_ax = self.ax[-1, 0]
        self._ylabel_ax = self._xlabel_ax
        pylab.interactive(inter)
        pylab.draw_if_interactive()
        return self.ax


class figobj(axgroup):

    """
    A base class for axes -grid figures.

    Parameters
    ----------

    fignum   :
        int
      Figure number

    nax      :
        tuple(2 ints)
      Shape of the axes grid.

    saxparams  :
        dict
      input arguments to saxes.

    axsize     :
        tuple(2 floats)
      specifies the size of the axes [vertical, horizontal] in inches.

    frame      :
        iterable(4)
      specifies the frame around the axes [bottom, top,left,right], in
      inches (default: [.6, .3,1,.3]).

    gap        :
        tuple(2 floats) or float
      specifies the gap between axes [vertical, horizontal], in inches
      (default: [.2, .2]).

    hrel       :
        iterable
      specifies the relative horizontal size of each axes.

    vrel       :
        iterable
      specifies the relative vertical size of each axes.

    """
    nax = (1, 1)

    def savefig(self, *args, **kwargs):
        self.fig.savefig(*args, **kwargs)
        #self.meta.write(args[0])

    def initFig(self, fignum, **kwargs):
        figkws = {}
        figkws['figsize'] = kwargs.pop('figsize', self.saxes.axPlacer.figSize)
        self.fig = pylab.figure(fignum, **figkws)
        ff = np.array([0, .425])  # A fudge factor.
        if figkws['figsize'] is not None and \
                np.all(self.fig.get_size_inches() != figkws['figsize']):
            self.fig.set_size_inches(figkws['figsize'] + ff, forward=True)
        self.clf = self.fig.clf
        self.clf()
        if 'title' in kwargs:
            self.fig.canvas.set_window_title(
                'Fg%d: ' % (self.fig.number) + kwargs['title'])

    def __init__(self, fignum=None, nax=[1, 1], axsize=[3, 3],
                 frame=[.6, .3, 1, .3], gap=[.4, .4],
                 sharex=False, sharey=False,
                 **kwargs):
        gap = bf.pair(gap)
        axsize = bf.pair(axsize)
        vSpacer = simpleAxSpacer(nax[0],
                                 axsize[0],
                                 gap[0],
                                 frm=frame[:2],
                                 vertical=True)
        hSpacer = simpleAxSpacer(nax[1],
                                 axsize[1],
                                 gap[1],
                                 frm=frame[2:],
                                 vertical=False)
        placer = axPlacer(vSpacer, hSpacer)
        self.saxes = saxes(placer, sharex=sharex, sharey=sharey,)
        self.initFig(fignum, **kwargs)
        self.saxes.drawall()
        axgroup.__init__(self, self.saxes.axes)

    def __enter__(self,):
        return self

    def __exit__(self, type, value, trace):
        pass

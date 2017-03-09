import numpy as np
from scipy.stats import nanmean
import matplotlib as mpl
from string import lowercase
from ..tools.misc import nans, nans_like

try:
    numeric_types = (int, long, float, complex)
except NameError:
    # Python 3 doesn't have `long`
    numeric_types = (int, float, complex)

transforms = mpl.transforms
rcParams = mpl.rcParams


def skip_ticklabels(ax, rep=2, offset=0, axis='x', force=True):
    """
    hide the ticklabels on ticks except for every *rep*'th tick.
    *offset* specifies an offset, of tick to start on.
    *axis* specifies the x (default) or y axis.
    when *force* is True (default) this function turns on every *rep*'th tick.
    """
    if axis == 'x':
        tks = ax.get_xticklabels()
    else:
        tks = ax.get_yticklabels()
    for idx, tk in enumerate(tks):
        if np.mod(idx + offset, rep):
            tk.set_visible(False)
        elif force:
            tk.set_visible(True)


def pair(val):
    """
    Return the input as a list of two values if it is a scalar.
    """
    if np.isscalar(val):
        return [val] * 2
    if len(val) == 1:
        return [val[0], val[0]]
    return val


def cpcolor(*args, **kwargs):
    """
    cpcolor(x,y,c)

    makes a pseudocolor plot of the data in c

    Optional keyword arguments:
    fixgaps=True
    threshx=inf
    threshy=inf

    """
    threshx = np.inf
    threshy = np.inf
    fixgaps = True
    argind = 0
    if isinstance(args[0], mpl.axes.Axes):
        # Data is the second (1) element of args... (see below)
        argind += 1
        ax = args[0]
    elif ('ax' in kwargs) or ('axes' in kwargs) or ('parent' in kwargs):
        if 'parent' in kwargs:
            ax = kwargs.pop('parent')
        elif 'ax' in kwargs:
            ax = kwargs.pop('ax')
        else:
            ax = kwargs.pop('axes')
    else:
        ax = mpl.pylab.gca()

    if 'fixgaps' in kwargs:
        fixgaps = kwargs.pop('fixgaps')
    if 'threshx' in kwargs:
        threshx = kwargs.pop('threshx')
    if 'threshy' in kwargs:
        threshy = kwargs.pop('threshy')
    if 'clim' in kwargs:
        clm = kwargs.pop('clim')
        kwargs['vmin'] = clm[0]
        kwargs['vmax'] = clm[1]

    if len(args) - argind == 1:
        dat = args[0 + argind]
        x = np.arange(dat.shape[1])
        y = np.arange(dat.shape[0])
    else:
        x = args[0 + argind]
        y = args[1 + argind]
        dat = args[2 + argind]

    dfx = np.diff(x, 1, 0).astype('double')
    dx = dfx
    gd = abs(dx) <= 3 * nanmean(abs(dx))
    while not gd.all():
        dx = dx[gd]
        gd = abs(dx) <= 3 * nanmean(abs(dx))

    dx = nanmean(dx).astype('double')

    dfy = np.diff(y, 1, 0).astype('double')
    dy = dfy
    gd = abs(dy) <= 3 * nanmean(abs(dy))
    while not gd.all():
        dy = dy[gd]
        gd = abs(dy) <= 3 * nanmean(abs(dy))

    dy = nanmean(dy).astype('double')

    N = dat.shape[1] + sum(abs(dfx) > 3 * abs(dx)) * fixgaps
    datn = nans([dat.shape[0], N + 1])
    xn = nans([N + 1, 1])
    if fixgaps:
        if abs(dfx[0]) < 3 * abs(dx) or abs(dfx[0]) <= threshx:
            xn[0] = x[0] - dfx[0] / 2
        else:
            xn[0] = x[0] - dx
        datn[:, 0] = dat[:, 0]
        c = 0
        for i0 in range(0, len(dfx)):
            c = c + 1
            if abs(dfx[i0]) <= (3 * abs(dx)) or \
                    np.isnan(dfx[i0]) or abs(dfx[i0]) <= threshx:
                xn[c] = x[i0] + dfx[i0] / 2
                datn[:, c] = dat[:, i0 + 1]
            else:
                xn[c] = x[i0] + dx
                datn[:, c] = nans_like(dat[:, 0])
                c = c + 1
                xn[c] = x[i0] + dfx[i0] - dx
                datn[:, c] = dat[:, i0]
    else:
        datn[:, 1:N] = dat
        xn[2:N] = x[2:N] - dfx / 2

    xn[0] = x[0] - dx / 2
    xn[-1] = x[-1] + dx / 2

    N = datn.shape[0] + sum(abs(dfy) > 3 * abs(dy)) * fixgaps
    datn2 = nans([N + 1, datn.shape[1]])
    yn = nans([N + 1, 1])
    if fixgaps:
        if abs(dfy[0]) < 3 * abs(dy) or abs(dfy[0]) <= threshy:
            yn[0] = y[0] - dfy[0] / 2
        else:
            yn[0] = y[0] - dy
        datn2[0, :] = datn[0, :]
        c = 0
        for i0 in range(0, len(dfy)):
            c = c + 1
            if abs(dfy[i0]) <= (3 * abs(dy)) or \
                    np.isnan(dfy[i0]) or abs(dfy[i0]) <= threshy:
                yn[c] = y[i0] + dfy[i0] / 2
                datn2[c, :] = datn[i0 + 1, :]
            else:
                yn[c] = y[i0] + dy
                datn2[c, :] = nans_like(datn[0, :])
                c = c + 1
                yn[c] = y[i0] + dfy[i0] - dy
                datn2[c, :] = datn[i0, :]
    else:
        datn2[1:N, :] = datn
        yn[2:N] = y[2:N] - dfy / 2

    yn[0] = y[0] - dy / 2
    yn[-1] = y[-1] + dy / 2

    datm = np.ma.array(datn2, mask=np.isnan(datn2))

    [mx, my] = np.meshgrid(xn, yn)

    mx = np.ma.array(mx, mask=np.isnan(mx))
    my = np.ma.array(my, mask=np.isnan(my))

    # mx=xn
    # my=yn

    hndl = ax.pcolormesh(mx, my, datm, shading='flat', **kwargs)
    hndl.set_rasterized(True)
    mpl.pylab.draw_if_interactive()
    return hndl


def cbar(peer, mappable=None, place='right',
         axsize=.023, axgap=.02, lims=None, **kwargs):
    xtkdir = mpl.rcParams['xtick.direction']
    mpl.rcParams['xtick.direction'] = 'in'
    ytkdir = mpl.rcParams['ytick.direction']
    mpl.rcParams['ytick.direction'] = 'in'
    bx = mpl.pylab.getp(peer, 'position')
    ext = bx.extents
    axp = np.zeros(4)
    orient = 'vertical'
    if place == 'right':
        axp[0] = ext[2] + axgap
        axp[1] = ext[1]
        axp[2] = axsize
        axp[3] = bx.height / 2
    elif place == 'over':
        axp[0] = ext[0] + bx.width / 2
        axp[1] = ext[3] + axgap
        axp[2] = bx.width / 2
        axp[3] = axsize
        orient = 'horizontal'
        lblpos = 'top'
    elif hasattr(place, '__iter__'):
        axp = place
        if axp[3] < axp[2]:
            orient = 'horizontal'

    if 'orient' in kwargs:
        orient = kwargs.pop('orient')

    if 'axdict' in kwargs:
        axd = kwargs.pop('axdict')
    else:
        axd = {}
    ax2 = {}
    if 'linewidth' in kwargs:
        axd['linewidth'] = kwargs.pop('linewidth')
    if 'ticklabels' in kwargs:
        ax2['yticklabels'] = kwargs.pop('ticklabels')

    if 'fontsize' in kwargs:
        ax2['fontsize'] = kwargs.pop('fontsize')

    tmp = mpl.pyplot.axes(axp, **axd)
    if mappable is None:
        hndl = mpl.pylab.colorbar(cax=tmp, orientation=orient, **kwargs)
    else:
        hndl = mpl.pylab.colorbar(
            mappable, cax=tmp, orientation=orient, **kwargs)

    if 'fontsize' in ax2:
        if orient == 'vertical':
            mpl.pylab.setp(tmp.get_yticklabels(), fontsize=ax2.pop('fontsize'))
        else:
            mpl.pylab.setp(tmp.get_xticklabels(), fontsize=ax2.pop('fontsize'))

    tmp.set(**ax2)
    mpl.rcParams['xtick.direction'] = xtkdir
    mpl.rcParams['ytick.direction'] = ytkdir

    if place == 'right':
        pass
    elif place == 'over':
        tmp.xaxis.set_label_position('top')
        tmp.xaxis.set_ticks_position('top')
    return hndl


def labelax(peer, str, place='right', **kwargs):
    if place == 'right':
        place = (1.025, .6)
    elif place == 'over':
        place = (.48, 1.1)
        if 'horizontalalignment' not in kwargs:
            kwargs['horizontalalignment'] = 'right'

    hndl = peer.text(
        place[0], place[1], str, transform=peer.transAxes, **kwargs)

    return hndl


def errorshadex(peer, x, y, xerr, ecolor=None,
                ealpha=.5, color='b', zorder=0, **kwargs):
    """
    Plot a line with a shaded region for error.
    """
    if ecolor is None:
        ecolor = color
    peer.plot(x, y, color=color, zorder=zorder, **kwargs)
    peer.fill_betweenx(
        y, x - xerr, x + xerr, alpha=ealpha, color=ecolor, zorder=zorder - 1)


def vecs2fillvec(y1, y2, meanstd=False, x=None, axis=0):
    """
    *y1* and *y2* should be the ranges.
    This function will then flip y2 and tack it onto y1.

    For meanstd=True
    *y1* should be the mean, and *y2* the std.
    This function will add and subtract y2 from y1.
    """

    if meanstd:
        y1, y2 = y1 + y2, y1 - y2

    if x is None:
        return np.concatenate((y1, y2[::-1], y1[[0]]), axis)
    else:
        return (np.concatenate((y1, y2[::-1], y1[[0]]), axis),
                np.concatenate((x, x[::-1], x[[0]]), axis))


def calcFigSize(n, ax=np.array([1, 0]), frm=np.array([.5, .5]), norm=False):
    """
    sz,vec = calcFigSize(n,ax,frame) calculates the width (or height)
    of a figure with *n* subplots.  Specify the width (height) of each
    subplot with *ax[0]*, the space between subplots with *ax[1]*, and
    the left/right (bottom/top) spacing with *frame[0]*/*frame[1]*.

    calcFigSize returns *sz*, a scalar, which is the width (or height)
    the figure should, and *vec*, which is the three element vector
    for input to saxes.

    See also: saxes, axes, calcAxesSize
    """
    if hasattr(n, '__iter__'):
        n = np.sum(n)
    sz = n * ax[0] + (n - 1) * ax[1] + frm[0] + frm[1]
    frm = np.array(frm)
    ax = np.array(ax)
    if not (norm.__class__ is False.__class__ and not norm):
        # This checks that it is not the default.
        frm = frm / sz * norm
        ax = ax / sz * norm
        sz = norm
    v = np.array([frm[0], (sz - frm[1]), ax[1]]) / sz
    return sz, v


def calcAxesSize(n, totsize, gap, frame):
    """
    Calculate the width of each axes, based on the total figure width
    (height) *totsize*, the desired frame size, *frame*, the desired
    spacing between axes *gap* and the number of axes *n*.

    calcAxesSize returns the size each axes should be, along with the
    three element vector for input to saxes.

    See also: saxes, axes, calcFigSize
    """
    if hasattr(gap, '__len__'):
        gtot = np.sum(gap[:n])
    else:
        gtot = gap * (n - 1)
    axsz = (totsize - frame[0] - frame[1] - gtot) / n
    sz, v = calcFigSize(n, [axsz, gap], frame, False)
    return axsz, v


def calcAxesSpacer(n, totsize, gap, frame):
    """
    Calculate the width of each axes, based on the total figure width
    (height) *totsize*, the desired frame size, *frame*, the desired
    spacing between axes *gap* and the number of axes *n*.

    calcAxesSize returns the size each axes should be, along with the
    three element vector for input to saxes.

    See also: saxes, axes, calcFigSize
    """
    if hasattr(gap, '__len__'):
        gtot = np.sum(gap[:n])
    else:
        gtot = gap * (n - 1)
    axsz = (totsize - frame[0] - frame[1] - gtot) / n
    sz, v = calcFigSize(n, [axsz, gap], frame, False)
    return axsz, v


def axvec2axpos(n, vec, vertflag=False, rel=False):
    """
    calculates the positions for the `n` axes, based on the axes
    vector `vec`.

    Parameters
    ----------
    n : int
        The number of frames to make.
    vec : iterable(3)
          The (left/bottom,right/top,gap) surrounding and between
          the axes.
    vertflag : bool, optional (default: False)
               Specifies this is for vertical (True) or horizontal
               spacing.
    rel : iterable(`n`), optional
          This specifies the relative width of each of the axes. By
          default all axes are the same width.

    Returns
    -------
    pos : iterable(`n`)
          specifies the position of each axes.
    wd : iterable(`n`)
         Specifies the width of each axes. Each entry will be the same
         unless `rel` is specified.

    Notes
    -----

    The units of the returned variables match that of the input `vec`.

    """

    if rel.__class__ is False.__class__ and not rel:
        # Default value.
        rel = np.ones(n)
    wd = (((vec[1] - vec[0]) + vec[2]) / n - vec[2]) * rel / rel.mean()
    if vertflag:
        pos = vec[1] - (wd + vec[2]).cumsum().reshape((n, 1)) + vec[2]
        wd = wd.reshape((n, 1))
    else:
        pos = vec[0] + (wd + vec[2]).cumsum().reshape((1, n)) - wd - vec[2]
        wd = wd.reshape((1, n))
    return pos, wd


def get_transform(ax, trans):
    if trans.__class__ is not str:
        return trans
    if hasattr(ax, trans):
        return getattr(ax, trans)
    return getattr(ax, 'trans' + trans)


def offset_text(ax, x, y, s, offset=(0, 0), transform=None, **kwargs):
    """
    Add text to an axes offset from a location.

    *offset* specifies the offset (in points) from the selected *pos*.
    If *offset* is a two element list or tuple, it specifies a
    different offset in the x and y directions.

    Returns the text object.

    By default the *x*,*y* positions are in data coordinates.  Specify
    a different 'transform' to change this.

    """
    if transform is None:
        transform = ax.transData
    else:
        transform = get_transform(ax, transform)
    if (offset.__class__ is list) or (offset.__class__ is tuple):
        osx = offset[0] / 72.
        osy = offset[1] / 72.
    else:
        osx = offset / 72.
        osy = offset / 72.
    trfrm = transform + transforms.ScaledTranslation(osx,
                                                     osy,
                                                     ax.figure.dpi_scale_trans)
    return ax.text(x, y, s, transform=trfrm, **kwargs)


def annoteCorner(ax, s, pos='ll', offset=10, **kwargs):
    """
    annotate a corner of an axes with a string.

    Parameters
    ----------
    *ax* : axes
           is the axes into which to place the annotation.
    *s* : str
          is the text to place in the corner.
    *pos* : str {'ll','ul','lr','ur'}, tuple(2)
            The tuple form specifies the text locaiton in axes coordinates.

    *offset* : tuple(1 or 2)
               Specifies the offset from the selected *pos* (in points).

    Returns
    -------
    t : text artist.
        Also, it creates a 'corner_label' attribute in the axes, with
        this text artist.

    Notes
    -----
    If the string form of *pos* is used then the sign of *offset* is
    always such that it shifts the string toward the center.If it is a
    two element tuple or string, it specifies a different offset in
    the x and y directions.

    """
    prm = {}
    yp = 0.0
    xp = 0.0
    prm['va'] = 'baseline'
    prm['ha'] = 'left'
    # prm['fontsize']='medium'
    if (offset.__class__ is list) or (offset.__class__ is tuple):
        osx = offset[0]
        osy = offset[1]
    else:
        osx = offset
        osy = offset
    if pos.__class__ is str:
        if pos[0] == 'u':
            osy = -osy
            yp = 1.
            prm['va'] = 'top'
        if pos[1] == 'r':
            osx = -osx
            xp = 1.
            prm['ha'] = 'right'
    else:
        xp = pos[0]
        yp = pos[1]
    prm['offset'] = (osx, osy)
    prm['transform'] = ax.transAxes

    for key in prm:
        if key not in kwargs:
            kwargs[key] = prm[key]
    ax.corner_label = offset_text(ax, xp, yp, s, **kwargs)
    return ax.corner_label


def shadex(ax, x, y=[0, 1], transform='DataXAxesY', label='_nolegend_',
           zorder=-100, color='k', alpha=0.2, edgecolor='none', **kwargs):
    transform = get_transform(ax, transform)
    ax.fill_between(x, y[0], y[1], label=label, transform=transform,
                    zorder=zorder, color=color, alpha=alpha,
                    edgecolor=edgecolor, **kwargs)


def shadey(ax, y, x=[0, 1], transform='AxesXDataY', label='_nolegend_',
           zorder=-100, color='k', alpha=0.2, edgecolor='none', **kwargs):
    transform = get_transform(ax, transform)
    ax.fill_betweenx(y, x[0], x[1], label=label, transform=transform,
                     zorder=zorder, color=color, alpha=alpha,
                     edgecolor=edgecolor, **kwargs)


def _vln(ax, x, y=[0, 1], transform='DataXAxesY', label='_nolegend_',
         color='k', linewidth=rcParams['axes.linewidth'], **kwargs):
    if isinstance(x, numeric_types):
        x = [x]
    transform = get_transform(ax, transform)
    for xnow in x:
        ax.plot([xnow, xnow], y, transform=transform, label=label,
                color=color, linewidth=linewidth, **kwargs)


def _hln(ax, y, x=[0, 1], transform='AxesXDataY', **kwargs):
    if 'label' not in kwargs:
        kwargs['label'] = '_nolegend_'
    if 'color' not in kwargs:
        kwargs['color'] = 'k'
    if 'linewidth' not in kwargs and 'lw' not in kwargs:
        kwargs['lw'] = rcParams['axes.linewidth']
    if isinstance(y, numeric_types):
        y = [y]
    transform = get_transform(ax, transform)
    for ynow in y:
        ax.plot(x, [ynow, ynow], transform=transform, **kwargs)


def _setaxesframe(ax, str):
    str = np.array(list(str))
    if any(str == 't') and any(str == 'b'):
        ax.xaxis.set_ticks_position('both')
        ax.spines['top'].set_visible(True)
        ax.spines['bottom'].set_visible(True)
    elif any(str == 't'):
        ax.xaxis.set_ticks_position('top')
        ax.xaxis.set_label_position('top')
        ax.spines['top'].set_visible(True)
        ax.spines['bottom'].set_visible(False)
    elif any(str == 'b'):
        ax.xaxis.set_ticks_position('bottom')
        ax.xaxis.set_label_position('bottom')
        ax.spines['top'].set_visible(False)
        ax.spines['bottom'].set_visible(True)
    else:
        ax.xaxis.set_ticks_position('none')
        ax.spines['top'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.xaxis.set_ticklabels('')

    if any(str == 'l') and any(str == 'r'):
        ax.yaxis.set_ticks_position('both')
        ax.spines['left'].set_visible(True)
        ax.spines['right'].set_visible(True)
    elif any(str == 'l'):
        ax.yaxis.set_ticks_position('left')
        ax.yaxis.set_label_position('left')
        ax.spines['left'].set_visible(True)
        ax.spines['right'].set_visible(False)
    elif any(str == 'r'):
        ax.yaxis.set_ticks_position('right')
        ax.yaxis.set_label_position('right')
        ax.spines['left'].set_visible(False)
        ax.spines['right'].set_visible(True)
    else:
        ax.yaxis.set_ticks_position('none')
        ax.spines['left'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.yaxis.set_ticklabels('')
        # for tk in ax.yaxis.get_ticklabels


def alphNumAxes(self, vals=lowercase, prefix=None, suffix=None, **kwargs):
    """
    Label the axes with alphanumeric characters.

    *axs* are the axes over which to add labels to.  vals* should be a
    *string or list of strings to annotate the axes with.  It defaults
    *to string.lowercase prefix* and *suffix* are strings that can be
    *placed before and after each val. e.g.: prefix='(' and suffix=')'
    *will wrap the annotations in parenthesis.

    By default, this function calls annoteCorner on its
    axes.ax.flatten(), and uses

    See also: annoteCorner, string
    """
    if suffix is None:
        suffix = ')'
    if prefix is None:
        prefix = ''
    corner_labels = np.empty(self.size, 'O')
    for idx, ax in enumerate(self):
        corner_labels[idx] = ax.annoteCorner(
            prefix + vals[idx] + suffix, **kwargs)

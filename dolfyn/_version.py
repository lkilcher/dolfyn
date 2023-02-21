__version__ = '1.2.1'
__prog_name__ = 'DOLfYN'
__version_date__ = 'Feb-20-2023'


def ver2tuple(ver):
    out = []
    if '-' in __version__:
        ver, pre_rel = ver.split('-')
    else:
        pre_rel = None
    for val in ver.split('.'):
        val = int(val)
        out.append(val)
    if pre_rel is not None:
        return tuple(out + [pre_rel])
    else:
        return tuple(out)


version_info = ver2tuple(__version__)

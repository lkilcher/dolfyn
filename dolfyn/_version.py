__version__ = '0.13.0'
__prog_name__ = 'DOLfYN'
__version_date__ = 'Aug-10-2021'


def ver2tuple(ver):
    out = []
    for val in ver.split('.'):
        val = int(val)
        out.append(val)
    return tuple(out)


version_info = ver2tuple(__version__)

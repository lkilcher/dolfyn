__version__ = '0.11.0'
__prog_name__ = 'DOLfYN'
__version_date__ = 'April-23-2019'


def ver2tuple(ver):
    if isinstance(ver, tuple):
        return ver
    # ### Previously used FLOATS for 'save-format' versioning.
    # Version 1.0: underscore ('_') handled inconsistently.
    # Version 1.1: '_' and '#' handled consistently in group naming:
    # '#' is for groups that should be excluded, unless listed explicitly.
    # '##' and ending with '##' is for specially handled groups.
    # Version 1.2: now using time_array.
    #         '_' is for essential groups.
    # Version 1.3: Now load/unload is fully symmetric (needed for __eq__ tests)
    #         Added _config_type to i/o.
    if isinstance(ver, (float, int)):
        return (0, int(ver), int(round(10 * (ver % 1))))
    # ### Now switched to use pkg_version STRING.
    # Switch to pkg_version STRING (pkg_version 0.6)
    # Now 'old versions' become '0.x.y'
    # ver becomes a tuple.
    out = []
    for val in ver.split('.'):
        try:
            val = int(val)
        except ValueError:
            pass
        out.append(val)
    return tuple(out)


version_info = ver2tuple(__version__)

import numpy as np
from dolfyn.h5.data.base_legacy import config as LegacyConfigType


def array_equiv(a, b):
    try:
        np.testing.assert_equal(a, b)
    except AssertionError:
        return False
    return True


def compare_new2old(new, old):
    out = True
    for ky in new:
        o_ky = ky
        if o_ky in old and isinstance(old[o_ky], LegacyConfigType):
            if not compare_config(new[ky], old[o_ky]):
                print("---> config group '{}' does not match <---".format(ky))
                out = False
        elif isinstance(new[ky], dict):
            if not compare_new2old(new[ky], old):
                print("---> group '{}' does not match <---".format(ky))
                out = False
        elif o_ky in old:
            if array_equiv(new[ky], old[o_ky]):
                #print("{} matches.".format(ky))
                pass
            else:
                print("!!! {} does not match.".format(ky))
                out = False
        else:
            print("No entry {}".format(ky))
            out = False
    return out


def compare_config(new, old):
    out = True
    for ky in new:
        o_ky = ky
        if isinstance(old, LegacyConfigType) and ky == '_type':
            # Old data structures don't have this.
            continue
        elif isinstance(new, LegacyConfigType) and ky == 'config_type':
            o_ky = '_type'
        if isinstance(new[ky], dict):
            if not compare_config(new[ky], old[o_ky]):
                print("---> config group '{}' does not match <---".format(ky))
                out = False
        elif o_ky in old:
            if array_equiv(new[ky], old[o_ky]):
                #print("{} matches.".format(ky))
                pass
            else:
                print("!!! {} does not match.".format(ky))
                out = False
        else:
            print("No entry {}".format(o_ky))
            out = False
    return out


def compare_old2new(old, new):
    out = True
    out = compare_config(old['config'], new['config'])
    for g, ky in old.groups.iter():
        if g == 'config':
            # This is handled above.
            continue
        if g.startswith('#'):
            g = g[1:]
        if g == 'extra':
            g = '_extra'
        if ky == 'pressure':
            g = 'env'
        if ky == 'AnaIn2MSB':
            g = '_extra'
        if ky == 'orientation_down':
            g = 'orient'
        if ky in new:
            if array_equiv(new[ky], old[ky]):
                pass
            else:
                print("!!! {} does not match.".format(ky))
                out = False
        elif g in new and ky in new[g]:
            if array_equiv(new[g][ky], old[ky]):
                pass
            else:
                print("!!! {} does not match.".format(ky))
                out = False
        else:
            print("No entry {}".format(ky))
            out = False
    return out


def compare(new, old):
    return compare_new2old(new, old) and compare_old2new(old, new)

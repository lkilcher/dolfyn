

# # I'm pretty sure this is unneeded, but saving it here just in case.
# cdef struct headconfig:
#     bint press_valid
#     bint temp_valid
#     bint compass_valid
#     bint tilt_valid
#     bint vel
#     bint amp
#     bint corr
#     bint alti
#     bint altiRaw
#     bint AST
#     bint Echo
#     bint ahrs
#     bint PGood
#     bint stdDev
#     unsigned short ncells
#     unsigned short nbeams


def getbit(val, n):
    return bool((val >> n) & 1)


def headconfig_int2dict(val):
    # Cython doesn't support bit flags, so we do this here.
    return dict(
        press_valid=getbit(val, 0),
        temp_valid=getbit(val, 1),
        compass_valid=getbit(val, 2),
        tilt_valid=getbit(val, 3),
        # bit 4 is unused
        vel=getbit(val, 5),
        amp=getbit(val, 6),
        corr=getbit(val, 7),
        alti=getbit(val, 8),
        altiRaw=getbit(val, 9),
        AST=getbit(val, 10),
        Echo=getbit(val, 11),
        ahrs=getbit(val, 12),
        PGood=getbit(val, 13),
        stdDev=getbit(val, 14),
        # bit 15 is unused
    )


def beams_cy_int2dict(val, id):
    if id == 28:  # 0x1C (echo):
        return dict(ncells=val)
    return dict(
        ncells=val & (2 ** 10 - 1),
        cy=['ENU', 'XYZ', 'BEAM', None][val >> 10 & 3],
        nbeams=val >> 12
    )

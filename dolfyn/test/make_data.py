"""
!!!Warning!!! the lines in this file will rebuild data files that
are benchmark tests. Uncomment lines to rebuild data files only if
you know you have fixed a bug, and wish to fix an existing test data
set.
"""
print(__doc__)

import test_adv as advt
import test_rotate_adv as advro
import test_read_adp as adpr
import test_rotate_adp as adpro


def rungen(gen):
    for g in gen:
        pass


# rungen(advt.read_test(make_data=True))
# rungen(advt.motion_test(make_data=True))
# advt.heading_test(make_data=True)
# advt.turbulence_test(make_data=True)
# advt.clean_test(make_data=True)
# rungen(advt.subset_test(make_data=True))
# rungen(advro.test_rotate_inst2earth(make_data=True))
# rungen(advro.test_rotate_inst2beam(make_data=True))


# rungen(adpr.test_read(make_data=True))
# rungen(adpro.test_rotate_beam2inst(make_data=True))
# rungen(adpro.test_rotate_inst2earth(make_data=True))
# rungen(adpro.test_rotate_earth2inst(make_data=True))
# rungen(adpro.test_rotate_inst2beam(make_data=True))

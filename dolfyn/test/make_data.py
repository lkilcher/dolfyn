"""
!!!Warning!!! the lines in this file will rebuild data files that
are benchmark tests. Uncomment lines to rebuild data files only if
you know you have fixed a bug, and wish to fix an existing test data
set.
"""
print(__doc__)

import adv_tests as advt
import adp_tests as adpt


def rungen(gen):
    for g in gen:
        pass

# rungen(advt.read_test(make_data=True))
# rungen(advt.motion_test(make_data=True))
# advt.heading_test(make_data=True)
# advt.turbulence_test(make_data=True)
# advt.clean_test(make_data=True)
# rungen(advt.subset_test(make_data=True))

# rungen(adpt.read_test(make_data=True))
# adpt.rotate_beam2inst_test(make_data=True)
# adpt.rotate_inst2earth_test(make_data=True)

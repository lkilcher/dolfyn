"""
The base module for the adv package.
"""

from ..data import base as db
from ..data import velocity as dbvel
import numpy as np
# import turbulence as turb
ma = db.ma

# This is the body->imu vector (in body frame)
# In inches it is: (0.25, 0.25, 5.9)
body2imu = {'Nortek VECTOR': np.array([0.00635, 0.00635, 0.14986])}


class ADVraw(dbvel.Velocity):

    """
    The base class for ADV data objects.
    """

    @property
    def make_model(self,):
        return self.props['inst_make'] + ' ' + self.props['inst_model']

    @property
    def body2imu_vec(self,):
        # Currently only the Nortek VECTOR has an IMU.
        return body2imu[self.make_model]


class ADVbinned(dbvel.VelBindatSpec, ADVraw):

    """
    A base class for binned ADV objects.
    """
    # Is this needed?
    pass

The |dlfn| API
------------------

This is the |dlfn| API. It is a high-level object-oriented library
composed of a set of **data-object** classes (types) that contain data
from a particular measurement instrument, and a collection of
**functions** that manipulate those data objects to accomplish data
processing and data analysis tasks.

.. contents::

|dlfn| data objects
^^^^^^^^^^^^^

.. autosummary::
  :toctree: _as_gen
  :nosignatures:

  dolfyn.Velocity
  dolfyn.ADPdata
  dolfyn.ADVdata

.. autoclass:: dolfyn.Velocity
   :members:
   :inherited-members:
   :exclude-members: clear, fromkeys, items, popitem, update, values, setdefault

.. autoclass:: dolfyn.ADPdata
   :members:

.. autoclass:: dolfyn.ADVdata
   :members:

|dlfn| tools and functions
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autosummary::
   :toctree: _as_gen
   :nosignatures:

   dolfyn.read
   dolfyn.rotate2
   dolfyn.adv.motion.CorrectMotion
   dolfyn.VelBinner
   dolfyn.adv.turbulence.TurbBinner
   dolfyn.calc_principal_heading

.. autofunction:: dolfyn.read
   
.. autofunction:: dolfyn.rotate2

.. autoclass:: dolfyn.adv.motion.CorrectMotion
   :members:

.. autoclass:: dolfyn.VelBinner
   :members:
   :inherited-members:

.. autoclass:: dolfyn.adv.turbulence.TurbBinner
   :members:

.. autofunction:: dolfyn.calc_principal_heading

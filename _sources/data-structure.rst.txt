Data Structure
==============

|dlfn| data objects are built on (subclasses of) `pyDictH5
<http://github.com/lkilcher/pyDictH5>`_ data objects, which are
themselves subclasses of Python dictionaries. As such, these objects
support all of the same basic functionality of dictionaries (e.g.,
indexing, iterating, etc.), with additional functionality that is
designed to streamline the process of analyzing and working with
data. Most notably, these data objects provide:

- a summarized view of the data structure when in interactive mode::

    >>> dat
    <ADV data object>
      . 1.05 hours (started: Jun 12, 2012 12:00)
      . EARTH-frame
      . (120530 pings @ 32Hz)
      *------------
      | mpltime                  : <time_array; (120530,); float64>
      | vel                      : <array; (3, 120530); float32>
      + config                   : + DATA GROUP
      + env                      : + DATA GROUP
      + orient                   : + DATA GROUP
      + props                    : + DATA GROUP
      + signal                   : + DATA GROUP
      + sys                      : + DATA GROUP

- attribute-style syntax (``dat.vel`` is equivalent to ``dat['vel']``)

- direct access of items within sub-groups (``dat['env.temp']`` works,
  and ``'env.temp' in dat`` evaluates to ``True``)

See the `pyDictH5 README
<https://github.com/lkilcher/pyDictH5/blob/master/README.rst>`_ for
additional details.

.. _rotations:

Rotations and Coordinate Systems
--------------------------------

Coordinate systems (a.k.a. reference frames) specify the coordinate
directions of vector data in the data object. The values in the list
`dat.props['rotate_vars']` specifies the vectors that are rotated when
changing between different coordinate systems. **You can also create
`dat._rotate_*` functions to perform additional rotation operations. I
need to document these!**

The first dimension of these vectors are the coordinate
systems. DOLfYN supports four primary coordinate systems:

- **BEAM**: this is the coordinate system of the 'along-beam'
  velocities. When a data object is in this coordinate system, only
  the velocity data (i.e., the variables in `dat.props['rotate_vars']`
  starting with '`vel'`) is in beam coordinates. Other vector
  variables listed in `'rotate_vars'` (e.g., `dat.orient.AngRt`, for
  instruments with IMUs) are in the INST frame. This coordinate system
  is *not* ortho-normal. When the data object is in BEAM coordinates,
  the first dimension of the velocity vectors are: [beam1, beam2,
  ... beamN].

- **INST**: this is the 'instrument' coordinate system defined by the
  manufacturer. This coordinate system is orth-normal, but is not
  necessarily fixed. That is, if the instrument is rotating, then this
  coordinate system changes relative to the earth. When the data
  object is in INST coordinates, the first dimension of the vectors
  are: [X, Y, Z, ...].

  Note: instruments with more than three beams will have more than
  three coordinate directions. See the documentation for your specific
  instrument to see how 'extra' dimensions are handled by DOLfYN. **I
  need to update this more**.

- **EARTH**: the earth coordinate system is the 'rotationally-fixed'
  coordinate system. This coordinate system is 'fixed' in the sense
  that it does not rotate, but it may not be 'stationary' if the
  instrument slides around translationally (see the
  :ref:`motion-correction` section for details on how to correct for
  translational motion). When the data object is in EARTH coordinates,
  the first dimension of the vectors are: [East, North, Up, ...].

- **PRINCIPAL**: the principal coordinate system is similar to the
  earth coordinate system (it is fixed), but it has been rotated in
  the horizontal plane to align with the flow in one way or
  another. In this coordinate system the first dimension of the
  vectors are: [Stream-wise, Cross-stream, Up]. By default, the
  stream-wise direction is determined using the
  `:func:<data.velocity.calc_principal_angle>` function. Or, you can
  specify the rotation direction directly by setting
  `dat.props['principal_angle']` to the rotation angle by which you
  want to rotate the horizontal velocity, in units of radians. This
  direction (positive counter-clockwise from east) will be the first
  row of vectors (i.e., the *Streamwise* direction).

To rotate a data object into one of these coordinate systems, simply
use the `rotate2` method::

  >>> dat_earth = dat.rotate2('earth')  # ("rotate to earth") 
  >>> dat_earth
  <ADV data object>
    . 1.05 hours (started: Jun 12, 2012 12:00)
    . EARTH-frame
    . (120530 pings @ 32Hz)
    *------------
    | mpltime                  : <time_array; (120530,); float64>
    | vel                      : <array; (3, 120530); float32>
    + config                   : + DATA GROUP
    + env                      : + DATA GROUP
    + orient                   : + DATA GROUP
    + props                    : + DATA GROUP
    + signal                   : + DATA GROUP
    + sys                      : + DATA GROUP


.. _units:

Data Description and Units
--------------------------

|dlfn| generally uses the `*MKS* system
<https://en.wikipedia.org/wiki/MKS_system_of_units>`_, with most
angles in degrees.

.. csv-table:: Table 1: The units of common variables found in |dlfn| data objects.
               :header-rows: 1
               :widths: 15, 20, 15, 50
               :file: ./units.csv

User Meta-Data (``dat.props``)
------------------------------

The ``props`` data-group of |dlfn| data objects is a place for
user-specified meta-data and |dlfn|-specific implementation data. The
most common variables found here are described in Table 2.

.. |dagger| unicode:: 0x02020 .. the dagger-symbol

.. csv-table:: Table 2: The entries in ``dat.props`` that are used in |dlfn|.
               :header-rows: 1
               :widths: 15, 105
               :file: ./props_info.csv

\*: These entries are set by |dlfn|, and should *not* - in general -
be set or changed by the user.

|dagger|: These entries are not used or set by |dlfn|, but they are
useful measurement meta-data and are listed here to assist in
standardizing the location and format of this information.

Specify meta-data in a JSON file
................................

The values in ``dat.props`` can also be set in a json file,
``<data_filename>.userdata.json``, containing a single `json-object
<https://json.org/>`_. For example, the contents of these files should
look something like::

    {"body2head_rotmat": "identity",
     "body2head_vec": [-1.0, 0.5, 0.2],
     "motion accel_filtfreq Hz": 0.03,
     "declination": 8.28,
     "lonlat": [-105.2283, 39.9402]
    }

Prior to reading a binary data file ``my_data.VEC``, you can
create a ``my_data.userdata.json`` file. Then when you do
``dolfyn.read('my_data.VEC')``, |dlfn| will read the contents of
``my_data.userdata.json`` and include that information in the
``dat.props`` attribute of the returned data object. This
feature is provided so that meta-data can live alongside your
binary data files.


Data Shortcuts (properties)
---------------------------
In addition to the data items listed above, |dlfn| data objects also
contain shortcuts to tools and other variables that can be obtained
from simple operations of its data items. These attributes aren't
listed in the view of the data shown above. Instead, to see the
variables that are available as shortcuts for a particular data
object, take a look at the ``dat.shortcuts`` property (new in |dlfn|
0.10.1).

.. csv-table:: Table 3: Notes on common shorcuts found in |dlfn| data objects.
               :header-rows: 1
               :widths: 15, 20, 85
               :file: ./shortcuts.csv

**Important Note:** The items listed in Table 3 are not stored in the data
object but are provided as attributes (shortcuts) to |dlfn| data objects.

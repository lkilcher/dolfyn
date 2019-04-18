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
      . INST-frame
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
``dat.props['rotate_vars']`` specifies the vectors that are rotated
when changing between different coordinate systems.  The first
dimension of these vectors are their coordinate directions, which are
defined by the following coordinate systems:

- **BEAM**: this is the coordinate system of the 'along-beam'
  velocities. When a data object is in this coordinate system, only
  the velocity data (i.e., the variables in
  ``dat.props['rotate_vars']`` starting with ``'vel'``) is in beam
  coordinates. Other vector variables listed in `'rotate_vars'` (e.g.,
  `dat.orient.AngRt`) are in the INST frame. This coordinate system is
  *not* ortho-normal. When the data object is in BEAM coordinates, the
  first dimension of the velocity vectors are: [beam1, beam2,
  ... beamN].

- **INST**: this is the 'instrument' coordinate system defined by the
  manufacturer. This coordinate system is orth-normal, but is not
  necessarily fixed. That is, if the instrument is rotating, then this
  coordinate system changes relative to the earth. When the data
  object is in INST coordinates, the first dimension of the vectors
  are: [X, Y, Z, ...].

  Note: instruments with more than three beams will have more than
  three velocity components. **|dlfn| does not yet handle these extra
  dimensions consistently**.

- **EARTH**: When the data object is in EARTH coordinates, the first
  dimension of vectors are: [East, North, Up, ...]. This coordinate
  system is also sometimes denoted as "ENU". If the declination is set
  the earth coordinate system is "True-East, True-North, Up"
  otherwise, East and North are magnetic. See the `Declination
  Handling`_ section for further details on setting declination.

  Note that the ENU definition used here is different from the 'north,
  east, down' coordinate system typically used by aircraft.
  Also note that the earth coordinate system is a 'rotationally-fixed'
  coordinate system: it does not rotate, but it is not necessarily
  *inertial* or *stationary* if the instrument slides around
  translationally (see the :ref:`motion-correction` section for
  details on how to correct for translational motion).

- **PRINCIPAL**: the principal coordinate system is a fixed coordinate
  system that has been rotated in the horizontal plane (around the Up
  axis) to align with the flow. In this coordinate system the first
  dimension of a vector is meant to be: [Stream-wise, Cross-stream,
  Up]. This coordinate system is defined by the variables
  ``dat.props['coord_sys_principal_ref']``, and
  ``dat.props['principal_angle']``. These variables define the
  *reference* coordinate system that the data was rotated from and the
  rotation angle, respectively. The rotation angle is the angle that
  the principal coordinate system is rotated relative to the reference
  coordinate system around the Up (or Z axis when the reference
  coordinate system is *inst*), positive according to the
  right-hand-rule (i.e., counter-clockwise). See the `Principal
  Angles`_ section for further details.

To rotate a data object into one of these coordinate systems, simply
use the ``rotate2`` method::

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

Orientation Data
................
  
The instrument orientation data in |dlfn| data objects is contained in
the ``orient`` data group. The ``orientmat`` data item in this group
is the orientation matrix, :math:`R`, of the instrument in the earth
reference frame. It is a 3x3xNt array, where each 3x3 array is the `rotation matrix
<http://en.wikipedia.org/wiki/Rotation_matrix>`_ that rotates vectors
in the earth frame, $v_e$, into the instrument coordinate system,
$v_i$, at each timestep:

.. math:: v_i = R \cdot v_e

The ENU definitions of coordinate systems means that the rows of
:math:`R` are the unit-vectors of the XYZ coordinate system in the ENU
reference frame, and the columns are the unit vectors of the ENU
coordinate system in the XYZ reference frame. That is, for this kind
of simple rotation matrix between two orthogonal coordinate systems,
the inverse rotation matrix is simply the transpose:

.. math:: v_e = R^T \cdot v_i

Heading, Pitch, Roll
....................

The instrument's *heading*, *pitch*, and *roll* information can be
computed from the orientation matrix using the
``dolfyn.rotate.orient2euler`` function. This function computes these
variables according to the following conventions:

  - a "ZYX" rotation order. That is, these variables are computed
    assuming that rotation from the earth -> instrument frame happens
    by rotating around the z-axis first (heading), then rotating
    around the y-axis (pitch), then rotating around the x-axis (roll).

  - heading is defined as the direction the x-axis points, positive
    clockwise from North (this is the opposite direction from the
    right-hand-rule around the Up-axis)

  - pitch is positive when the x-axis pitches up (this agrees with the
    right-hand-rule)

  - roll is positive according to the right-hand-rule around the
    instument's x-axis

Considerable care has been taken to make sure
that these definitions of *heading*, *pitch*, *roll* and *orientmat*
are consistent within |dlfn| between instrument models.
However, because the instrument manufacturer's definitions of these
variables are not consistent between instrument makes/models, this
means that |dlfn|\ 's consistent definitions are often different from
the definitions provided by an instrument manufacturer (i.e., there is
no consensus on these definitions, so |dlfn| uses the above
definitions).

So, while |dlfn| uses the instrument manufacturer's definition of the
instrument coordinate system ("XYZ"), the details of how this relates
to the 'earth' coordinate system, and how *pitch*, *roll*, *heading*
are computed are often distinct from the definitions specified by
the instrument manufacturer (e.g., some manufacturers reference
heading off of the y-axis rather than x, some use a 'north-east-down'
earth reference frame, etc.). For practical purposes, when utilizing
|dlfn| orientation data (for all instrument types), this all means
that the user should:

  - Use the instrument manufacturers definitions of XYZ

  - Interpret *heading*, *pitch*, and *roll* data according to the above
    definitions (ignore manufacturer definitions of these variables)

  - All rotations into the earth frame will yield vectors that are in
    a ENU coordinate system

Declination Handling
....................

|dlfn| includes functionality for handling `declination
<https://www.ngdc.noaa.gov/geomag/declination.shtml>`_, but the value
of the declination must be specified by the user. There are two ways
to set a data-object's declination:

1. Set declination explicitly using the ``dat.set_declination``
   method, for example::

     dat.set_declination(16.53)

2. Set declination in the ``<data_filename>.userdata.json`` file
   (`more details <json-userdata>`_ ), then read the binary data
   file (i.e., using ``dat = dolfyn.read(<data_filename>)``).

Both of these approaches will yield data objects with the following
characteristics:

- If the data-object is in the *earth* reference frame at the time of
  setting declination, it will be rotated into the "*True-East*,
  *True-North*, Up" (hereafter, ETU) coordinate system

- ``dat['orient']['orientmat']`` is modified to be an ETU to
  instrument (XYZ) rotation matrix (rather than the magnetic-ENU to
  XYZ rotation matrix). Therefore, all rotations to/from the 'earth'
  frame will now be to/from this ETU coordinate system.

- The value of the declination will be stored in ``dat.props['declination']``

- ``dat['orient']['heading']`` is adjusted for declination (i.e., it is relative to True North)

Principal Angles
................

As described above, the principal coordinate system is meant to be the
flow-aligned coordinate system (Streamwise, Cross-stream, Up). |dlfn|
includes the `:func:<dolfyn.calc_principal_angle>` function to aide in
identifying/calculating the principal angle. Using this function to
identify the principal angle, an ADV data object can be rotated into
the principal coordinate system like this::

  dat.props['principal_angle'] = dolfyn.calc_principal_angle(dat.vel)
  dat.rotate2('principal')

Note here that when you are rotating to the principal coordinate
system, and ``dat.props['coord_sys_principal_ref']`` is not defined
(but ``principal_angle`` is), ``rotate2`` assumes that the data
object's existing coordinate system is the reference coordinate
system, and it sets it (i.e., prior to rotating to principal,
``rotate2`` does ``dat.props['coord_sys_principal_ref'] =
dat.props['coord_sys']``).

It should also be noted that by defining
``dat.props['principal_angle']``, the user can choose any horizontal
coordinate system that they like, and this might not be consistent
with the *streamwise, cross-stream, up* definition described here. In
those cases, the user should take care to clarify this point with
collaborators to avoid confusion.

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

.. _json-userdata

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

.. _rotations:

Rotations & Coordinate Systems
==============================

One of |dlfn|\ 's primary advantages is that it contains tools
for managing the coordinate system (a.k.a. the reference frame) of
tensor data. The coordinate-system/rotation tools provided in
|dlfn| have been tested to varying degrees on different types of
instruments and configurations. See :ref:`the table
<rotate-testing-table>` at the bottom of this page for details on the
degree of testing of |dlfn|\ 's rotations and coordinate-system tools
that has occurred for several instrument types. With your help, we
hope to improve our confidence in these tools for the wide-array of
instruments and configurations that exist.

The values in the list ``dat.attrs['rotate_vars']`` specifies the
vectors that are rotated when changing between different coordinate
systems.  The first dimension of these vectors are their coordinate
directions, which are defined by the following coordinate systems:

- **Beam**: this is the coordinate system of the 'along-beam'
  velocities.  When the data object is in 'beam' coordinates, the first
  dimension of the velocity vectors are: [beam1, beam2,
  ... beamN]. This coordinate system is *not* ortho-normal, which
  means that the inverse rotation (inst to beam) cannot be computed
  using the transpose of the beam-to-inst rotation matrix. Instead,
  the inverse of the matrix must be computed explicitly, which is done
  internally in |dlfn| (in :func:`~dolfyn.rotate.base.beam2inst`).

  When a data object is in this coordinate system, only the velocity
  data (i.e., the variables in ``dat.attrs['rotate_vars']`` starting
  with ``'vel'``) is in beam coordinates. Other vector variables
  listed in ``'rotate_vars'`` are in the 'inst' frame (e.g.,
  ``dat.angrt``). This is true for data read from binary files
  that is in beam coordinates, and also when rotating from other
  coordinate systems to beam coordinates.

- **Inst**: this is the 'instrument' coordinate system defined by the
  manufacturer. This coordinate system is ortho-normal, but is not
  necessarily fixed. That is, if the instrument is rotating, then this
  coordinate system changes relative to the earth. When the data
  object is in 'inst' coordinates, the first dimension of the vectors
  are: [X, Y, Z, ...].

- **Earth**: When the data object is in 'earth' coordinates, the first
  dimension of vectors are: [East, North, Up, ...]. This coordinate
  system is also sometimes denoted as "ENU". If the declination is set
  the earth coordinate system is "True-East, True-North, Up"
  otherwise, East and North are magnetic. See the `Declination
  Handling`_ section for further details on setting declination.

  Note that the ENU definition used here is different from the 'North,
  East, Down' local coordinate system typically used by aircraft.
  Also note that the earth coordinate system is a 'rotationally-fixed'
  coordinate system: it does not rotate, but it is not necessarily
  *inertial* or *stationary* if the instrument slides around
  translationally (see the :ref:`motion-correction` section for
  details on how to correct for translational motion).

- **Principal**: the principal coordinate system is a fixed coordinate
  system that has been rotated in the horizontal plane (around the Up
  axis) to align with the flow. In this coordinate system the first
  dimension of a vector is meant to be: [Stream-wise, Cross-stream,
  Up]. This coordinate system is defined by the variable
  ``dat.attrs['principal_heading']``, which specifies the
  principal coordinate system's :math:`+u` direction. The
  :math:`v` direction is then defined by the right-hand-rule (with
  :math:`w` up). See the `Principal Heading`_ section for further
  details.

To rotate a data object into one of these coordinate systems, simply
use the ``rotate2`` method:

.. code-block::

  >> dat = dlfn.read_example('vector_data_imu01.VEC')
  >> dlfn.rotate2(dat, 'earth')
  >> dat
  <xarray.Dataset>
  Dimensions:              (time: 27043, dir: 3, beam: 3, x*: 3, earth: 3, inst: 3, dirIMU: 3)
  Coordinates:
    * time                 (time) datetime64[ns] 2012-06-12T12:00:02.681046 ......
    * dir                  (dir) <U1 'E' 'N' 'U'
    * beam                 (beam) int32 1 2 3
    * x*                   (x*) int32 1 2 3
    * earth                (earth) <U1 'E' 'N' 'U'
    * inst                 (inst) <U1 'X' 'Y' 'Z'
    * dirIMU               (dirIMU) <U1 'E' 'N' 'U'
  Data variables: (12/18)
    beam2inst_orientmat  (beam, x*) float64 2.74 -1.384 -1.354 ... 0.3489 0.3413
    batt                 (time) float32 11.3 11.3 11.3 11.3 ... 10.8 10.8 10.8
    c_sound              (time) float32 1.491e+03 1.491e+03 ... 1.486e+03
    heading              (time) float32 0.0 0.0 0.0 0.0 0.0 ... 0.0 0.0 0.0 0.0
    pitch                (time) float32 0.0 0.0 0.0 0.0 0.0 ... 0.0 0.0 0.0 0.0
    roll                 (time) float32 0.0 0.0 0.0 0.0 0.0 ... 0.0 0.0 0.0 0.0
                  ...
    accel                (dir, time) float32 -0.03771 0.01074 ... 9.796 9.788
    angrt                (dir, time) float32 -0.006857 -0.004057 ... 0.1279
    mag                  (dir, time) float32 0.001869 0.001455 ... -0.5543
    orientmat            (earth, inst, time) float32 0.7867 0.7819 ... -0.9979
    orientation_down     (time) bool False False False ... False False False
    pressure             (time) float64 198.6 198.6 198.6 ... 623.2 623.2 623.2
  Attributes:
    config:       {'ProLogID': 187, 'ProLogFWver': '4.12', 'config': 15412, '...
    inst_make:    Nortek
    inst_model:   Vector
    inst_type:    ADV
    rotate_vars:  ['vel', 'accel', 'angrt', 'mag']
    freq:         6000
    SerialNum:    VEC 9625
    Comments:     NREL Vector with INS on APL-UW Tidal Turbulence Mooring in ...
    fs:           32.0
    coord_sys:    earth
    has_imu:      1


Orientation Data
----------------
  
The instrument orientation data in |dlfn| data objects is contained in
``orientmat`` and ``beam2inst_orientmat``. The ``orientmat`` data item
is the earth2inst orientation matrix, :math:`R`, of the instrument in the earth
reference frame. It is a 3x3xNt array, where each 3x3 array is the `rotation matrix
<http://en.wikipedia.org/wiki/Rotation_matrix>`_ that rotates vectors
in the earth frame, :math:`v_e`, into the instrument coordinate system,
:math:`v_i`, at each timestep:

.. math:: v_i = R \cdot v_e

The ENU definitions of coordinate systems means that the rows of
:math:`R` are the unit-vectors of the XYZ coordinate system in the ENU
reference frame, and the columns are the unit vectors of the ENU
coordinate system in the XYZ reference frame. That is, for this kind
of simple rotation matrix between two orthogonal coordinate systems,
the inverse rotation matrix is simply the transpose:

.. math:: v_e = R^T \cdot v_i

Heading, Pitch, Roll
--------------------

Most instruments do not calculate or output the orientation
matrix by default. Instead, these instruments typically provide
*heading*, *pitch*, and *roll* data (hereafter, *h,p,r*).  Instruments that provide an ``orientmat`` directly will contain ``dat.attrs['has_imu'] = 1``. Otherwise, the ``orientmat`` was calculated from *h,p,r*.

Note that an orientation matrix calculated
from *h,p,r* can have larger error associated with it, partly because
of the `gimbal lock <https://en.wikipedia.org/wiki/Gimbal_lock>`_
problem, and also because the accuracy of some *h,p,r* sensors
decreases for large pitch or roll angles (e.g., >40 degrees).

Because the definitions of *h,p,r* are not consistent between
instrument makes/models, and because |dlfn|\ -developers have chosen
to utilize consistent definitions of orientation data (``orientmat``,
and *h,p,r*), the following things are true:

- |dlfn| uses instrument-specific functions to calculate a
  consistent ``orientmat`` from the inconsistent
  definitions of *h,p,r*

- |dlfn|\ 's consistent definitions *h,p,r* are generally different
  from the definitions provided by an instrument manufacturer (i.e.,
  there is no consensus on these definitions, so |dlfn| developers
  have chosen one)

Varying degrees of validation have been performed to confirm that the
``orientmat`` is being calculated correctly for each instrument's
definitions of *h,p,r*. See the :ref:`the table
<rotate-testing-table>` at the bottom of this page for details on
this. If your instrument has low confidence, or you suspect an error
in rotating data into the earth coordinate system, and you have
interest in doing the work to fix this, please reach out to us
by filing an issue.

|dlfn|-Defined Heading, Pitch, Roll
...................................

The |dlfn|-defined *h,p,r* variables can be calculated using the
:func:`dolfyn.orient2euler` function (:func:`dolfyn.euler2orient`
provides the reverse functionality). This function computes these
variables according to the following conventions:

- a "ZYX" rotation order. That is, these variables are computed
  assuming that rotation from the earth -> instrument frame happens
  by rotating around the z-axis first (heading), then rotating
  around the y-axis (pitch), then rotating around the x-axis (roll).

- heading is defined as the direction the x-axis points, positive
  clockwise from North (this is *opposite* the right-hand-rule
  around the Z-axis)

- pitch is positive when the x-axis pitches up (this is *opposite* the
  right-hand-rule around the Y-axis)

- roll is positive according to the right-hand-rule around the
  instrument's x-axis

Instrument heading, pitch, roll
...............................
    
The raw *h,p,r* data as defined by the instrument manufacturer is
available in ``dat.data_vars``. Note that this data does not
obey the above definitions, and instead obeys the instrument
manufacturer's definitions of these variables (i.e., it is exactly the
data contained in the binary file). Also note that ``dat['heading']`` 
is unaffected by setting declination as described in the next section.
    
Declination Handling
--------------------

|dlfn| includes functionality for handling `declination
<https://www.ngdc.noaa.gov/geomag/declination.shtml>`_, but the value
of the declination must be specified by the user. There are two ways
to set a data-object's declination:

#. Set declination explicitly using the ``set_declination``
   method, for example::

     dlfn.set_declination(dat, 16.53)

#. Set declination in the ``<data_filename>.userdata.json`` file
   (`more details <json-userdata>`_ ), then read the binary data
   file (i.e., using ``dat = dolfyn.read(<data_filename>)``).

Both of these approaches produce modify the ``dat`` as described in
the documentation for :meth:`~dolfyn.set_declination` .
   
Principal Heading
-----------------

As described above, the principal coordinate system is meant to be the
flow-aligned coordinate system (Streamwise, Cross-stream, Up). |dlfn|
includes the :func:`~dolfyn.calc_principal_heading` function to aide in
identifying/calculating the principal heading. Using this function to
identify the principal heading, an ADV data object that is in the
earth-frame can be rotated into the principal coordinate system like
this:

.. code-block::

  dat.attrs['principal_heading'] = dlfn.calc_principal_heading(dat.vel)
  dat.rotate2('principal')

Note here that if ``dat`` is in a coordinate system other than EARTH,
you will get unexpected results, because you will calculate a
*principal_heading* in the coordinate system that the data is in.

It should also be noted that by setting
``dat.attrs['principal_heading']`` the user can choose any horizontal
coordinate system, and this might not be consistent with the
*streamwise, cross-stream, up* definition described here. In those
cases, the user should take care to clarify this point with
collaborators to avoid confusion.

Degree of testing by instrument type
------------------------------------

The table below details the degree of testing of the rotation,
*p,r,h*, and coordinate-system tools contained in |dlfn|. The
*confidence* column provides a general indication of the level of
confidence that we have in these tools for each instrument.

If you encounter unexpected results that seem to be
related to coordinate systems (especially for instruments and
configurations that are listed as "low" or "medium" confidence), the
best thing to do is file :repo:`an issue <issues/>`.


.. _rotate-testing-table:

.. csv-table:: Table 1: Instruments tested to be consistent with
               |dlfn|\ 's coordinate systems and rotation tools.
               :header-rows: 1
               :widths: 15, 20, 30, 15, 50
               :file: ./rotation_testing.csv

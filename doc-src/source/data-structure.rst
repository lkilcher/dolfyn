Data Structure
==============

|dlfn| data objects are built on (subclasses of) `pyDictH5 <http://github.com/lkilcher/pyDictH5>`_ data objects, which are themselves subclasses of Python dictionaries. As such, these objects support all of the same basic functionality of dictionaries (e.g., indexing, iterating, etc.), with additional functionality that is designed to streamline the process of analyzing and working with data. Most notably, these data objects provide:

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

- direct access of items within sub-groups (``dat['env.temp']`` works, and ``'env.temp' in dat`` evaluates to ``True``)

See the `pyDictH5 README <https://github.com/lkilcher/pyDictH5/blob/master/README.rst>`_ for additional details.

.. _rotations:

Rotations and Coordinate Systems
--------------------------------

Coordinate systems (a.k.a. reference frames) specify the coordinate directions of vector data in the data object. The values in the list `dat.props['rotate_vars']` specifies the vectors that are rotated when changing between different coordinate systems. The first dimension of these vectors are the coordinate systems. DOLfYN supports four primary coordinate systems:

- **BEAM**: this is the coordinate system of the 'along-beam' velocities. When a data object is in this coordinate system, only the velocity data (i.e., the variables in `dat.props['rotate_vars']` starting with '`vel'`) is in beam coordinates. Other vector variables listed in `'rotate_vars'` (e.g., `dat.orient.AngRt`, for instruments with IMUs) are in the INST frame. This coordinate system is *not* ortho-normal. When the data object is in BEAM coordinates, the first dimension of the velocity vectors are: [beam1, beam2, ... beamN].

- **INST**: this is the 'instrument' coordinate system defined by the manufacturer. This coordinate system is orth-normal,  but is not necessarily fixed. That is, if the instrument is rotating, then this coordinate system changes relative to the earth. When the data object is in INST coordinates, the first dimension of the vectors are: [X, Y, Z, ...].

  Note: instruments with more than three beams will have more than three coordinate directions. See the documentation for your specific instrument to see how 'extra' dimensions are handled by DOLfYN. **I need to update this more**.

- **EARTH**: the earth coordinate system is the 'rotationally-fixed' coordinate system. This coordinate system is 'fixed' in the sense that it does not rotate, but it may not be 'stationary' if the instrument slides around translationally (see the :ref:`motion-correction` section for details on how to correct for translational motion). When the data object is in EARTH coordinates, the first dimension of the vectors are: [East, North, Up, ...].

- **PRINCIPAL**: the principal coordinate system is similar to the earth coordinate system (it is fixed), but it has been rotated in the horizontal plane to align with the flow in one way or another. In this coordinate system the first dimension of the vectors are: [Stream-wise, Cross-stream, Up]. By default, the stream-wise direction is determined using the `:func:<data.velocity.calc_principal_angle>` function. Or, you can specify the rotation direction directly by setting `dat.props['principal_angle']` to the rotation angle by which you want to rotate the horizontal velocity, in units of radians. This direction (positive counter-clockwise from east) will be the first row of vectors (i.e., the *Streamwise* direction).

To rotate a data object into one of these coordinate systems, simply use the `rotate2` method::

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

Units
-----

|dlfn| generally uses the `*MKS* system <https://en.wikipedia.org/wiki/MKS_system_of_units>`_, with most angles in degrees. This table lists the units of all variables in |dlfn| data objects:

.. csv-table:: Units Table!
               :header-rows: 1
               :widths: 15, 20, 15, 50
               :file: ./units.csv


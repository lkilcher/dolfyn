.. _usage:

The Basics
=====

|dlfn| is a library of tools for reading, processing, and analyzing
data from oceanographic velocity measurement instruments such as
acoustic Doppler velocimeters (ADVs) and acoustic Doppler profilers
(ADPs). This page documents general and basic usage of the |dlfn| package.

Reading data
---------------

To begin, we load the |dlfn| module and read a data file::

  >>> import dolfyn as dlfn
  >>> dat = dlfn.read(<path/to/my_data_file>)

In an interactive shell, typing the variable name and hitting enter will display information about the data object, e.g.::

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

This view reveals a few detailed attributes of the data object (above line), and the underlying data structure (below). The attributes indicate that this ADV dataset is 3.02 seconds long, started at noon on June 12, 2012, is in the 'instrument' reference-frame, and contains 99 pings at a 32Hz sample-rate. The information below the line shows the variable names in the ADV dataset. ``mpltime`` is a `<~dolfyn.data.time.time_array>` that contains the time information in MatPlotLib time format. ``vel`` is the velocity data. The other entries (with `+` next to them) are 'data groups', which contain additional data. These variables can be accessed using dict-style syntax, *or* attribute-style syntax. For example::

  >>> dat['mpltime']
  time_array([734666.50003436, 734666.50003472, 734666.50003509, ...,
              734666.54362775, 734666.54362811, 734666.54362847])

  >>> dat.vel
  array([[-1.0020001 , -1.008     , -0.94400007, ...,  0.83100003,
          -2.305     ,  5.177     ],
         [ 0.097     ,  0.068     ,  0.066     , ..., -2.275     ,
           0.86300004, -3.6950002 ],
         [ 0.115     ,  0.12400001,  0.12200001, ...,  0.596     ,
           0.22700001,  0.16600001]], dtype=float32)

Interactive display of a data group will reveal the variables the group contains::

  >>> dat.orient
  <class 'dolfyn.data.base.TimeData'>: Data Object with Keys:
    *------------
    | heading                  : <array; (120530,); float32>
    | orientation_down         : <array; (120530,); bool>
    | pitch                    : <array; (120530,); float32>
    | roll                     : <array; (120530,); float32>

Note here that the display information includes the size of each array, and its data-type. The units of most variables are in the *MKS* system (e.g., velocity is in meters-per-second), and angles are in degrees. See the [units]_ section for a complete list of the units of variables handled by |dlfn|.

Data Groups
-------------

The data in data objects is organized into data groups to facilitate easier viewing, and to streamline file I/O during advanced processing steps (i.e., so that you only load the data you need). The 

- **``config``**: this data group contains instrument-configuration data that was loaded from the source file. This is a long list of information that (*mostly*) inherits attribute names from the manufacturers documentation (i.e., see that documentation for info on these variables).

- **``env``**: contains *environmental* data such as temperature, pressure, or the speed of sound::
     <class 'dolfyn.data.base.TimeData'>: Data Object with Keys:
      *------------
      | c_sound                  : <array; (120530,); float32>
      | pressure                 : <array; (120530,); float64>
      | temp                     : <array; (120530,); float32>

- **``orient``**: contains orientation data such as pitch, roll, and heading (shown above).

- **``props``**: is a dictionary containing information about the data object that is used and modified by/within |dlfn|::

    >>> dat.props
    {'coord_sys': 'inst',
     'fs': 32,
     'has imu': False,
     'inst_make': 'Nortek',
     'inst_model': 'VECTOR',
     'inst_type': 'ADV',
     'rotate_vars': {'vel'}}

  Here we see that the ``props`` attribute contains the `'coord_sys'` entry, which is the 'coordinate system' or 'reference frame' of the data (see the [rotations]_ section for more information on coordinate systems). It also includes the data sample-rate (32 Hz), and indicates whether this instrument has an 'inertial motion unit' or 'IMU' (it doesn't). The instrument manufacturer, model, and type are also included here. The last entry in this dictionary is the `'rotate_vars'` entry, which lists the vector-variables that should be rotated when rotating this data object.

- **``signal``**: contains information about the amplitude and quality (e.g., correlation) of the acoustic signal::

    <class 'dolfyn.data.base.TimeData'>: Data Object with Keys:
      *------------
      | amp                      : <array; (3, 120530); uint8>
      | corr                     : <array; (3, 120530); uint8>

- **``sys``**: contains system status information such as battery levels, and error codes::

    <class 'dolfyn.data.base.TimeData'>: Data Object with Keys:
      *------------
      | batt                     : <array; (120530,); float32>
      | error                    : <array; (120530,); uint8>
      | status                   : <array; (120530,); uint8>

  
Saving Data
-------

Finally, note that a data object can be saved for later use using the ``to_hdf5`` method::

  >>> dat.to_hdf5('my_data_file.h5')

To load this data from the data file, use |dlfn|'s load function::

  >>> dat2 = dlfn.load('my_data_file.h5')

.. _rotations:
Rotations and Coordinate Systems
-----------------------------------------

Coordinate systems (a.k.a. reference frames) specify the coordinate directions of vector data in the data object. The values in the list `dat.props['rotate_vars']` specifies the vectors that are rotated when changing between different coordinate systems. The first dimension of these vectors are the coordinate systems. DOLfYN supports four primary coordinate systems:

- **BEAM**: this is the coordinate system of the 'along-beam' velocities. When a data object is in this coordinate system, only the velocity data (i.e., the variables in `dat.props['rotate_vars']` starting with '`vel'`) is in beam coordinates. Other variables in the data object (e.g., `dat.orient.AngRt`, for instruments with IMUs) are in the INST frame. This coordinate system is *not* ortho-normal. When the data object is in BEAM coordinates, the first dimension of the velocity vectors are: [beam1, beam2, ... beamN].

- **INST**: this is the 'instrument' coordinate system defined by the manufacturer. This coordinate system is orth-normal,  but is not necessarily fixed. That is, if the instrument is rotating, then this coordinate system changes relative to the earth. When the data object is in INST coordinates, the first dimension of the vectors are: [X, Y, Z, ...].

  Note: instruments with more than three beams will have more than three coordinate directions. See the documentation for your specific instrument to see how 'extra' dimensions are handled by DOLfYN. **I need to update this more**.

- **EARTH**: the earth coordinate system is the 'rotationally-fixed' coordinate system. This coordinate system is 'fixed' in the sense that it does not rotate, but it may not be 'stationary' if the instrument slides around translationally (see the [motion-correction]_ section for details on how to correct for translational motion). When the data object is in EARTH coordinates, the first dimension of the vectors are: [East, North, Up, ...].

- **PRINCIPAL**: the principal coordinate system is similar to the earth coordinate system (it is fixed), but it has been rotated in the horizontal plane to align with the flow in one way or another. In this coordinate system the first dimension of the vectors are: [Stream-wise, Cross-stream, Up]. By default, the stream-wise direction is determined using the `:func:<data.velocity.calc_principal_angle>` function. Or, you can specify the rotation direction directly by setting `dat.props['principal_angle']` to the rotation angle by which you want to rotate the horizontal velocity, in units of radians. This direction (positive counter-clockwise from east) will be the first row of vectors (i.e., the *Streamwise* direction).

To rotate a data object into one of these coordinate systems, simply use the rotate method::

  >>> dat_earth = dat.rotate('earth')
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
  
Working with ADV data
.....................

|dlfn| has several tools for performing useful and common operations
on ADV data. Most of these are available via the ADV
:mod:`~dolfyn.adv.api`. For example:

.. literalinclude:: examples/adv_example01.py





.. Plotting ADV data
   .................



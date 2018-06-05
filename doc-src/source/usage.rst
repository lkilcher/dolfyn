.. _usage:

The Basics
==========

|dlfn| is a library of tools for reading, processing, and analyzing
data from oceanographic velocity measurement instruments such as
acoustic Doppler velocimeters (ADVs) and acoustic Doppler profilers
(ADPs). This page documents general and basic usage of the |dlfn| package.

Reading source data files
-----------------------------

To begin, we load the |dlfn| module and read a data file::

  >>> import dolfyn as dlfn
  >>> dat = dlfn.read(<path/to/my_data_file>)

.. ADD MORE HERE: |dlfn|'s read function is for reading binary data formats. Which formats are supported? Which aren't? Why aren't pre-processed (e.g., text etc.) files supported?
  
In an interactive shell, typing the variable name followed by enter/return will display information about the data object, e.g.::

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

This view reveals a few detailed attributes of the data object (above line), and the underlying data structure (below). The attributes indicate that this ADV dataset is 3.02 seconds long, started at noon on June 12, 2012, is in the 'instrument' reference-frame, and contains 99 pings at a 32Hz sample-rate. The information below the line shows the variable names in the ADV dataset. ``mpltime`` is a `<~dolfyn.data.time.time_array>` that contains the time information in `MatPlotLib date <https://matplotlib.org/api/dates_api.html#matplotlib.dates.date2num>`_ format. ``vel`` is the velocity data. The other entries (with ``+`` next to them) are 'data groups', which contain additional data. These variables can be accessed using dict-style syntax, *or* attribute-style syntax. For example::

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

Note here that the display information includes the size of each array, and its data-type. The units of most variables are in the *MKS* system (e.g., velocity is in meters-per-second), and angles are in degrees. See the :ref:`units` section for a complete list of the units of |dlfn| variables.

Data Groups
-------------

The data in data objects is organized into data groups to facilitate easier viewing, and to streamline file I/O during advanced processing steps (i.e., so that you only load the data you need). The 

- ``config``: this data group contains instrument-configuration data that was loaded from the source file. This is a long list of information that (*mostly*) inherits attribute names from the manufacturers documentation (i.e., see that documentation for info on these variables).

- ``env``: contains *environmental* data such as temperature, pressure, or the speed of sound::
     <class 'dolfyn.data.base.TimeData'>: Data Object with Keys:
      *------------
      | c_sound                  : <array; (120530,); float32>
      | pressure                 : <array; (120530,); float64>
      | temp                     : <array; (120530,); float32>

- ``orient``: contains orientation data such as pitch, roll, and heading (shown above).

- ``props``: is a dictionary containing information about the data object that is used and modified by/within |dlfn|::

    >>> dat.props
    {'coord_sys': 'inst',
     'fs': 32,
     'has imu': False,
     'inst_make': 'Nortek',
     'inst_model': 'VECTOR',
     'inst_type': 'ADV',
     'rotate_vars': {'vel'}}

Here we see that the ``props`` attribute contains the `'coord_sys'` entry, which is the 'coordinate system' or 'reference frame' of the data (see the :ref:`rotations` section for more information on coordinate systems). It also includes the data sample-rate (32 Hz), and indicates whether this instrument has an 'inertial motion unit' or 'IMU' (it doesn't). The instrument manufacturer, model, and type are also included here. The last entry is the `'rotate_vars'` entry, which lists the vector-variables that should be rotated when rotating this data object (again, see the :ref:`rotations` section).

- ``signal``: contains information about the amplitude and quality (e.g., correlation) of the acoustic signal::

    <class 'dolfyn.data.base.TimeData'>: Data Object with Keys:
      *------------
      | amp                      : <array; (3, 120530); uint8>
      | corr                     : <array; (3, 120530); uint8>

- ``sys``: contains system status information such as battery levels, and error codes::

    <class 'dolfyn.data.base.TimeData'>: Data Object with Keys:
      *------------
      | batt                     : <array; (120530,); float32>
      | error                    : <array; (120530,); uint8>
      | status                   : <array; (120530,); uint8>

  
Saving and loading data
------------------------------

A data object can be saved for later use using the ``to_hdf5`` method::

    >>> dat.to_hdf5('my_data_file.h5')

To load this data into memory (e.g., in a different script), use |dlfn|'s load function::

    >>> dat2 = dlfn.load('my_data_file.h5')

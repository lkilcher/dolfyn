.. _usage:

The Basics
==========

|dlfn| data objects are built on (subclasses of) `pyDictH5
<http://github.com/lkilcher/pyDictH5/blob/master/README.rst>`_ 
data objects. These objects support all of the same basic 
functionality of dictionaries (e.g., indexing, iterating, etc.), 
with additional functionality that is designed to streamline 
the process of analyzing and working with data. Most notably, 
these data objects provide:

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

This view reveals a few detailed attributes of the data object (above line), and the underlying data structure (below). The attributes indicate that this ADV dataset is 

* 1.05 hours long
* started at noon on June 12, 2012
* is in the 'instrument' reference-frame
* contains 120530 pings at a 32Hz sample-rate

The information below the line shows the variable names in the ADV dataset.

* ``mpltime`` is a :class:`~dolfyn.data.time.time_array` that contains the time information in `MatPlotLib date <https://matplotlib.org/api/dates_api.html#matplotlib.dates.date2num>`_ format 
* ``vel`` is the velocity data
* Other entries (with ``+`` next to them) are 'data groups', which contain additional data

These variables can be accessed using dict-style syntax, *or* attribute-style syntax. For example::

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

Subsetting data
---------------

A segment of the time-record of a data object can be extracted to a new data object using the ``subset`` property, for example::

  >>> datsub = dat.subset[:1000]

Returns a new data object with a copy of the first one-thousand time-steps from the original data object.

The subset property is actually an indexing-object that takes a *one-dimensional* `numpy-compatible indexing object <https://docs.scipy.org/doc/numpy/reference/arrays.indexing.html>`_ such as slices and boolean arrays. For example, we can also do::

  >>> from datetime import datetime
  >>> datsub = dat.subset[(datetime(2012,6,12,0,1) < dat.mpltime.datetime) &
						 (dat.mpltime.datetime < datetime(2012,6,12,12,0,3))]

This gives a data with data from the original for the two seconds between 12:00:01 and 12:00:03 on June 12, 2012. This also reveals the ``.datetime`` property of the ``time_array`` class, but this functionality may change.

Saving and loading data
------------------------------

A data object can be saved for later use using the ``to_hdf5`` method::

    >>> dat.to_hdf5('my_data_file.h5')

To load this data into memory (e.g., in a different script), use |dlfn|'s load function::

    >>> dat2 = dlfn.load('my_data_file.h5')

Cleaning data
----------------

|dlfn| includes tools for cleaning ADV data in the ``dlfn.adv.clean`` module. Take a look at those functions for more details. Tools for cleaning ADP data are located in the ``dlfn.adp.clean`` module.
  
Averaging data
------------------

|dlfn| includes tools for averaging data and computing turbulence
statistics from ADV and ADP data. These tools are Python classes
('averaging objects') that are initialized with specific averaging
window details, and then you call methods of the averaging object to
compute averages or turbulence statistics. For example::

  # First initalize the averaging tool
  >>> avg_tool = dlfn.VelBinner(n_bin=4800, fs=16)

  # Then create ensembles of all variables in dat
  >>> avg_dat = avg_tool.do_avg(dat)

Here, we have initialized an averaging tool, ``avg_tool``, to bin 16 Hz data into 4800-point ensembles (5 minutes). Then when we call the ``do_avg`` method in the averaging tool on a data object, it returns an 'averaged' data object, where all the data field names are the same, but the fields contain averaged data. The averaging tool also includes many other tools (methods) for computing statistics other than averages, for example::

  # Compute the power-spectral-density of the velocity data, and store it in 
  >>> avg_dat['Spec'] = avg_tool.do_spec(dat)

  # Compute the Reynold's stresses (cross-correlations) of the velocity data:
  >>> avg_dat['stress'] = avg_tool.calc_stress(dat['vel'])

There is also :class:`~dolfyn.adv.turbulence.TurbBinner`, which is based on
:class:`~dolfyn.data.velocity.VelBinner`, and has several methods for computing additional statistics from ADV data. Take a look at the API documentation for both of
those tools for more details.

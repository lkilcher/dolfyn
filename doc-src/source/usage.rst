.. _usage:

Usage
=====

|dlfn| is a library of tools for reading, processing, and analyzing
data from oceanographic instrumentation such as acoustic Doppler
velocimeters (ADVs) and acoustic Doppler profilers (ADPs). It also
includes tools for reading buoy data from the `National Data Buoy
Center <http://www.ndbc.noaa.gov/>`_ (NDBC).

|dlfn| is organized into subpackages for working with each data type
it supports, as well as base packages

This page documents general and basic usage of the |dlfn| package, for
detailed information on more specific uses of the package see the
[usage-specific]_ page.

Working with ADV data
---------------------

Acoustic Doppler velocimeters (ADVs) make measurements of velocity at
a point in space (e.g. the `Sontek Argonaut-ADV
<http://www.sontek.com/productsdetail.php?Argonaut-ADV-6>`_, and the
`Nortek Vector <http://www.nortek-as.com/en/products/velocimeters>`_).

Reading ADV data
................

Currently |dlfn| supports reading of binary Nortek Vector, `.vec`,
files. Assuming you are working from an interactive prompt, you can
read a Vector file like this::

  >>> from dolfyn.adv import api as adv
  >>> dat = adv.read_nortek(<path/to/my_vector_file.vec>)

This returns a :class:`~dolfyn.adv.base.ADVraw` object, which contains
the data loaded from the file::

  >>> dat.u
  array([-0.92200005, -0.87800002, -0.85400003, ..., -0.88900006,
         -0.85600007, -0.98100007], dtype=float32)

  >>> dat.mpltime
  time_array([ 734666.50003103,  734666.50003139,  734666.50003175, ...,
          734666.50973251,  734666.50973287,  734666.50973323])

Working with ADV data
.....................

|dlfn| has several tools for performing useful and common operations
on ADV data. Most of these are available via the ADV
:mod:`~dolfyn.adv.api`. For example:

.. literalinclude:: examples/adv_example01.py





.. Plotting ADV data
   .................



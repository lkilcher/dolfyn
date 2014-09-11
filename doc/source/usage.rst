.. _usage:

Usage
=====

DOLfYN is a library of tools for reading, processing, and analyzing data from oceanographic instrumentation such as acoustic Doppler velocimeters (ADVs) and acoustic Doppler profilers (ADPs). It also includes tools for reading buoy data from the `National Data Buoy Center <http://www.ndbc.noaa.gov/>`_ (NDBC).

DOLfYN is organized into subpackages for working with each data type it supports, as well as base packages 

Working with ADV data
---------------------

Acoustic Doppler velocimeters (ADVs) make measurements of velocity at a point in space (e.g. the `Sontek Argonaut-ADV <http://www.sontek.com/productsdetail.php?Argonaut-ADV-6>`_, and the `Nortek Vector <http://www.nortek-as.com/en/products/velocimeters>`_).

Reading ADV data
................

Currently DOLfYN supports reading of binary Nortek Vector, `.vec`, files. Assuming you are working from an interactive prompt, you can read a Vector file like this::

  >>> from dolfyn.adv import api as avm
  >>> dat = api.read_nortek(<path/to/my_vector_file.vec>)

The variable this returns is an :class:`adv_raw <dolfyn.adv.base.adv_raw>` object, which contains the data loaded from the file::

  >>> dat.u
  array([-0.92200005, -0.87800002, -0.85400003, ..., -0.88900006,
         -0.85600007, -0.98100007], dtype=float32)

  >>> dat.mpltime
  time_array([ 734666.50003103,  734666.50003139,  734666.50003175, ...,
          734666.50973251,  734666.50973287,  734666.50973323])

The :class:`adv_raw ` 

.. DOLfYN documentation master file, created by
   sphinx-quickstart on Tue Apr  1 12:34:10 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to the DOLfYN home page!
================================

DOLfYN is the Doppler Oceanography Library for pYthoN.

DOLfYN includes libraries for reading binary Nortek(tm) and
Teledyne-RDI(tm) data files.  At this point it is designed to read and
work with Acoustic Doppler Velocimeter (ADV) and Acoustic Doppler
Profiler (ADP/ADCP) data.  If you have a data file of one of these
formats that is not read by DOLfYN, contact the DOLfYN development
team.  If you have suggestions of other data-file formats that should
be added to DOLfYN, contact the development team.

DOLfYN includes a data abstraction and input/output layer that enables
saving and loading of data after it has been read from the binary
files. This data abstraction layer is designed to allow easy
input/output (loading/saving) of data along the data processing and
analysis chain. The data is written to disk in HDF5 format using the
`h5py <www.h5py.org>`_ library. Data can also be written to Matlab\
:sup:`TM` format.



Table of Contents
=================

.. toctree::
   :maxdepth: 3
   
   about
   install
   usage
   plotting-tools
   api/dolfyn
   glossary
   

Indices, tables and notes
=========================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
* :doc:`glossary`

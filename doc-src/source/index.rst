Welcome to the DOLfYN home page
================================

DOLfYN is the Doppler Oceanography Library for pYthoN.

It is designed to read and work with Acoustic Doppler Velocimeter
(ADV) and Acoustic Doppler Profiler (ADP/ADCP) data. DOLfYN includes
libraries for reading binary Nortek(tm) and Teledyne-RDI(tm) data
files.

Please document any issues and submit feature requests via the |dlfn|
:repo:`issues page<issues/>`.

DOLfYN utilizes a data abstraction and input/output layer that enables
saving and loading of data after it has been read from the binary
files. This data abstraction layer is designed to allow easy
input/output ('saving' and 'loading') data along the data processing and
analysis chain. The data is written to disk in HDF5 format using the
`h5py <www.h5py.org>`_ library. Data can also be written in Matlab\
:sup:`TM` format.



Table of Contents
=================

.. toctree::
   :maxdepth: 3
   
   about
   install
   usage
   usage-specific
   plotting-tools
   api/dolfyn
   glossary
   

Indices, tables and notes
=========================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
* :doc:`glossary`

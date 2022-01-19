.. _about:

About
-----

|dlfn| is a library of tools for reading, processing, and analyzing
data from oceanographic velocity measurement instruments such as
acoustic Doppler velocimeters (ADVs) and acoustic Doppler current profilers
(ADCPs). It includes tools to

* Read in raw ADCP/ADV datafiles
* QC velocity data 
* Rotate vector data through coordinate systems (i.e. beam to instrument to Earth to principal frames of reference)
* Motion correction for ADV velocity measurements (via onboard IMU data)
* Bin/ensemble averaging
* Turbulence statistics for ADV data

.. _about.history:


Instrument Support
^^^^^^^^^^^^^^^^^^

* Nortek:

  * AWAC ADCP (current data only, waves in development)
  * Signature AD2CP (current and waves)
  * Vector ADV

* TRDI:

  * Workhorse ADCPs (Monitor and Sentinel)
  * WinRiver output files
  * VMDAS output files

History
^^^^^^^

DOLfYN was originally created to provide open-source software for motion correction 
and turbulence analysis of velocity data collected from ADVs mounted on compliant moorings.
It has since been expanded to include reading and analyzing ADCP data.

License
^^^^^^^
DOLfYN is released Apache License 2.0 (see the LICENSE.txt file in the
:repo:`repository <>`).


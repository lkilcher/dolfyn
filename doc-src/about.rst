.. _about:

About
-----
|dlfn| is a library of tools for reading, processing, and analyzing
data from oceanographic velocity measurement instruments such as
acoustic Doppler velocimeters (ADVs) and acoustic Doppler current profilers
(ADCPs). It includes tools to

* Read in binary data files from Nortek and Teledyne RD Instruments:

   * Nortek AWAC, Signature, & Vector
   * TRDI Workhorse (Monitor & Sentinel)
   
* Clean velocity data 
* Rotate vector data through coordinate systems (i.e. beam to instrument to Earth frames of reference)
* Motion correction for buoy-mounted ADV velocity measurements (via onboard IMU data)
* Bin/ensemble averaging
* Calculate turbulence statistics

.. _about.history:

History
^^^^^^^

DOLfYN was originally created to provide open-source software for analyzing turbulence data
from ADVs mounted on compliant moorings, and has since been expanded to include reading and analyzing ADCP data.


License
^^^^^^^
DOLfYN is released Apache License 2.0 (see the LICENSE.txt file in the
:repo:`repository <>`).


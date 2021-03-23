.. _about:

About
-----
|dlfn| is a library of tools for reading, processing, and analyzing
data from oceanographic velocity measurement instruments such as
acoustic Doppler velocimeters (ADVs) and acoustic Doppler current profilers
(ADCPs). It includes tools to

* Read in binary data files from Nortek and Teledyne RD Instruments

   * Nortek AWAC, Signature, Vector
   * TRDI Workhorse (Monitor & Sentinel)
   
* Clean velocity data 
* Coordinate system rotation for vector data (beam to instrument to Earth frames of reference)
* Motion correction for buoy-mounted ADV velocity measurements (via onboard IMU data)
* Ensemble averaging
* Turbulence statistics (ADV only)

.. _about.history:

History
^^^^^^^

DOLfYN was originally created to provide open-source software for analyzing turbulence data
from ADVs mounted on compliant moorings, and has since been expanded to include reading and analyzing ADCP data.

.. [Kilcher_etal_2016] Kilcher, L., Thomson, J., Talbert, J., DeKlerk, A. (2016).
   "Measuring Turbulence from Moored Acoustic Doppler Velocimeters".
   National Renewable Energy Lab, 
   `Report Number 62979 <http://www.nrel.gov/docs/fy16osti/62979.pdf>`_.
   
.. [Harding_etal_2017] Harding, S., Kilcher, L., Thomson, J. (2017).
   Turbulence Measurements from Compliant Moorings. Part I: Motion Characterization.
   *Journal of Atmospheric and Oceanic Technology*, 34(6), 1235-1247.
   doi: 10.1175/JTECH-D-16-0189.1
	
.. [Kilcher_etal_2017] Kilcher, L., Thomson, J., Harding, S., & Nylund, S. (2017).
   Turbulence Measurements from Compliant Moorings. Part II: Motion Correction.
   *Journal of Atmospheric and Oceanic Technology*, 34(6), 1249-1266.
   doi: 10.1175/JTECH-D-16-0213.1


License
^^^^^^^
DOLfYN is released Apache License 2.0 (see the LICENSE.txt file in the
:repo:`repository <>`).


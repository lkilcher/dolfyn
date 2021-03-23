.. |pm|   unicode:: U+00B1 .. PLUS-MINUS SIGN

.. _motion-correction:

ADV Motion Correction
=====================

The Nortek Vector ADV can be purchased with an Inertial Motion Unit
(IMU) that measures the ADV motion. These measurements can be used to
remove motion from ADV velocity measurements when the ADV is mounted
on a moving platform (e.g. a mooring). This approach has been found to
be effective for removing high-frequency motion from ADV measurements,
but cannot remove low-frequency (:math:`\lesssim` 0.03Hz) motion
because of bias-drift inherent in IMU accelerometer sensors that
contaminates motion estimates at those frequencies.

This documentation is designed to document the methods for performing
motion correction of ADV-IMU measurements. The accuracy and
applicability of these measurements is beyond the scope of this
documentation (journal articles are forthcoming).

Nortek's Signature ADCP's are now also available with an IMU, but
|dlfn| does not yet support motion correction of ADP data. I hope to
remedy this soon.

Pre-Deployment Requirements
...........................

In order to perform motion correction the ADV-IMU must be assembled
and configured correctly:

1. The ADV *head* must be rigidly connected to the ADV *pressure case*.

2. The ADV software must be configured properly.  In the 'Deployment
   Planning' frame of the Vector Nortek Software, be sure that:

   a. The IMU sensor is enabled (checkbox) and set to record *'dAng dVel Orient'*.

   b. The 'Coordinate system' must be set to *'XYZ'*.

   c. It is recommended to set the ADV velocity range to |pm| *4 m/s*,
      or larger.

3. For cable-head ADVs be sure to record the position and orientation
   of the ADV head relative to the ADV pressure case 'inst' coordinate
   system (Figure 1). This information is specified in terms of the
   following variables:

   inst2head_rotmat
     The rotation matrix (a 3-by-3 array) that rotates vectors in the
     'inst' coordinate system, to the ADV
     'head' coordinate system. For fixed-head ADVs this is the identify
     matrix, but for cable-head ADVs it is an arbitrary unimodular
     (determinant of 1) matrix. This property must be in the
     ``dat.props`` in order to do motion correction.

   inst2head_vec
     The 3-element vector that specifies the position of the ADV head in
     the inst coordinate system (Figure 1). This property must be in
     ``dat.props`` in order to do motion correction.

   These variables are set in either the `userdata.json file
   <json-userdata>`_ (prior to calling ``dolfyn.read``), or by setting
   them explicitly after the data file has been read::

     dat.set_inst2head_rotmat(<3x3 rotation matrix>)
     dat.props['inst2head_vec'] = [3-element vector]
     
.. figure:: pic/adv_coord_sys3_warr.png
   :align: center
   :scale: 60%
   :alt: ADV head and inst coordinate systems.
   :figwidth: 560px

   The ADV 'inst' (magenta) and head (yellow) coordinate
   systems. The :math:`\hat{x}^\mathrm{head}` -direction is known by
   the black-band around the transducer arm, and the
   :math:`\hat{x}^*` -direction is marked by a notch on the end-cap
   (indiscernible in the image). The cyan arrow indicates the
   ``inst2head_vec`` vector :math:`\vec{\ell}_{head}^*` .  The perspective
   slightly distorts the fact that :math:`\hat{x}^\mathrm{head}
   \parallel - \hat{z}^*` , :math:`\hat{y}^\mathrm{head} \parallel
   -\hat{y}^*` , and :math:`\hat{z}^\mathrm{head} \parallel
   -\hat{x}^*` .

Data processing
...............

After making ADV-IMU measurements, the |dlfn| package can perform
motion correction processing steps on the ADV data. Assuming you have
created a ``../dolfyn/example_data/vector_data_imu01.userdata.json`` file 
(to go with your ``vector_data_imu01.vec`` data file) and it contains entries 
for ``inst2head_rotmat`` and ``inst2head_vec`` attributes to it, motion
correction is fairly simple, you can either:

1. Utilize the |dlfn| api perform motion-correction processing
   explicitly in Python::

     import dolfyn.adv as adv

   a. Load your data file, for example::

        dat = adv.read('vector_data_imu01.vec')

   b. Then perform motion correction::

        adv.motion.correct_motion(dat, accel_filtfreq=0.1) # specify the filter frequency in Hz.

2. For users who want to perform motion correction with minimal Python
   scripting, the :repo:`motcorrect_vectory.py
   <tree/master/scripts/motcorrect_vector.py>` script can be used. So long as
   |dlfn| has been `installed properly <install>`_, you can use this
   script from the command line in a directory which contains your
   data files::

        $ python motcorrect_vector.py vector_data_imu01.vec

   By default this will write a Matlab file containing your
   motion-corrected ADV data in ENU coordinates. Note that for
   fixed-stem ADVs (no cable-head), the standard values for
   ``inst2head_rotmat`` and ``inst2head_vec`` can be specified by
   using the ``--fixed-head`` command-line parameter::
     
        $ python motcorrect_vector.py --fixed-head vector_data_imu01.vec

   Otherwise, these parameters should be specified in the
   ``.userdata.json`` file, as described above.

   The motcorrect_vector.py script also allows the user to specify the
   ``accel_filtfreq`` using the ``-f`` flag.  Therefore, to use a
   filter frequency of 0.1Hz (as opposed to the default 0.033Hz), you
   could do::
     
     $ python motcorrect_vector.py -f 0.1 vector_data_imu01.vec

   It is also possible to do motion correction of multiple data files
   at once, for example::

     $ python motcorrect_vector.py vector_data_imu01.vec vector_data_imu02.vec

   In all of these cases the script will perform motion correction on
   the specified file and save the data in ENU coordinates, in Matlab
   format.  Happy motion-correcting!

After following one of these paths, your data will be motion corrected and it's ``.u``,
``.v`` and ``.w`` attributes are in an East, North and Up (ENU)
coordinate system, respectively.  In fact, all vector quantities
in ``dat`` are now in this ENU coordinate system.  See the
documentation of the :func:`~dolfyn.adv.motion.correct_motion`
function for more information.

A key input parameter of motion-correction is the high-pass filter
frequency that removes low-frequency bias drift from the IMU
accelerometer signal (the default value is 0.033Hz, 30second
period). By default, |dlfn| uses a value of 0.03 Hz. For more details
on choosing the appropriate value for a particular application, please
see [Kilcher_etal_2016]_.

.. [Kilcher_etal_2016] Kilcher, L.; Thomson, J.; Talbert, J.; DeKlerk, A.; 2016,
   "Measuring Turbulence from Moored Acoustic
   Doppler Velocimeters" National Renewable Energy
   Lab, `Report Number 62979
   <http://www.nrel.gov/docs/fy16osti/62979.pdf>`_.
   

ADV head-to-body rotation matrix example
........................................

.. figure:: pic/turbulence_torpedo.png
   :align: center
   :scale: 60%
   :alt: ADV mounted on a Columbus-type sounding weight.
   
   ADV mounted on a Columbus-type sounding weight.

An example 'userdata.json' file corresponding to Figure 2 would look like:

.. code-block:: text

	{"inst2head_rotmat": [[0, 0, 1],
	                     [ 0, 1, 0],
	                     [-1, 0, 0]],
	 "inst2head_vec": [0.20, 0, 0.04],
	 "declination": 15.87,
	 "lat": 48.08,
	 "lon": -123.04,
	 "depth": 8
	}


Motion Correction Full Examples
...............................

The two following examples depict the standard workflow for analyzing
ADV-IMU data using |dlfn|.

Example 1
"""""""""
.. literalinclude:: ../examples/adv_example.py

Example 2
"""""""""
.. literalinclude:: ../examples/adv_example2.py

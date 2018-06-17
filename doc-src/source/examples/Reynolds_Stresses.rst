Calculating Reynold's stresses (RSes)
============================

ADV
----

It is recommended that Reynold's stresses are calculated in the Earth frame. This works for both moving, and stationary ADVs. Need to add checks on this somehow?

ADP
---

The Stacey method only works in the instrument reference frame. Thus, to rotate back to a stationary frame after averaging is problematic. So, you can't really calculate RSes using moving ADPs. Perhaps we can check/screen for motion magnitude with the magnitude of the `1 - np.linalg.det(orientmat)` (after averaging)?

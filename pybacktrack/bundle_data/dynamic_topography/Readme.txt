Dynamic topography models
=========================
All models are in the 'mantle' reference frame (instead of 'plate' reference frame) and hence the
well location must be reconstructed before sampling time-dependent dynamic topography grids.

The time-dependent grid files are in the 'models/' sub-directory.
The files needed to reconstruct well locations are in the 'reconstructions/' sub-directory - they are
in a separate sub-directory because some of these reconstructions are shared by more than one model.

This data (model and reconstructions) was obtained from Michael Chin and is the data used
in his GPlates Web Portal. The mantle-frame grids were subsequently down-sampled using
'misc/convert_to_netcdf4.py' which essentially amounts to 'gmt grdfilter input.nc -Goutput.nc -D4 -Fc200 -I1'
to create 1 degree resolution grids where the cosine filter width is 200km (radius 100km).
Also the multipoint grids (used by GPlates Web Portal to convert mantle-frame to plate-frame) were
tested against the static polygons, using 'misc/test_multipoint_came_from_static_polygons.py',
to make sure we associated the correct static polygons with each model.



Cao et al., 2019
----------------
Cao, W., Flament, N., Zahirovic, S., Williams, S. and Müller, R.D. 2019. The interplay of dynamic topography and eustasy on continental flooding in the late Paleozoic. Tectonophysics. 761. 10.1016/j.tecto.2019.04.018. 

Models: AY18, KM16.


Müller et al., 2017
-------------------
Müller R.D., Hassan, R., Gurnis, M., Flament, N., and Williams, S.E., 2017, Dynamic topography of passive continental margins and their hinterlands since the Cretaceous, Gondwana Research, in press, accepted 21 March 2017.

Models: M1, M2, M3, M4, M5, M6, M7.


Rubey et al., 2017
------------------
Rubey, M., Brune, S., Heine, C., Davies, D. R., Williams, S. E., and Müller R. D.: Global patterns of Earth's dynamic topography since the Jurassic, Solid Earth Discuss., doi:10.5194/se-2017-26, in review, 2017.

Models: terra.


Müller et al., 2008
-------------------
Müller, R.D., Sdrolias, M., Gaina, C., Steinberger, B. and Heine, C., 2008. Long-term sea-level fluctuations driven by ocean basin dynamics. science, 319(5868), pp.1357-1362.

Models: ngrand, s20rts, smean.

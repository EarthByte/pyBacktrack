# PyBacktrack

A tool for reconstructing paleobathymetry on oceanic and continental crust.

## Documentation

Documentation can be found at http://pybacktrack.readthedocs.io

## Scripts

In all scripts use the "-h" option to see full details (eg, "python -m pybacktrack.backtrack -h").

### age_to_depth

Convert age to basement depth in ocean basins.

For example:

```
  python -m pybacktrack.age_to_depth -m GDH1 -r tests/data/test_ages.txt tests/data/test_depths_from_ages.txt
```

Currently supports two models:

* Stein and Stein 1992 (GDH1)
* Crosby et al. 2006

### interpolate

Interpolate a model of age-to-depth (linear segments) at given depths (stratigraphic layer boundaries) to get interpolated ages.

For example, to read a file (from standard input) containing depths and write a file (via standard output) containing interpolated ages and those depths:

```
  python -m pybacktrack.util.interpolate -cx 1 -cy 0 -r -c tests/data/ODP-114-699_age-depth-model.txt tests/data/ODP-114-699_strat_boundaries.txt tests/data/ODP-114-699_strat_boundaries_age_depth.txt
```

Note that it's a general interpolate script for piecewise linear y=f(x), so can be used for other types of data (hence the extra options).

### backstrip

Find tectonic subsidence from paleo water depths near passive margins.

For example:

```
  # FIXME: Need a site with min/max paleo water depths for backstripping.
  #
  # python -m pybacktrack.backstrip -w tests/data/DSDP-36-327-Lithology.txt -l pybacktrack/bundle_data/lithologies/lithologies.txt -c 0 1 2 3 6 -d age compacted_depth compacted_thickness decompacted_thickness average_tectonic_subsidence average_water_depth lithology -s pybacktrack/bundle_data/sediment_thickness/sedthick_world_v3_5min_epsg4326_cf.nc -o tests/data/DSDP-36-327_backstrip_amended.txt -- tests/data/DSDP-36-327_backstrip_decompat.txt
```

### backtrack

Find paleo water depths from tectonic subsidence model (age-to-depth curve in ocean basins, and rifting near passive margins).

Ocean basin example using bundled data (via the 'backtrack_bundle' module):

```
  python -m pybacktrack.backtrack_bundle -w tests/data/ODP-114-699-Lithology.txt -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density water_depth tectonic_subsidence lithology -y M2 -sl Haq87_SealevelCurve_Longterm -o tests/data/ODP-114-699_backtrack_amended.txt -- tests/data/ODP-114-699_backtrack_decompat.txt
```

...the equivalent example using the 'backtrack' module is...

```
  python -m pybacktrack.backtrack -w tests/data/ODP-114-699-Lithology.txt -l pybacktrack/bundle_data/lithologies/lithologies.txt -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density water_depth tectonic_subsidence lithology -a pybacktrack/bundle_data/age/agegrid_6m.grd -t pybacktrack/bundle_data/topography/ETOPO1_0.1.grd -s pybacktrack/bundle_data/sediment_thickness/sedthick_world_v3_5min_epsg4326_cf.nc -k pybacktrack/bundle_data/crustal_thickness/crsthk.grd -y pybacktrack/bundle_data/dynamic_topography/models/M2.grids pybacktrack/bundle_data/dynamic_topography/reconstructions/2013.2-r213/static_polygons.shp pybacktrack/bundle_data/dynamic_topography/reconstructions/2013.2-r213/rotations.rot -sl pybacktrack/bundle_data/sea_level/Haq87_SealevelCurve_Longterm.dat -o tests/data/ODP-114-699_backtrack_amended.txt -- tests/data/ODP-114-699_backtrack_decompat.txt
```
  
Passive margin example using bundled data (via the 'backtrack_bundle' module):

```
  python -m pybacktrack.backtrack_bundle -w tests/data/DSDP-36-327-Lithology.txt -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density water_depth tectonic_subsidence lithology -y M2 -sl Haq87_SealevelCurve_Longterm -o tests/data/DSDP-36-327_backtrack_amended.txt -- tests/data/DSDP-36-327_backtrack_decompat.txt
```

...the equivalent example using the 'backtrack' module is...

```
  python -m pybacktrack.backtrack -w tests/data/DSDP-36-327-Lithology.txt -l pybacktrack/bundle_data/lithologies/lithologies.txt -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density water_depth tectonic_subsidence lithology -a pybacktrack/bundle_data/age/agegrid_6m.grd -t pybacktrack/bundle_data/topography/ETOPO1_0.1.grd -s pybacktrack/bundle_data/sediment_thickness/sedthick_world_v3_5min_epsg4326_cf.nc -k pybacktrack/bundle_data/crustal_thickness/crsthk.grd -y pybacktrack/bundle_data/dynamic_topography/models/M2.grids pybacktrack/bundle_data/dynamic_topography/reconstructions/2013.2-r213/static_polygons.shp pybacktrack/bundle_data/dynamic_topography/reconstructions/2013.2-r213/rotations.rot -sl pybacktrack/bundle_data/sea_level/Haq87_SealevelCurve_Longterm.dat -o tests/data/DSDP-36-327_backtrack_amended.txt -- tests/data/DSDP-36-327_backtrack_decompat.txt
```

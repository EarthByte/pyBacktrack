# PyBacktrack

A tool for reconstructing paleobathymetry on oceanic and continental crust.

## Scripts

In all scripts use the "-h" option to see full details (eg, "python backtrack.py -h").

### age_to_depth

Convert age to basement depth in ocean basins.

For example:

```
  python age_to_depth.py -m GDH1 < lon_lat_age.xy > lon_lat_depth.xy
```

Currently supports two models:

* Stein and Stein 1992 (GDH1)
* Crosby et al. 2006

### interpolate

Interpolate a model of age-to-depth (linear segments) at given depths (stratigraphic layer boundaries) to get interpolated ages.

For example, to read a file (from standard input) containing depths and write a file (via standard output) containing interpolated ages and those depths:

```
  python interpolate.py -cx 1 -cy 0 -r -c test_data/ODP-114-699_age-depth-model.txt < test_data/ODP-114-699_strat_boundaries.txt > test_data/ODP-114-699_strat_boundaries_age_depth.txt
```

Note that it's a general interpolate script for piecewise linear y=f(x), so can be used for other types of data (hence the extra options).

### backstrip

Find tectonic subsidence from paleo water depths near passive margins.

For example:

```
  # FIXME: Need a site with min/max paleo water depths for backstripping.
  #
  # python backstrip.py -w test_data/DSDP-36-327-Lithology.txt -l bundle_data/lithologies/lithologies.txt -c 0 1 2 3 6 -d age compacted_depth compacted_thickness decompacted_thickness average_tectonic_subsidence average_water_depth lithology -s bundle_data/sediment_thickness/sedthick_world_v3_5min_epsg4326_cf.nc -o test_data/DSDP-36-327_backstrip_amended.txt -- test_data/DSDP-36-327_backstrip_decompat.txt
```

### backtrack

Find paleo water depths from tectonic subsidence model (age-to-depth curve in ocean basins, and rifting near passive margins).

Ocean basin example using bundled data (via 'backtrack_bundle.py'):

```
  python backtrack_bundle.py -w test_data/ODP-114-699-Lithology.txt -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density water_depth tectonic_subsidence lithology -y M2 -sl Haq87_SealevelCurve_Longterm -o test_data/ODP-114-699_backtrack_amended.txt -- test_data/ODP-114-699_backtrack_decompat.txt
```

...the equivalent example using 'backtrack.py' is...

```
  python backtrack.py -w test_data/ODP-114-699-Lithology.txt -l bundle_data/lithologies/lithologies.txt -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density water_depth tectonic_subsidence lithology -a bundle_data/age/agegrid_6m.grd -t bundle_data/topography/ETOPO1_0.1.grd -s bundle_data/sediment_thickness/sedthick_world_v3_5min_epsg4326_cf.nc -k bundle_data/crustal_thickness/crsthk.grd -y bundle_data/dynamic_topography/models/M2.grids bundle_data/dynamic_topography/reconstructions/Global_Model_WD_Internal_Release_2013.2-r213/Static_Polygons_Merged_01_07_2013.shp bundle_data/dynamic_topography/reconstructions/Global_Model_WD_Internal_Release_2013.2-r213/Global_EarthByte_TPW_CK95G94_2013.2.rot -sl Haq87_SealevelCurve_Longterm.dat -o test_data/ODP-114-699_backtrack_amended.txt -- test_data/ODP-114-699_backtrack_decompat.txt
```
  
Passive margin example using bundled data (via 'backtrack_bundle.py'):

```
  python backtrack_bundle.py -w test_data/DSDP-36-327-Lithology.txt -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density water_depth tectonic_subsidence lithology -y M2 -sl Haq87_SealevelCurve_Longterm -o test_data/DSDP-36-327_backtrack_amended.txt -- test_data/DSDP-36-327_backtrack_decompat.txt
```

...the equivalent example using 'backtrack.py' is...

```
  python backtrack.py -w test_data/DSDP-36-327-Lithology.txt -l bundle_data/lithologies/lithologies.txt -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density water_depth tectonic_subsidence lithology -a bundle_data/age/agegrid_6m.grd -t bundle_data/topography/ETOPO1_0.1.grd -s bundle_data/sediment_thickness/sedthick_world_v3_5min_epsg4326_cf.nc -k bundle_data/crustal_thickness/crsthk.grd -y bundle_data/dynamic_topography/models/M2.grids bundle_data/dynamic_topography/reconstructions/Global_Model_WD_Internal_Release_2013.2-r213/Static_Polygons_Merged_01_07_2013.shp bundle_data/dynamic_topography/reconstructions/Global_Model_WD_Internal_Release_2013.2-r213/Global_EarthByte_TPW_CK95G94_2013.2.rot -sl Haq87_SealevelCurve_Longterm.dat -o test_data/DSDP-36-327_backtrack_amended.txt -- test_data/DSDP-36-327_backtrack_decompat.txt
```

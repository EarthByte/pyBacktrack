.. _pygplates_examples:

Examples
========

This document contains examples of how to use scripts inside the ``pytrackback`` package and how to import and use its functions.

.. contents::
   :local:
   :depth: 2

Scripts
-------

In all scripts use the ``--help`` option to see full details (eg, ``python -m pybacktrack.backtrack --help``).

age_to_depth
^^^^^^^^^^^^

Convert age to basement depth in ocean basins.

For example:

.. code-block:: python

    python -m pybacktrack.age_to_depth \
        -m GDH1 \
        -r \
        tests/data/test_ages.txt \
        tests/data/test_depths_from_ages.txt

Currently supports two models:

* Stein and Stein 1992 (GDH1)
* Crosby et al. 2006

interpolate
^^^^^^^^^^^

Interpolate a model of age-to-depth (linear segments) at given depths (stratigraphic layer boundaries) to get interpolated ages.

For example, to read a file containing depths and write a file containing interpolated ages and those depths:

.. code-block:: python

    python -m pybacktrack.util.interpolate \
        -cx 1 \
        -cy 0 \
        -r \
        -c tests/data/ODP-114-699_age-depth-model.txt \
        tests/data/ODP-114-699_strat_boundaries.txt \
        tests/data/ODP-114-699_strat_boundaries_age_depth.txt

.. note::This is a general interpolate script for piecewise linear ``y=f(x)``, so can be used for other types of data (hence the extra options).

backstrip
^^^^^^^^^

Find tectonic subsidence from paleo water depths near passive margins.

For example:

.. code-block:: python

    python -m pybacktrack.backstrip \
        -w tests/data/DSDP-36-327-Lithology.txt \
        -l pybacktrack/bundle_data/lithologies/lithologies.txt \
        -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density average_tectonic_subsidence average_water_depth lithology \
        -s pybacktrack/bundle_data/sediment_thickness/sedthick_world_v3_5min_epsg4326_cf.nc \
        -sl pybacktrack/bundle_data/sea_level/Haq87_SealevelCurve_Longterm.dat \
        -o tests/data/DSDP-36-327_backstrip_amended.txt \
        -- \
        tests/data/DSDP-36-327_backstrip_decompat.txt

backtrack
^^^^^^^^^

Find paleo water depths from tectonic subsidence model (age-to-depth curve in ocean basins, and rifting near passive margins).

Ocean basin example:

.. code-block:: python

    python -m pybacktrack.backtrack \
        -w tests/data/ODP-114-699-Lithology.txt \
        -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density water_depth tectonic_subsidence lithology \
        -ym M2 \
        -slm Haq87_SealevelCurve_Longterm \
        -o tests/data/ODP-114-699_backtrack_amended.txt \
        -- \
        tests/data/ODP-114-699_backtrack_decompat.txt

Passive margin example:

.. code-block:: python

    python -m pybacktrack.backtrack \
        -w tests/data/DSDP-36-327-Lithology.txt \
        -c 0 1 4 \
        -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density water_depth tectonic_subsidence lithology \
        -ym M2 \
        -slm Haq87_SealevelCurve_Longterm \
        -o tests/data/DSDP-36-327_backtrack_amended.txt \
        -- \
        tests/data/DSDP-36-327_backtrack_decompat.txt

And since the above examples default to using the internal :ref:`bundled data<pybacktrack_bundle_data>` they are equivalent to the following longer versions...

Ocean basin example:

.. code-block:: python

    python -m pybacktrack.backtrack \
        -w tests/data/ODP-114-699-Lithology.txt \
        -l pybacktrack/bundle_data/lithologies/lithologies.txt \
        -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density water_depth tectonic_subsidence lithology \
        -a pybacktrack/bundle_data/age/agegrid_6m.grd \
        -t pybacktrack/bundle_data/topography/ETOPO1_0.1.grd \
        -s pybacktrack/bundle_data/sediment_thickness/sedthick_world_v3_5min_epsg4326_cf.nc \
        -k pybacktrack/bundle_data/crustal_thickness/crsthk.grd \
        -y pybacktrack/bundle_data/dynamic_topography/models/M2.grids \
           pybacktrack/bundle_data/dynamic_topography/reconstructions/2013.2-r213/static_polygons.shp \
           pybacktrack/bundle_data/dynamic_topography/reconstructions/2013.2-r213/rotations.rot \
        -sl pybacktrack/bundle_data/sea_level/Haq87_SealevelCurve_Longterm.dat \
        -o tests/data/ODP-114-699_backtrack_amended.txt \
        -- \
        tests/data/ODP-114-699_backtrack_decompat.txt

Passive margin example:

.. code-block:: python

    python -m pybacktrack.backtrack \
        -w tests/data/DSDP-36-327-Lithology.txt \
        -c 0 1 4 \
        -l pybacktrack/bundle_data/lithologies/lithologies.txt \
        -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density water_depth tectonic_subsidence lithology \
        -a pybacktrack/bundle_data/age/agegrid_6m.grd \
        -t pybacktrack/bundle_data/topography/ETOPO1_0.1.grd \
        -s pybacktrack/bundle_data/sediment_thickness/sedthick_world_v3_5min_epsg4326_cf.nc \
        -k pybacktrack/bundle_data/crustal_thickness/crsthk.grd \
        -y pybacktrack/bundle_data/dynamic_topography/models/M2.grids \
           pybacktrack/bundle_data/dynamic_topography/reconstructions/2013.2-r213/static_polygons.shp \
           pybacktrack/bundle_data/dynamic_topography/reconstructions/2013.2-r213/rotations.rot \
        -sl pybacktrack/bundle_data/sea_level/Haq87_SealevelCurve_Longterm.dat \
        -o tests/data/DSDP-36-327_backtrack_amended.txt \
        -- \
        tests/data/DSDP-36-327_backtrack_decompat.txt

...which demonstrates how you can use your own data instead of the bundled data (ie, by replacing files prefixed with ``pybacktrack/bundle_data/`` with your own).

.. note:: Also note the use of ``-y`` and ``-sl`` options instead of the simpler ``-ym`` and ``-slm`` command-line options.

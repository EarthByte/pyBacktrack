.. _pygplates_examples:

Examples
========

This document contains examples of how to use scripts inside the ``pybacktrack`` package and how to import and use its functions.

.. contents::
   :local:
   :depth: 2

Scripts
-------

In all scripts use the ``--help`` option to see full details (eg, ``python -m pybacktrack.backtrack --help``).

.. note:: | The input files used in the examples below are available from the ``tests/data/`` directory of the `pyBacktrack source code <https://github.com/EarthByte/pyBacktrack>`_.
          | If you want to run these examples you can download that test data, or you can use your own input files (such as your own ocean drill site files).

age_to_depth
^^^^^^^^^^^^

Convert age to basement depth in ocean basins.

For example:

.. code-block:: python

    python -m pybacktrack.age_to_depth \
        -m GDH1 \
        -r \
        tests/data/test_ages.txt \
        test_depths_from_ages.txt

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
        ODP-114-699_strat_boundaries_age_depth.txt

.. note::This is a general interpolate script for piecewise linear ``y=f(x)``, so can be used for other types of data (hence the extra options).

backstrip
^^^^^^^^^

Find tectonic subsidence from paleo water depths near passive margins.

For example:

.. code-block:: python

    python -m pybacktrack.backstrip \
        -w tests/data/DSDP-36-327-Lithology.txt \
        -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density average_tectonic_subsidence average_water_depth lithology \
        -slm Haq87_SealevelCurve_Longterm \
        -o DSDP-36-327_backstrip_amended.txt \
        -- \
        DSDP-36-327_backstrip_decompat.txt

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
        -o ODP-114-699_backtrack_amended.txt \
        -- \
        ODP-114-699_backtrack_decompat.txt

Passive margin example:

.. code-block:: python

    python -m pybacktrack.backtrack \
        -w tests/data/DSDP-36-327-Lithology.txt \
        -c 0 1 4 \
        -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density water_depth tectonic_subsidence lithology \
        -ym M2 \
        -slm Haq87_SealevelCurve_Longterm \
        -o DSDP-36-327_backtrack_amended.txt \
        -- \
        DSDP-36-327_backtrack_decompat.txt

There are more command-line options available for ``backstrip`` and ``backtrack``. The above examples just rely on default values for these extra options. To see a description of all options run:

.. code-block:: python

    python -m pybacktrack.backstrip --help
    python -m pybacktrack.backtrack --help

For example, if you want to run the passive margin backtrack example with your own global topography/bathymetry grid (instead of the default :ref:`bundled topography grid<pybacktrack_bundle_data>`)
then you could add the ``-t`` command-line option to specify your own GMT5-compatible topography grid ``my_topography.grd``:

.. code-block:: python

    python -m pybacktrack.backtrack \
        -w tests/data/DSDP-36-327-Lithology.txt \
        -c 0 1 4 \
        -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density water_depth tectonic_subsidence lithology \
        -t my_topography.grd \
        -ym M2 \
        -slm Haq87_SealevelCurve_Longterm \
        -o DSDP-36-327_backtrack_amended.txt \
        -- \
        DSDP-36-327_backtrack_decompat.txt

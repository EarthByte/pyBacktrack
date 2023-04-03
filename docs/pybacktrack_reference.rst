.. _pybacktrack_reference:

Reference
=========

This section documents the Python functions and classes that make up the public interface of the *pybacktrack* package.

.. contents::
   :local:
   :depth: 3

The ``pybacktrack`` package has the ``__version__`` attribute:
::

    import pybacktrack
    
    pybacktrack.__version__


.. _pybacktrack_reference_backtracking:

Backtracking
------------

Find decompacted total sediment thickness and water depth through time.

Summary
^^^^^^^

:func:`pybacktrack.backtrack_well` finds decompacted total sediment thickness and water depth for each age in a well.

:func:`pybacktrack.write_backtrack_well` writes decompacted parameters as columns in a text file.

:func:`pybacktrack.backtrack_and_write_well` both backtracks well and writes decompacted data.

Detail
^^^^^^

.. autofunction:: pybacktrack.backtrack_well

.. autofunction:: pybacktrack.write_backtrack_well

.. autofunction:: pybacktrack.backtrack_and_write_well


.. _pybacktrack_reference_backstripping:

Backstripping
-------------

Find decompacted total sediment thickness and tectonic subsidence through time.

Summary
^^^^^^^

:func:`pybacktrack.backstrip_well` finds decompacted total sediment thickness and tectonic subsidence for each age in a well.

:func:`pybacktrack.write_backstrip_well` writes decompacted parameters as columns in a text file.

Detail
^^^^^^

.. autofunction:: pybacktrack.backstrip_well

.. autofunction:: pybacktrack.write_backstrip_well

.. autofunction:: pybacktrack.backstrip_and_write_well


.. _pybacktrack_reference_paleobathymetry:

Paleobathymetry
---------------

Generate paleo bathymetry grids through time.

Summary
^^^^^^^

:func:`pybacktrack.generate_lon_lat_points` generates a global grid of points uniformly spaced in longitude and latitude.

:func:`pybacktrack.reconstruct_paleo_bathymetry` reconstructs and backtracks sediment-covered crust through time to get paleo bathymetry.

:func:`pybacktrack.write_paleo_bathymetry_grids` grid paleo bathymetry into NetCDF grids files.

:func:`pybacktrack.reconstruct_paleo_bathymetry_grids` generates a global grid of points, reconstructs/backtracks their bathymetry and writes paleo bathymetry grids.

Detail
^^^^^^

.. autofunction:: pybacktrack.generate_lon_lat_points

.. autofunction:: pybacktrack.reconstruct_paleo_bathymetry

.. autofunction:: pybacktrack.write_paleo_bathymetry_grids

.. autofunction:: pybacktrack.reconstruct_paleo_bathymetry_grids


.. _pybacktrack_reference_creating_lithologies:

Creating lithologies
--------------------

Create lithologies or read them from file(s).

Summary
^^^^^^^

:class:`pybacktrack.Lithology` is a class containing data for a lithology.

:func:`pybacktrack.read_lithologies_file` reads lithologies from a text file.

:func:`pybacktrack.read_lithologies_files` reads and merges lithologies from one or more text files.

:func:`pybacktrack.create_lithology` creates a lithology by looking up a name in a dictionary of lithologies.

:func:`pybacktrack.create_lithology_from_components` creates a lithology by combining multiple lithologies using different weights.

Detail
^^^^^^

.. autoclass:: pybacktrack.Lithology
   :members:
   :special-members: __init__

.. autofunction:: pybacktrack.read_lithologies_file

.. autofunction:: pybacktrack.read_lithologies_files

.. autofunction:: pybacktrack.create_lithology

.. autofunction:: pybacktrack.create_lithology_from_components


.. _pybacktrack_reference_decompacting_well_sites:

Decompacting well sites
-----------------------

* :ref:`Read/write well site files <pybacktrack_reference_read_write_well_sites>`,
* :ref:`query a well and its stratigraphic layers <pybacktrack_reference_compacted_well>`, and
* :ref:`query decompacted sections at past times <pybacktrack_reference_decompacted_well>`.

.. _pybacktrack_reference_read_write_well_sites:

Reading and writing well files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Read/write well site files.

Summary
"""""""

:func:`pybacktrack.read_well_file` reads a text file with each row representing a stratigraphic unit.

:func:`pybacktrack.write_well_file` writes a text file with each row representing a stratigraphic unit.

:func:`pybacktrack.write_well_metadata` writes well metadata to a text file.

Detail
""""""

.. autofunction:: pybacktrack.read_well_file

.. autofunction:: pybacktrack.write_well_file

.. autofunction:: pybacktrack.write_well_metadata

.. _pybacktrack_reference_compacted_well:

Compacted well
^^^^^^^^^^^^^^

Query a well and its stratigraphic layers.

Summary
"""""""

:class:`pybacktrack.Well` is a class containing all stratigraphic units in a well.

:class:`pybacktrack.StratigraphicUnit` is a class containing data for a stratigraphic unit.

Detail
""""""

.. autoclass:: pybacktrack.Well
   :members:
   :special-members: __init__

.. autoclass:: pybacktrack.StratigraphicUnit
   :members:
   :special-members: __init__

.. _pybacktrack_reference_decompacted_well:

Decompacted well
^^^^^^^^^^^^^^^^

Query decompacted sections at past times.

Summary
"""""""

:class:`pybacktrack.DecompactedWell` is a class containing the decompacted well data at a specific age.

:class:`pybacktrack.DecompactedStratigraphicUnit` is a class to hold data for a *decompacted* stratigraphic unit.

Detail
""""""

.. autoclass:: pybacktrack.DecompactedWell
   :members:
   :special-members: __init__

.. autoclass:: pybacktrack.DecompactedStratigraphicUnit
   :members:
   :special-members: __init__


.. _pybacktrack_reference_converting_age_to_depth:

Converting oceanic age to depth
-------------------------------

Convert ocean basin ages (Ma) to basement depth (metres) using different age/depth models.

Summary
^^^^^^^

:func:`pybacktrack.convert_age_to_depth` converts a single ocean basin age to basement depth.

:func:`pybacktrack.convert_age_to_depth_files` converts a sequence of ages (read from an input file) to depths (and writes both ages and depths to an output file).

Detail
^^^^^^

.. autofunction:: pybacktrack.convert_age_to_depth

.. autofunction:: pybacktrack.convert_age_to_depth_files


.. _pybacktrack_reference_rifting:

Continental rifting
-------------------

Continental passive margin initial rifting subsidence and subsequent thermal subsidence.
Rifting is assumed instantaneous in that thermal contraction only happens after rifting has ended.

Summary
^^^^^^^

:func:`pybacktrack.estimate_rift_beta` estimates the stretching factor (beta).

:func:`pybacktrack.total_rift_subsidence` calcultaes the total subsidence as syn-rift plus post-rift.

:func:`pybacktrack.syn_rift_subsidence` calculates the initial subsidence due to continental stretching.

:func:`pybacktrack.post_rift_subsidence` calculates the thermal subsidence as a function of time.

Detail
^^^^^^

.. autofunction:: pybacktrack.estimate_rift_beta

.. autofunction:: pybacktrack.total_rift_subsidence

.. autofunction:: pybacktrack.syn_rift_subsidence

.. autofunction:: pybacktrack.post_rift_subsidence


.. _pybacktrack_reference_dynamic_topography:

Dynamic topography
------------------

Summary
^^^^^^^

:class:`pybacktrack.DynamicTopography` is a class that reconstructs point location(s) and samples (and interpolates) time-dependent dynamic topography *mantle* frame grids.

:class:`pybacktrack.InterpolateDynamicTopography` is a class that just samples and interpolates time-dependent dynamic topography *mantle* frame grid files.

Detail
^^^^^^

.. autoclass:: pybacktrack.DynamicTopography
   :members:
   :special-members: __init__

.. autoclass:: pybacktrack.InterpolateDynamicTopography
   :members:
   :special-members: __init__


.. _pybacktrack_reference_sea_level:

Average sea level variations
----------------------------

Read a sea level file and compute average sea level variations during time periods.

Summary
^^^^^^^

:class:`pybacktrack.SeaLevel` is a class that calculates integrated sea levels (relative to present day) over a time period.

Detail
^^^^^^

.. autoclass:: pybacktrack.SeaLevel
   :members:
   :special-members: __init__


.. _pybacktrack_reference_converting_stratigraphic_depth_to_age:

Converting stratigraphic depth to age
-------------------------------------

Convert stratigraphic depths (metres) to age (Ma) using an depth-to-age model.

Summary
^^^^^^^

:func:`pybacktrack.convert_stratigraphic_depth_to_age` converts a single stratigraphic depth to an age.

:func:`pybacktrack.convert_stratigraphic_depth_to_age_files` converts a sequence of stratigraphic depths (read from an input file) to ages
(and writes both ages and depths, and any lithologies in the input file, to an output file).

Detail
^^^^^^

.. autofunction:: pybacktrack.convert_stratigraphic_depth_to_age

.. autofunction:: pybacktrack.convert_stratigraphic_depth_to_age_files


.. _pybacktrack_reference_utilities:

Utilities
---------

Interpolate a sequence of linear segments read from a 2-column file at the values read from a 1-column file.

Summary
^^^^^^^

:func:`pybacktrack.read_interpolate_function` reads x and y columns from a curve file and returns a function y(x) that linearly interpolates.

:func:`pybacktrack.interpolate_file` interpolates a curve function at `x` positions, read from input file, and stores both `x` and interpolated `y` values to output file.

Detail
^^^^^^

.. autofunction:: pybacktrack.read_interpolate_function

.. autofunction:: pybacktrack.interpolate_file


.. _pybacktrack_reference_constants:

Constants
---------

This section covers the various pre-defined constants that can be passed to the above functions and classes.

.. _pybacktrack_reference_bundle_data:

Bundle data
^^^^^^^^^^^

The following bundled data comes included with the ``pybacktrack`` package:

- a lithologies text file
- an age grid
- a sediment thickness grid
- a crustal thickness grid
- a topography grid
- a collection of common dynamic topography models
- a couple of sea level curves

The following attributes are available to access the bundled data:

``pybacktrack.BUNDLE_PATH``
  Base directory of the bundled data.

  This is an absolute path so that scripts outside the ``pybacktrack`` package can also reference the bundled data.
  All bundle data paths are derived from this base path.

``pybacktrack.BUNDLE_LITHOLOGY_FILENAMES``
  A list of bundled lithology filenames.
  
``pybacktrack.DEFAULT_BUNDLE_LITHOLOGY_FILENAME``
  Same as ``pybacktrack.PRIMARY_BUNDLE_LITHOLOGY_FILENAME``.
  
``pybacktrack.PRIMARY_BUNDLE_LITHOLOGY_FILENAME``
  The primary lithology filename contains the lithologies covered in Table 1 in the pyBacktrack paper:

  * Müller, R. D., Cannon, J., Williams, S. and Dutkiewicz, A., 2018,
    `PyBacktrack 1.0: A Tool for Reconstructing Paleobathymetry on Oceanic and Continental Crust <https://doi.org/10.1029/2017GC007313>`_,
    **Geochemistry, Geophysics, Geosystems,** 19, 1898-1909, doi: 10.1029/2017GC007313.

``pybacktrack.EXTENDED_BUNDLE_LITHOLOGY_FILENAME``
  The optional extended lithology filename extends the primary lithologies, and mostly contains lithologies in shallow water.


``pybacktrack.BUNDLE_AGE_GRID_FILENAME``
  Bundled age grid file.

``pybacktrack.BUNDLE_TOPOGRAPHY_FILENAME``
  Bundled topography/bathymetry grid file.

``pybacktrack.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME``
  Bundled total sediment thickness grid file.

``pybacktrack.BUNDLE_CRUSTAL_THICKNESS_FILENAME``
  Bundled crustal thickness grid file.

``pybacktrack.BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS``
  Bundled dynamic topography models.

  This is a dict mapping dynamic topography model name to model information 3-tuple of (grid list filenames, static polygon filename and rotation filenames).
  Each *key* or *value* in the dict can be passed to the ``dynamic_topography_model`` argument of :func:`pybacktrack.backtrack_well` and :func:`pybacktrack.backtrack_and_write_well`.

``pybacktrack.BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_NAMES``
  A list of bundled dynamic topography model *names* (keys in `BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS`).
  
  Choices include ``terra``, ``M1``, ``M2``, ``M3``, ``M4``, ``M5``, ``M6``, ``M7``, ``ngrand``, ``s20rts``, ``smean``, ``AY18``, ``KM16``, ``D10_gmcm9`` and ``gld428``.

``pybacktrack.BUNDLE_SEA_LEVEL_MODELS``
  Bundled sea level models.

  This is a dict mapping sea level model name to sea level file.
  Each *key* or *value* in the dict can be passed to the ``sea_level_model`` argument of :func:`pybacktrack.backtrack_well` and :func:`pybacktrack.backtrack_and_write_well`.

``pybacktrack.BUNDLE_SEA_LEVEL_MODEL_NAMES``
  A list of bundled sea level model *names* (keys in `BUNDLE_SEA_LEVEL_MODELS`).
  
  Choices include ``Haq87_SealevelCurve`` and ``Haq87_SealevelCurve_Longterm``.

``pybacktrack.BUNDLE_RECONSTRUCTION_ROTATION_FILENAMES``
  Rotation files of the reconstruction model used to reconstruct sediment-deposited crust for paleobathymetry gridding.

``pybacktrack.BUNDLE_RECONSTRUCTION_STATIC_POLYGON_FILENAME``
  Static polygon file of the reconstruction model used to assign plate IDs to points on sediment-deposited crust for paleobathymetry gridding.

Backtracking
^^^^^^^^^^^^

``pybacktrack.BACKTRACK_DEFAULT_DECOMPACTED_COLUMNS``
  Default list of decompacted columns used for ``decompacted_columns`` argument of
  :func:`pybacktrack.backtrack_well` and :func:`pybacktrack.backtrack_and_write_well`.

List of column types available for the ``decompacted_columns`` argument of
:func:`pybacktrack.backtrack_well` and :func:`pybacktrack.backtrack_and_write_well`:

- ``pybacktrack.BACKTRACK_COLUMN_AGE``
- ``pybacktrack.BACKTRACK_COLUMN_COMPACTED_DEPTH``
- ``pybacktrack.BACKTRACK_COLUMN_COMPACTED_THICKNESS``
- ``pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_THICKNESS``
- ``pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_DENSITY``
- ``pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_SEDIMENT_RATE``
- ``pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_DEPTH``
- ``pybacktrack.BACKTRACK_COLUMN_DYNAMIC_TOPOGRAPHY``
- ``pybacktrack.BACKTRACK_COLUMN_TECTONIC_SUBSIDENCE``
- ``pybacktrack.BACKTRACK_COLUMN_WATER_DEPTH``
- ``pybacktrack.BACKTRACK_COLUMN_LITHOLOGY``

Backstripping
^^^^^^^^^^^^^

``pybacktrack.BACKSTRIP_DEFAULT_DECOMPACTED_COLUMNS``
  Default list of decompacted columns used for ``decompacted_columns`` argument of
  :func:`pybacktrack.backstrip_well` and :func:`pybacktrack.backstrip_and_write_well`.

List of column types available for the ``decompacted_columns`` argument of
:func:`pybacktrack.backstrip_well` and :func:`pybacktrack.backstrip_and_write_well`:

- ``pybacktrack.BACKSTRIP_COLUMN_AGE``
- ``pybacktrack.BACKSTRIP_COLUMN_DECOMPACTED_THICKNESS``
- ``pybacktrack.BACKSTRIP_COLUMN_DECOMPACTED_DENSITY``
- ``pybacktrack.BACKSTRIP_COLUMN_DECOMPACTED_SEDIMENT_RATE``
- ``pybacktrack.BACKSTRIP_COLUMN_DECOMPACTED_DEPTH``
- ``pybacktrack.BACKSTRIP_COLUMN_AVERAGE_TECTONIC_SUBSIDENCE``
- ``pybacktrack.BACKSTRIP_COLUMN_MIN_TECTONIC_SUBSIDENCE``
- ``pybacktrack.BACKSTRIP_COLUMN_MAX_TECTONIC_SUBSIDENCE``
- ``pybacktrack.BACKSTRIP_COLUMN_AVERAGE_WATER_DEPTH``
- ``pybacktrack.BACKSTRIP_COLUMN_MIN_WATER_DEPTH``
- ``pybacktrack.BACKSTRIP_COLUMN_MAX_WATER_DEPTH``
- ``pybacktrack.BACKSTRIP_COLUMN_COMPACTED_THICKNESS``
- ``pybacktrack.BACKSTRIP_COLUMN_LITHOLOGY``
- ``pybacktrack.BACKSTRIP_COLUMN_COMPACTED_DEPTH``

Paleobathymetry
^^^^^^^^^^^^^^^

``pybacktrack.DEFAULT_PALEO_BATHYMETRY_LITHOLOGY_NAME``
  Default name of the lithology of all sediment (for paleo bathymetry gridding the total sediment thickness at all
  sediment locations consists of a single lithology). This lithology is the average of the ocean floor sediment.
  This differs from the base lithology of drill sites where the undrilled portions are usually below the
  Carbonate Compensation Depth (CCD) where shale dominates.

Lithology
^^^^^^^^^

``pybacktrack.DEFAULT_BASE_LITHOLOGY_NAME``
  Default name of the lithology of the stratigraphic unit at the base of a drill site (the undrilled portion).
  This lithology is shale since the undrilled portions are usually below the Carbonate Compensation Depth (CCD) where shale dominates.

Oceanic subsidence
^^^^^^^^^^^^^^^^^^

``pybacktrack.AGE_TO_DEPTH_MODEL_RHCW18``
    Richards et al. (2020) ``Structure and dynamics of the oceanic lithosphere-asthenosphere system``.

``pybacktrack.AGE_TO_DEPTH_MODEL_CROSBY_2007``
    Crosby, A.G., (2007) ``Aspects of the relationship between topography and gravity on the Earth and Moon, PhD thesis``.

``pybacktrack.AGE_TO_DEPTH_MODEL_GDH1``
    Stein and Stein (1992) ``Model for the global variation in oceanic depth and heat flow with lithospheric age``.

``pybacktrack.AGE_TO_DEPTH_DEFAULT_MODEL``
    The age-to-depth model to use by default.

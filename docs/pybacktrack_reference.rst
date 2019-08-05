.. _pybacktrack_reference:

Reference
=========

This section documents the Python functions and classes that make up the public interface of the *pybacktrack* package.

.. contents::
   :local:
   :depth: 2

The ``pybacktrack`` package has the ``__version__`` attribute:
::

    import pybacktrack
    
    pybacktrack.__version__

.. _pybacktrack_reference_backtracking:

Backtracking
------------

.. autofunction:: pybacktrack.backtrack_well

.. autofunction:: pybacktrack.write_backtrack_well

.. autofunction:: pybacktrack.backtrack_and_write_well

Constants
^^^^^^^^^

``pybacktrack.BACKTRACK_DEFAULT_DECOMPACTED_COLUMNS``
  Default list of decompacted columns used for ``decompacted_columns`` argument of
  :func:`pybacktrack.backtrack_well` and :func:`pybacktrack.backtrack_and_write_well`.

List of column types available for the ``decompacted_columns`` argument of
:func:`pybacktrack.backtrack_well` and :func:`pybacktrack.backtrack_and_write_well`:

- ``pybacktrack.BACKTRACK_COLUMN_AGE``
- ``pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_THICKNESS``
- ``pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_DENSITY``
- ``pybacktrack.BACKTRACK_COLUMN_TECTONIC_SUBSIDENCE``
- ``pybacktrack.BACKTRACK_COLUMN_WATER_DEPTH``
- ``pybacktrack.BACKTRACK_COLUMN_COMPACTED_THICKNESS``
- ``pybacktrack.BACKTRACK_COLUMN_LITHOLOGY``
- ``pybacktrack.BACKTRACK_COLUMN_COMPACTED_DEPTH``

.. _pybacktrack_reference_backstripping:

Backstripping
-------------

.. autofunction:: pybacktrack.backstrip_well

.. autofunction:: pybacktrack.write_backstrip_well

.. autofunction:: pybacktrack.backstrip_and_write_well

Constants
^^^^^^^^^

``pybacktrack.BACKSTRIP_DEFAULT_DECOMPACTED_COLUMNS``
  Default list of decompacted columns used for ``decompacted_columns`` argument of
  :func:`pybacktrack.backstrip_well` and :func:`pybacktrack.backstrip_and_write_well`.

List of column types available for the ``decompacted_columns`` argument of
:func:`pybacktrack.backstrip_well` and :func:`pybacktrack.backstrip_and_write_well`:

- ``pybacktrack.BACKSTRIP_COLUMN_AGE``
- ``pybacktrack.BACKSTRIP_COLUMN_DECOMPACTED_THICKNESS``
- ``pybacktrack.BACKSTRIP_COLUMN_DECOMPACTED_DENSITY``
- ``pybacktrack.BACKSTRIP_COLUMN_AVERAGE_TECTONIC_SUBSIDENCE``
- ``pybacktrack.BACKSTRIP_COLUMN_MIN_TECTONIC_SUBSIDENCE``
- ``pybacktrack.BACKSTRIP_COLUMN_MAX_TECTONIC_SUBSIDENCE``
- ``pybacktrack.BACKSTRIP_COLUMN_AVERAGE_WATER_DEPTH``
- ``pybacktrack.BACKSTRIP_COLUMN_MIN_WATER_DEPTH``
- ``pybacktrack.BACKSTRIP_COLUMN_MAX_WATER_DEPTH``
- ``pybacktrack.BACKSTRIP_COLUMN_COMPACTED_THICKNESS``
- ``pybacktrack.BACKSTRIP_COLUMN_LITHOLOGY``
- ``pybacktrack.BACKSTRIP_COLUMN_COMPACTED_DEPTH``

Creating lithologies
--------------------

.. autoclass:: pybacktrack.Lithology
   :members:
   :special-members: __init__

.. autofunction:: pybacktrack.read_lithologies_file

.. autofunction:: pybacktrack.create_lithology

.. autofunction:: pybacktrack.create_lithology_from_components

Constants
^^^^^^^^^

``pybacktrack.DEFAULT_BASE_LITHOLOGY_NAME``
  Default name of the lithology of the stratigraphic unit at the base of the well.

Decompacting well sites
-----------------------

.. autofunction:: pybacktrack.read_well_file

.. autofunction:: pybacktrack.write_well_file

.. autofunction:: pybacktrack.write_well_metadata

.. autoclass:: pybacktrack.Well
   :members:
   :special-members: __init__

.. autoclass:: pybacktrack.StratigraphicUnit
   :members:
   :special-members: __init__

.. autoclass:: pybacktrack.DecompactedWell
   :members:
   :special-members: __init__

.. autoclass:: pybacktrack.DecompactedStratigraphicUnit
   :members:
   :special-members: __init__

.. _pybacktrack_reference_converting_age_to_depth:

Converting oceanic age to depth
-------------------------------

.. autofunction:: pybacktrack.convert_age_to_depth

.. autofunction:: pybacktrack.convert_age_to_depth_files

Constants
^^^^^^^^^

``pybacktrack.AGE_TO_DEPTH_MODEL_GDH1``
    Stein and Stein (1992) ``Model for the global variation in oceanic depth and heat flow with lithospheric age``.

``pybacktrack.AGE_TO_DEPTH_MODEL_CROSBY_2007``
    Crosby et al. (2006) ``The relationship between depth, age and gravity in the oceans``.

``pybacktrack.AGE_TO_DEPTH_DEFAULT_MODEL``
    The age-to-depth model to use by default.

Continental rifting
-------------------

.. autofunction:: pybacktrack.estimate_rift_beta

.. autofunction:: pybacktrack.total_rift_subsidence

.. autofunction:: pybacktrack.syn_rift_subsidence

.. autofunction:: pybacktrack.post_rift_subsidence

Dynamic topography
------------------

.. autoclass:: pybacktrack.DynamicTopography
   :members:
   :special-members: __init__

Average sea level variations
----------------------------

.. autoclass:: pybacktrack.SeaLevel
   :members:
   :special-members: __init__

.. _pybacktrack_reference_utilities:

Utilities
---------

.. autofunction:: pybacktrack.read_interpolate_function

.. autofunction:: pybacktrack.interpolate_file

.. _pybacktrack_reference_bundle_data:

Bundle data
-----------

The following bundled data comes included with the ``pybacktrack`` package:

- a lithologies text file
- an age grid
- a sediment thickness grid
- a crustal thickness grid
- a topography grid
- a collection of common dynamic topography models
- a couple of sea level curves

Constants
^^^^^^^^^

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
  
  Choices include ``terra``, ``M1``, ``M2``, ``M3``, ``M4``, ``M5``, ``M6``, ``M7``, ``ngrand``, ``s20rts`` and ``smean``.

``pybacktrack.BUNDLE_SEA_LEVEL_MODELS``
  Bundled sea level models.

  This is a dict mapping sea level model name to sea level file.
  Each *key* or *value* in the dict can be passed to the ``sea_level_model`` argument of :func:`pybacktrack.backtrack_well` and :func:`pybacktrack.backtrack_and_write_well`.

``pybacktrack.BUNDLE_SEA_LEVEL_MODEL_NAMES``
  A list of bundled sea level model *names* (keys in `BUNDLE_SEA_LEVEL_MODELS`).
  
  Choices include ``Haq87_SealevelCurve`` and ``Haq87_SealevelCurve_Longterm``.

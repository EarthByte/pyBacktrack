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

.. autosummary::
   :nosignatures:
   :toctree: generated
   
   pybacktrack.backtrack_well
   pybacktrack.write_backtrack_well
   pybacktrack.backtrack_and_write_well

.. _pybacktrack_reference_backstripping:

Backstripping
-------------

Find decompacted total sediment thickness and tectonic subsidence through time.

.. autosummary::
   :nosignatures:
   :toctree: generated

   pybacktrack.backstrip_well
   pybacktrack.write_backstrip_well
   pybacktrack.backstrip_and_write_well

.. _pybacktrack_reference_paleobathymetry:

Paleobathymetry
---------------

Generate paleo bathymetry grids through time.

.. autosummary::
   :nosignatures:
   :toctree: generated

   pybacktrack.generate_lon_lat_points
   pybacktrack.reconstruct_paleo_bathymetry
   pybacktrack.write_paleo_bathymetry_grids
   pybacktrack.reconstruct_paleo_bathymetry_grids
   pybacktrack.merge_paleo_bathymetry_grid

.. _pybacktrack_reference_creating_lithologies:

Creating lithologies
--------------------

Create lithologies or read them from file(s).

.. autosummary::
   :nosignatures:
   :toctree: generated

   pybacktrack.Lithology
   pybacktrack.read_lithologies_file
   pybacktrack.read_lithologies_files
   pybacktrack.create_lithology
   pybacktrack.create_lithology_from_components

.. _pybacktrack_reference_read_write_well_sites:

Reading and writing well files
------------------------------

Read/write well site files.

.. autosummary::
   :nosignatures:
   :toctree: generated

   pybacktrack.read_well_file
   pybacktrack.write_well_file
   pybacktrack.write_well_metadata

.. _pybacktrack_reference_compacted_well:

Compacted well
--------------

Query a well and its stratigraphic layers.

.. autosummary::
   :nosignatures:
   :toctree: generated

   pybacktrack.Well
   pybacktrack.StratigraphicUnit

.. _pybacktrack_reference_decompacted_well:

Decompacted well
----------------

Query decompacted sections at past times.

.. autosummary::
   :nosignatures:
   :toctree: generated

   pybacktrack.DecompactedWell
   pybacktrack.DecompactedStratigraphicUnit

.. _pybacktrack_reference_converting_age_to_depth:

Converting oceanic age to depth
-------------------------------

Convert ocean basin ages (Ma) to basement depth (metres) using different age/depth models.

.. autosummary::
   :nosignatures:
   :toctree: generated

   pybacktrack.convert_age_to_depth
   pybacktrack.convert_age_to_depth_files

.. _pybacktrack_reference_rifting:

Continental rifting
-------------------

Continental passive margin initial rifting subsidence and subsequent thermal subsidence.
Rifting is assumed instantaneous in that thermal contraction only happens after rifting has ended.

.. autosummary::
   :nosignatures:
   :toctree: generated

   pybacktrack.estimate_rift_beta
   pybacktrack.total_rift_subsidence
   pybacktrack.syn_rift_subsidence
   pybacktrack.post_rift_subsidence

.. _pybacktrack_reference_dynamic_topography:

Dynamic topography
------------------

Sample time-dependent dynamic topography in the mantle reference frame.

.. autosummary::
   :nosignatures:
   :toctree: generated

   pybacktrack.DynamicTopography
   pybacktrack.InterpolateDynamicTopography

.. _pybacktrack_reference_sea_level:

Average sea level variations
----------------------------

Read a sea level file and compute average sea level variations during time periods.

.. autosummary::
   :nosignatures:
   :toctree: generated

   pybacktrack.SeaLevel

.. _pybacktrack_reference_converting_stratigraphic_depth_to_age:

Converting stratigraphic depth to age
-------------------------------------

Convert stratigraphic depths (metres) to age (Ma) using an depth-to-age model.

.. autosummary::
   :nosignatures:
   :toctree: generated

   pybacktrack.convert_stratigraphic_depth_to_age
   pybacktrack.convert_stratigraphic_depth_to_age_files

.. _pybacktrack_reference_utilities:

Utilities
---------

Interpolate a sequence of linear segments read from a 2-column file at the values read from a 1-column file.

.. autosummary::
   :nosignatures:
   :toctree: generated

   pybacktrack.read_interpolate_function
   pybacktrack.interpolate_file

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
    `PyBacktrack 1.0: A Tool for Reconstructing Paleobathymetry on Oceanic and Continental Crust <https://doi.org/10.1029/2017GC007313>`__,
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
  
  Choices include ``Miller2024_SealevelCurve``, ``Haq2024_Hybrid_SealevelCurve``, ``Haq2024_Hybrid_SealevelCurve_Longterm``, ``Haq87_SealevelCurve`` and ``Haq87_SealevelCurve_Longterm``.

``pybacktrack.BUNDLE_RECONSTRUCTION_ROTATION_FILENAMES``
  Rotation files of the `Zahirovic 2022 <https://zenodo.org/records/13899315>`__ default reconstruction model used to reconstruct sediment-deposited crust (at drill sites and for paleobathymetry gridding).

``pybacktrack.BUNDLE_RECONSTRUCTION_STATIC_POLYGON_FILENAME``
  Static polygon file of the `Zahirovic 2022 <https://zenodo.org/records/13899315>`__ default reconstruction model used to assign plate IDs to points on sediment-deposited crust (at drill sites and for paleobathymetry gridding).

Backtracking
^^^^^^^^^^^^

``pybacktrack.BACKTRACK_DEFAULT_DECOMPACTED_COLUMNS``
  Default list of decompacted columns used for ``decompacted_columns`` argument of
  :func:`pybacktrack.backtrack_well` and :func:`pybacktrack.backtrack_and_write_well`.

List of column types available for the ``decompacted_columns`` argument of
:func:`pybacktrack.backtrack_well` and :func:`pybacktrack.backtrack_and_write_well`:

- ``pybacktrack.BACKTRACK_COLUMN_AGE``
- ``pybacktrack.BACKTRACK_COLUMN_PALEO_LONGITUDE``
- ``pybacktrack.BACKTRACK_COLUMN_PALEO_LATITUDE``
- ``pybacktrack.BACKTRACK_COLUMN_COMPACTED_DEPTH``
- ``pybacktrack.BACKTRACK_COLUMN_COMPACTED_THICKNESS``
- ``pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_THICKNESS``
- ``pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_DENSITY``
- ``pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_SEDIMENT_RATE``
- ``pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_DEPTH``
- ``pybacktrack.BACKTRACK_COLUMN_DYNAMIC_TOPOGRAPHY``
- ``pybacktrack.BACKTRACK_COLUMN_TECTONIC_SUBSIDENCE``
- ``pybacktrack.BACKTRACK_COLUMN_WATER_DEPTH``
- ``pybacktrack.BACKTRACK_COLUMN_SEA_LEVEL``
- ``pybacktrack.BACKTRACK_COLUMN_LITHOLOGY``

Backstripping
^^^^^^^^^^^^^

``pybacktrack.BACKSTRIP_DEFAULT_DECOMPACTED_COLUMNS``
  Default list of decompacted columns used for ``decompacted_columns`` argument of
  :func:`pybacktrack.backstrip_well` and :func:`pybacktrack.backstrip_and_write_well`.

List of column types available for the ``decompacted_columns`` argument of
:func:`pybacktrack.backstrip_well` and :func:`pybacktrack.backstrip_and_write_well`:

- ``pybacktrack.BACKSTRIP_COLUMN_AGE``
- ``pybacktrack.BACKSTRIP_COLUMN_PALEO_LONGITUDE``
- ``pybacktrack.BACKSTRIP_COLUMN_PALEO_LATITUDE``
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
- ``pybacktrack.BACKSTRIP_COLUMN_SEA_LEVEL``
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
    Richards et al. (2020) `Structure and dynamics of the oceanic lithosphere-asthenosphere system <https://doi.org/10.1016/j.pepi.2020.106559>`__.

    The parameters of the preferred RHCW18 Plate Model used in pyBacktrack include a potential mantle temperature of 1333 in °C,
    a plate thickness of 130 km and a zero-age ridge depth of 2500 m, as described in Richards et al. (2020)
    (updated from Richards et al. (2018) and on the `related github repository <https://github.com/freddrichards/RHCW18_Plate_Model>`__).

``pybacktrack.AGE_TO_DEPTH_MODEL_CROSBY_2007``
    Crosby, A.G., (2007) ``Aspects of the relationship between topography and gravity on the Earth and Moon, PhD thesis``.
  
    The Python source code that implements this age-depth relationship can be found
    `here <https://github.com/EarthByte/pyBacktrack/blob/8e21ec2b49be101e88d80e8ccb18fe736d68a277/pybacktrack/age_to_depth.py#L195-L264>`__.
    And note that additional background information on this model can be found in:
    Crosby, A.G. and McKenzie, D., 2009. `An analysis of young ocean depth, gravity and global residual topography <https://doi.org/10.1111/j.1365-246X.2009.04224.x>`__.

``pybacktrack.AGE_TO_DEPTH_MODEL_GDH1``
    Stein and Stein (1992) `Model for the global variation in oceanic depth and heat flow with lithospheric age <https://doi.org/10.1038/359123a0>`__.

``pybacktrack.AGE_TO_DEPTH_DEFAULT_MODEL``
    The age-to-depth model to use by default.

# coding=utf-8

#
# Copyright (C) 2017 The University of Sydney, Australia
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License, version 2, as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

"""Access to the bundled data that comes included with the pybacktrack package.

The bundled data includes:

- a lithologies text file
- an age grid
- a sediment thickness grid
- a crustal thickness grid
- a topography grid
- a collection of common dynamic topography models
- a couple of sea level curves

The following module attributes are available:

- **pybacktrack.bundle_data.BUNDLE_PATH**

  Base directory of the bundled data.

  This is an absolute path so that scripts outside the pybacktrack package can also reference the bundled data.
  All bundle data paths are derived from this base path.

- **pybacktrack.bundle_data.BUNDLE_LITHOLOGY_FILENAMES**

  A list of bundled lithology filenames.
  
  **pybacktrack.bundle_data.DEFAULT_BUNDLE_LITHOLOGY_FILENAME**
  
  Same as **pybacktrack.bundle_data.PRIMARY_BUNDLE_LITHOLOGY_FILENAME**.
  
  **pybacktrack.bundle_data.PRIMARY_BUNDLE_LITHOLOGY_FILENAME**
  
  The primary lithology filename contains the lithologies covered in Table 1 in the pyBacktrack paper:

  * Müller, R. D., Cannon, J., Williams, S. and Dutkiewicz, A., 2018,
    `PyBacktrack 1.0: A Tool for Reconstructing Paleobathymetry on Oceanic and Continental Crust <https://doi.org/10.1029/2017GC007313>`_,
    **Geochemistry, Geophysics, Geosystems,** 19, 1898-1909, doi: 10.1029/2017GC007313.

  **pybacktrack.bundle_data.EXTENDED_BUNDLE_LITHOLOGY_FILENAME**
  
  The optional extended lithology filename extends the primary lithologies, and mostly contains lithologies in shallow water.
  
- **pybacktrack.bundle_data.BUNDLE_AGE_GRID_FILENAME**

  Bundled age grid file.

- **pybacktrack.bundle_data.BUNDLE_TOPOGRAPHY_FILENAME**

  Bundled topography/bathymetry grid file.

- **pybacktrack.bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME**

  Bundled total sediment thickness grid file.

- **pybacktrack.bundle_data.BUNDLE_CRUSTAL_THICKNESS_FILENAME**

  Bundled crustal thickness grid file.

- **pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS**

  Bundled dynamic topography models.

  This is a dict mapping dynamic topography model name to model information 3-tuple of (grid list filenames, static polygon filename and rotation filenames).
  Each *value* in the dict can be passed to the ``dynamic_topography_model`` argument of :func:`pybacktrack.backtrack_well` and :func:`pybacktrack.backtrack_and_write_well`.

- **pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_NAMES**

  A list of bundled dynamic topography model *names* (keys in `BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS`).
  
  Choices include ``terra``, ``M1``, ``M2``, ``M3``, ``M4``, ``M5``, ``M6``, ``M7``, ``ngrand``, ``s20rts``, ``smean``, ``AY18`` and ``KM16``.

- **pybacktrack.bundle_data.BUNDLE_SEA_LEVEL_MODELS**

  Bundled sea level models.

  This is a dict mapping sea level model name to sea level file.
  Each *value* in the dict can be passed to the ``sea_level_model`` argument of :func:`pybacktrack.backtrack_well` and :func:`pybacktrack.backtrack_and_write_well`.

- **pybacktrack.bundle_data.BUNDLE_SEA_LEVEL_MODEL_NAMES**

  A list of bundled sea level model *names* (keys in `BUNDLE_SEA_LEVEL_MODELS`).
  
  Choices include ``Haq87_SealevelCurve`` and ``Haq87_SealevelCurve_Longterm``.

- **pybacktrack.BUNDLE_RECONSTRUCTION_ROTATION_FILENAMES**

  Rotation files of the reconstruction model used to reconstruct sediment-deposited crust for paleobathymetry gridding.

- **pybacktrack.BUNDLE_RECONSTRUCTION_STATIC_POLYGON_FILENAME**

  Static polygon file of the reconstruction model used to assign plate IDs to points on sediment-deposited crust for paleobathymetry gridding.
"""


import os.path


BUNDLE_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'bundle_data')

# Primary lithologies file contains the lithologies in the pyBacktrack paper.
PRIMARY_BUNDLE_LITHOLOGY_FILENAME = os.path.join(BUNDLE_PATH, 'lithologies', 'primary.txt')
EXTENDED_BUNDLE_LITHOLOGY_FILENAME = os.path.join(BUNDLE_PATH, 'lithologies', 'extended.txt')
BUNDLE_LITHOLOGY_FILENAMES = [
    PRIMARY_BUNDLE_LITHOLOGY_FILENAME,
    EXTENDED_BUNDLE_LITHOLOGY_FILENAME
]
# Default lithologies file is the primary lithologies file.
DEFAULT_BUNDLE_LITHOLOGY_FILENAME = PRIMARY_BUNDLE_LITHOLOGY_FILENAME

BUNDLE_AGE_GRID_FILENAME = os.path.join(BUNDLE_PATH, 'age', 'agegrid_6m.nc')

BUNDLE_RIFTING_START_FILENAME = os.path.join(BUNDLE_PATH, 'reconstruction', '2019_v2', 'rift_start_grid.nc')
BUNDLE_RIFTING_END_FILENAME = os.path.join(BUNDLE_PATH, 'reconstruction', '2019_v2', 'rift_end_grid.nc')
BUNDLE_RECONSTRUCTION_ROTATION_FILENAMES = [os.path.join(BUNDLE_PATH, 'reconstruction', '2019_v2', 'rotations_250-0Ma.rot')]
BUNDLE_RECONSTRUCTION_STATIC_POLYGON_FILENAME = os.path.join(BUNDLE_PATH, 'reconstruction', '2019_v2', 'static_polygons.shp')

BUNDLE_AGE_TO_DEPTH_MODEL_RHCW18_FILENAME = os.path.join(BUNDLE_PATH, 'ocean_age_to_depth', 'RHCW18', 'depth-1333-130-2500.dat')

BUNDLE_TOPOGRAPHY_FILENAME = os.path.join(BUNDLE_PATH, 'topography', 'ETOPO1_0.1.grd')

BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME = os.path.join(BUNDLE_PATH, 'sediment_thickness', 'GlobSed.nc')

BUNDLE_CRUSTAL_THICKNESS_FILENAME = os.path.join(BUNDLE_PATH, 'crustal_thickness', 'crsthk.grd')

BUNDLE_DYNAMIC_TOPOGRAPHY_PATH = os.path.join(BUNDLE_PATH, 'dynamic_topography')
BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH = os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_PATH, 'models')
BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH = os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_PATH, 'reconstructions')
BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS = {
    'terra': (
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH, 'terra.grids'),
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'terra', 'static_polygons.gpmlz'),
        [
            os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'terra', 'rotations.rot')
        ]
    ),
    'M1': (
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH, 'M1.grids'),
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'M1', 'static_polygons.gpmlz'),
        [
            os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'M1', 'rotations.rot')
        ]
    ),
    'M2': (
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH, 'M2.grids'),
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, '2013.2-r213', 'static_polygons.shp'),
        [
            os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, '2013.2-r213', 'rotations.rot')
        ]
    ),
    'M3': (
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH, 'M3.grids'),
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, '2015_v2', 'static_polygons.gpmlz'),
        [
            os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, '2015_v2', 'rotations_250-0Ma.rot'),
            os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, '2015_v2', 'rotations_410-250Ma.rot')
        ]
    ),
    'M4': (
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH, 'M4.grids'),
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, '2014_1_401', 'static_polygons.shp'),
        [
            os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, '2014_1_401', 'rotations.rot')
        ]
    ),
    'M5': (
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH, 'M5.grids'),
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, '2013.2-r213', 'static_polygons.shp'),
        [
            os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, '2013.2-r213', 'rotations.rot')
        ]
    ),
    'M6': (
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH, 'M6.grids'),
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, '2015_v2', 'static_polygons.gpmlz'),
        [
            os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, '2015_v2', 'rotations_250-0Ma.rot'),
            os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, '2015_v2', 'rotations_410-250Ma.rot')
        ]
    ),
    'M7': (
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH, 'M7.grids'),
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, '2015_v2', 'static_polygons.gpmlz'),
        [
            os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, '2015_v2', 'rotations_250-0Ma.rot'),
            os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, '2015_v2', 'rotations_410-250Ma.rot')
        ]
    ),
    'ngrand': (
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH, 'ngrand.grids'),
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, '20101129', 'static_polygons.gpmlz'),
        [
            os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, '20101129', 'rotations.rot')
        ]
    ),
    's20rts': (
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH, 's20rts.grids'),
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, '20101129', 'static_polygons.gpmlz'),
        [
            os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, '20101129', 'rotations.rot')
        ]
    ),
    'smean': (
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH, 'smean.grids'),
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, '20101129', 'static_polygons.gpmlz'),
        [
            os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, '20101129', 'rotations.rot')
        ]
    ),
    'AY18': (
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH, 'AY18.grids'),
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'AY18', 'static_polygons.shp'),
        [
            os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'AY18', 'rotations_250-0Ma.rot'),
            os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'AY18', 'rotations_410-250Ma.rot')
        ]
    ),
    'KM16': (
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH, 'KM16.grids'),
        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'KM16', 'static_polygons.shp'),
        [
            os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'KM16', 'rotations_250-0Ma.rot'),
            os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'KM16', 'rotations_410-250Ma.rot')
        ]
    ),
}

BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_NAMES = BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS.keys()

BUNDLE_SEA_LEVEL_PATH = os.path.join(BUNDLE_PATH, 'sea_level')
BUNDLE_SEA_LEVEL_MODELS = {
    'Haq87_SealevelCurve': os.path.join(BUNDLE_SEA_LEVEL_PATH, 'Haq87_SealevelCurve.dat'),
    'Haq87_SealevelCurve_Longterm': os.path.join(BUNDLE_SEA_LEVEL_PATH, 'Haq87_SealevelCurve_Longterm.dat')
}

BUNDLE_SEA_LEVEL_MODEL_NAMES = BUNDLE_SEA_LEVEL_MODELS.keys()

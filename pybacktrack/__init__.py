from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

#
# Public API
#

from .backtrack import \
    backtrack_well, \
    write_well as write_backtrack_well, \
    backtrack_and_write_well, \
    DEFAULT_DECOMPACTED_COLUMNS as BACKTRACK_DEFAULT_DECOMPACTED_COLUMNS, \
    COLUMN_AGE as BACKTRACK_COLUMN_AGE, \
    COLUMN_DECOMPACTED_THICKNESS as BACKTRACK_COLUMN_DECOMPACTED_THICKNESS, \
    COLUMN_DECOMPACTED_DENSITY as BACKTRACK_COLUMN_DECOMPACTED_DENSITY, \
    COLUMN_TECTONIC_SUBSIDENCE as BACKTRACK_COLUMN_TECTONIC_SUBSIDENCE, \
    COLUMN_WATER_DEPTH as BACKTRACK_COLUMN_WATER_DEPTH, \
    COLUMN_COMPACTED_THICKNESS as BACKTRACK_COLUMN_COMPACTED_THICKNESS, \
    COLUMN_LITHOLOGY as BACKTRACK_COLUMN_LITHOLOGY, \
    COLUMN_COMPACTED_DEPTH as BACKTRACK_COLUMN_COMPACTED_DEPTH, \
    COLUMN_DECOMPACTED_SEDIMENT_RATE as BACKTRACK_COLUMN_DECOMPACTED_SEDIMENT_RATE, \
    COLUMN_DECOMPACTED_DEPTH as BACKTRACK_COLUMN_DECOMPACTED_DEPTH, \
    COLUMN_DYNAMIC_TOPOGRAPHY as BACKTRACK_COLUMN_DYNAMIC_TOPOGRAPHY

from .backstrip import \
    backstrip_well, \
    write_well as write_backstrip_well, \
    backstrip_and_write_well, \
    DEFAULT_DECOMPACTED_COLUMNS as BACKSTRIP_DEFAULT_DECOMPACTED_COLUMNS, \
    COLUMN_AGE as BACKSTRIP_COLUMN_AGE, \
    COLUMN_DECOMPACTED_THICKNESS as BACKSTRIP_COLUMN_DECOMPACTED_THICKNESS, \
    COLUMN_DECOMPACTED_DENSITY as BACKSTRIP_COLUMN_DECOMPACTED_DENSITY, \
    COLUMN_AVERAGE_TECTONIC_SUBSIDENCE as BACKSTRIP_COLUMN_AVERAGE_TECTONIC_SUBSIDENCE, \
    COLUMN_MIN_TECTONIC_SUBSIDENCE as BACKSTRIP_COLUMN_MIN_TECTONIC_SUBSIDENCE, \
    COLUMN_MAX_TECTONIC_SUBSIDENCE as BACKSTRIP_COLUMN_MAX_TECTONIC_SUBSIDENCE, \
    COLUMN_AVERAGE_WATER_DEPTH as BACKSTRIP_COLUMN_AVERAGE_WATER_DEPTH, \
    COLUMN_MIN_WATER_DEPTH as BACKSTRIP_COLUMN_MIN_WATER_DEPTH, \
    COLUMN_MAX_WATER_DEPTH as BACKSTRIP_COLUMN_MAX_WATER_DEPTH, \
    COLUMN_COMPACTED_THICKNESS as BACKSTRIP_COLUMN_COMPACTED_THICKNESS, \
    COLUMN_LITHOLOGY as BACKSTRIP_COLUMN_LITHOLOGY, \
    COLUMN_COMPACTED_DEPTH as BACKSTRIP_COLUMN_COMPACTED_DEPTH, \
    COLUMN_DECOMPACTED_SEDIMENT_RATE as BACKSTRIP_COLUMN_DECOMPACTED_SEDIMENT_RATE, \
    COLUMN_DECOMPACTED_DEPTH as BACKSTRIP_COLUMN_DECOMPACTED_DEPTH

from .paleo_bathymetry import \
    reconstruct_backtrack_bathymetry as reconstruct_paleo_bathymetry, \
    generate_lon_lat_points, \
    write_bathymetry_grids as write_paleo_bathymetry_grids, \
    reconstruct_backtrack_bathymetry_and_write_grids as reconstruct_paleo_bathymetry_grids, \
    DEFAULT_LITHOLOGY_NAME as DEFAULT_PALEO_BATHYMETRY_LITHOLOGY_NAME

from .lithology import \
    Lithology, \
    read_lithologies_file, \
    read_lithologies_files, \
    create_lithology, \
    create_lithology_from_components, \
    DEFAULT_BASE_LITHOLOGY_NAME

from .well import \
    StratigraphicUnit, \
    Well, \
    DecompactedStratigraphicUnit, \
    DecompactedWell, \
    read_well_file, \
    write_well_file, \
    write_well_metadata

from .age_to_depth import \
    convert_age_to_depth, \
    convert_age_to_depth_files, \
    MODEL_GDH1 as AGE_TO_DEPTH_MODEL_GDH1, \
    MODEL_CROSBY_2007 as AGE_TO_DEPTH_MODEL_CROSBY_2007, \
    MODEL_RHCW18 as AGE_TO_DEPTH_MODEL_RHCW18, \
    DEFAULT_MODEL as AGE_TO_DEPTH_DEFAULT_MODEL

from .stratigraphic_depth_to_age import \
    convert_stratigraphic_depth_to_age, \
    convert_stratigraphic_depth_to_age_files

from .rifting import \
    estimate_beta as estimate_rift_beta, \
    total_subsidence as total_rift_subsidence, \
    syn_rift_subsidence, \
    post_rift_subsidence

from .dynamic_topography import \
    DynamicTopography, \
    InterpolateDynamicTopography

from .sea_level import \
    SeaLevel

from .util.interpolate import \
    read_curve_function as read_interpolate_function, \
    interpolate_file

# From bundle_data module.
#
# Importing all since there are only module variables prefixed with 'BUNDLE_' in 'bundle_data' module.
from .bundle_data import *

# Installing examples from pybacktrack package.
from .install_examples import install as install_examples
# Installing supplementary script from pybacktrack package.
from .install_supplementary import install as install_supplementary

from .version import __version__, VERSION


# List public interface in case client does "from pybacktrack import *".
__all__ = [
    # From backtrack module...
    'backtrack_well',
    'write_backtrack_well',
    'backtrack_and_write_well',
    'BACKTRACK_DEFAULT_DECOMPACTED_COLUMNS',
    'BACKTRACK_COLUMN_AGE',
    'BACKTRACK_COLUMN_DECOMPACTED_THICKNESS',
    'BACKTRACK_COLUMN_DECOMPACTED_DENSITY',
    'BACKTRACK_COLUMN_TECTONIC_SUBSIDENCE',
    'BACKTRACK_COLUMN_WATER_DEPTH',
    'BACKTRACK_COLUMN_COMPACTED_THICKNESS',
    'BACKTRACK_COLUMN_LITHOLOGY',
    'BACKTRACK_COLUMN_COMPACTED_DEPTH',
    'BACKTRACK_COLUMN_DECOMPACTED_SEDIMENT_RATE',
    'BACKTRACK_COLUMN_DECOMPACTED_DEPTH',
    'BACKTRACK_COLUMN_DYNAMIC_TOPOGRAPHY',
    # From backstrip module...
    'backstrip_well',
    'write_backstrip_well',
    'backstrip_and_write_well',
    'BACKSTRIP_DEFAULT_DECOMPACTED_COLUMNS',
    'BACKSTRIP_COLUMN_AGE',
    'BACKSTRIP_COLUMN_DECOMPACTED_THICKNESS',
    'BACKSTRIP_COLUMN_DECOMPACTED_DENSITY',
    'BACKSTRIP_COLUMN_AVERAGE_TECTONIC_SUBSIDENCE',
    'BACKSTRIP_COLUMN_MIN_TECTONIC_SUBSIDENCE',
    'BACKSTRIP_COLUMN_MAX_TECTONIC_SUBSIDENCE',
    'BACKSTRIP_COLUMN_AVERAGE_WATER_DEPTH',
    'BACKSTRIP_COLUMN_MIN_WATER_DEPTH',
    'BACKSTRIP_COLUMN_MAX_WATER_DEPTH',
    'BACKSTRIP_COLUMN_COMPACTED_THICKNESS',
    'BACKSTRIP_COLUMN_LITHOLOGY',
    'BACKSTRIP_COLUMN_COMPACTED_DEPTH',
    'BACKSTRIP_COLUMN_DECOMPACTED_SEDIMENT_RATE',
    'BACKSTRIP_COLUMN_DECOMPACTED_DEPTH',
    # From paleo_bathymetry module...
    'reconstruct_paleo_bathymetry',
    'generate_lon_lat_points',
    'write_paleo_bathymetry_grids',
    'reconstruct_paleo_bathymetry_grids',
    'DEFAULT_PALEO_BATHYMETRY_LITHOLOGY_NAME',
    # From lithology module...
    'Lithology',
    'read_lithologies_file',
    'read_lithologies_files',
    'create_lithology',
    'create_lithology_from_components',
    'DEFAULT_BASE_LITHOLOGY_NAME',
    # From well module...
    'StratigraphicUnit',
    'Well',
    'DecompactedStratigraphicUnit',
    'DecompactedWell',
    'read_well_file',
    'write_well_file',
    'write_well_metadata',
    # From age_to_depth module...
    'convert_age_to_depth',
    'convert_age_to_depth_files',
    'AGE_TO_DEPTH_MODEL_GDH1',
    'AGE_TO_DEPTH_MODEL_CROSBY_2007',
    'AGE_TO_DEPTH_MODEL_RHCW18',
    'AGE_TO_DEPTH_DEFAULT_MODEL',
    # From stratigraphic_depth_to_age module...
    'convert_stratigraphic_depth_to_age',
    'convert_stratigraphic_depth_to_age_files',
    # From rifting module...
    'estimate_rift_beta',
    'total_rift_subsidence',
    'syn_rift_subsidence',
    'post_rift_subsidence',
    # From dynamic_topography module...
    'DynamicTopography',
    'InterpolateDynamicTopography',
    # From sea_level module...
    'SeaLevel',
    # From interpolate module...
    'read_interpolate_function',
    'interpolate_file',
    # From bundle_data module...
    'BUNDLE_SEA_LEVEL_MODELS',
    'BUNDLE_PATH',
    'BUNDLE_LITHOLOGY_FILENAMES',
    'DEFAULT_BUNDLE_LITHOLOGY_FILENAME',
    'PRIMARY_BUNDLE_LITHOLOGY_FILENAME',
    'EXTENDED_BUNDLE_LITHOLOGY_FILENAME',
    'BUNDLE_AGE_GRID_FILENAME',
    'BUNDLE_TOPOGRAPHY_FILENAME',
    'BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME',
    'BUNDLE_CRUSTAL_THICKNESS_FILENAME',
    'BUNDLE_DYNAMIC_TOPOGRAPHY_PATH',
    'BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH',
    'BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH',
    'BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS',
    'BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_NAMES',
    'BUNDLE_SEA_LEVEL_PATH',
    'BUNDLE_SEA_LEVEL_MODELS',
    'BUNDLE_SEA_LEVEL_MODEL_NAMES',
    'BUNDLE_RECONSTRUCTION_ROTATION_FILENAMES',
    'BUNDLE_RECONSTRUCTION_STATIC_POLYGON_FILENAME',
    '__version__',
    'VERSION'
]

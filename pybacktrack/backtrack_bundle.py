
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

"""An easier-to-use version of the `backtrack` module that references included bundled data.

The bundled data includes:

- a lithologies text file
- an age grid
- a sediment thickness grid
- a crustal thickness grid
- a topography grid
- a collection of common dynamic topography models
- a couple of sea level curves

:func:`backtrack` same as :func:`pybacktrack.backtrack.backtrack` but uses bundled data.

:func:`backtrack_and_write_decompacted` same as :func:`pybacktrack.backtrack.backtrack_and_write_decompacted` but uses bundled data.
"""

from __future__ import print_function
import argparse
import pybacktrack.age_to_depth
import pybacktrack.backtrack
import os.path
import sys
import traceback


# Base directory of the bundled data.
# This is an absolute path so that scripts outside the pybacktrack package can also reference the bundled data.
MODULE_DIR = os.path.abspath(os.path.dirname(__file__))
BUNDLE_PATH = os.path.join(MODULE_DIR, 'bundle_data')

BUNDLE_LITHOLOGIES_FILENAME = os.path.join(BUNDLE_PATH, 'lithologies', 'lithologies.txt')
BUNDLE_AGE_GRID_FILENAME = os.path.join(BUNDLE_PATH, 'age', 'agegrid_6m.grd')
BUNDLE_TOPOGRAPHY_FILENAME = os.path.join(BUNDLE_PATH, 'topography', 'ETOPO1_0.1.grd')
BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME = os.path.join(BUNDLE_PATH, 'sediment_thickness', 'sedthick_world_v3_5min_epsg4326_cf.nc')
BUNDLE_CRUSTAL_THICKNESS_FILENAME = os.path.join(BUNDLE_PATH, 'crustal_thickness', 'crsthk.grd')

BUNDLE_DYNAMIC_TOPOGRAPHY_PATH = os.path.join(BUNDLE_PATH, 'dynamic_topography')
BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH = os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_PATH, 'models')
BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH = os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_PATH, 'reconstructions')
# Dict mapping dynamic topography model name to model information 3-tuple of (grid list filenames, static polygon filename and rotation filenames).
BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_INFOS = {
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
    )
}
# Dynamic topography model names.
BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_NAMES = BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_INFOS.keys()

BUNDLE_SEA_LEVEL_PATH = os.path.join(BUNDLE_PATH, 'sea_level')
# Dict mapping sea level model name to model filename.
BUNDLE_SEA_LEVEL_MODEL_FILES = {
    'Haq87_SealevelCurve': os.path.join(BUNDLE_SEA_LEVEL_PATH, 'Haq87_SealevelCurve.dat'),
    'Haq87_SealevelCurve_Longterm': os.path.join(BUNDLE_SEA_LEVEL_PATH, 'Haq87_SealevelCurve_Longterm.dat')
}
# Sea level model names.
BUNDLE_SEA_LEVEL_MODEL_NAMES = BUNDLE_SEA_LEVEL_MODEL_FILES.keys()


def backtrack(
        well_filename,
        lithologies_filename=BUNDLE_LITHOLOGIES_FILENAME,
        age_grid_filename=BUNDLE_AGE_GRID_FILENAME,
        topography_filename=BUNDLE_TOPOGRAPHY_FILENAME,
        total_sediment_thickness_filename=BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,
        crustal_thickness_filename=BUNDLE_CRUSTAL_THICKNESS_FILENAME,
        dynamic_topography_model_name=None,
        sea_level_model_name=None,
        base_lithology_name=pybacktrack.backtrack.DEFAULT_BASE_LITHOLOGY_NAME,
        ocean_age_to_depth_model=pybacktrack.age_to_depth.DEFAULT_MODEL,
        rifting_period=None,
        well_location=None,
        well_bottom_age_column=0,
        well_bottom_depth_column=1,
        well_lithology_column=2):
    """Finds decompacted total sediment thickness and water depth for each age in a well.
    
    This function is very similar to :func:`pybacktrack.backtrack.backtrack` except it has
    default values that reference the bundled data included in the `pybacktrack` package.
    It also uses a model name (instead of filenames) for dynamic topography and sea-level curve to
    make specifying them even easier (especially dynamic topography).
    
    Parameters
    ----------
    well_filename : string
        Name of well text file.
    lithologies_filename : string, optional
        Name of lithologies text file.
    age_grid_filename : string, optional
        Age grid filename.
        Used to obtain age of seafloor at well location.
    topography_filename : string, optional
        Topography filename.
        Used to obtain water depth at well location.
    total_sediment_thickness_filename : string, optional
        Total sediment thickness filename.
        Used to obtain total sediment thickness at well location.
    crustal_thickness_filename : string, optional
        Crustal thickness filename.
        Used to obtain crustal thickness at well location.
    dynamic_topography_model_name : string, optional
        Represents a time-dependent dynamic topography raster grid.
        Currently only used for oceanic floor (ie, well location inside age grid)
        it is not used if well is on continental crust (passive margin).
        This is the name of a bundled dynamic topography model.
        Choices include 'terra', 'M1', 'M2', 'M3', 'M4', 'M5', 'M6' and 'M7'.
    sea_level_model_name : string, optional
        Name of the bundled sea level model.
        Choices include 'Haq87_SealevelCurve' and 'Haq87_SealevelCurve_Longterm'.
        Used to obtain sea levels relative to present day.
    base_lithology_name : string, optional
        Lithology name of the stratigraphic unit at the base of the well (must be present in lithologies file).
        The stratigraphic units in the well might not record the full depth of sedimentation.
        The base unit covers the remaining depth from bottom of well to the total sediment thickness.
        Defaults to 'Shale'.
    ocean_age_to_depth_model : {'age_to_depth.MODEL_GDH1', 'age_to_depth.MODEL_CROSBY_2007'}, optional
        The model to use when converting ocean age to depth at well location
        (if on ocean floor - not used for continental passive margin).
    rifting_period : tuple, optional
        Optional time period of rifting (if on continental passive margin - not used for oceanic floor).
        If specified then should be a 2-tuple (rift_start_age, rift_end_age) where rift_start_age can be None
        (in which case rifting is considered instantaneous from a stretching point-of-view, not thermal).
        If specified then overrides value in well file.
        If well is on continental passive margin then at least rift end age should be specified
        either here or in well file.
    well_location : tuple, optional
        Optional location of well.
        If not provided then is extracted from the `well_filename` file.
        If specified then overrides value in well file.
        If specified then must be a 2-tuple (longitude, latitude) in degrees.
    well_bottom_age_column : int, optional
        The column of well file containing bottom age. Defaults to 0.
    well_bottom_depth_column : int, optional
        The column of well file containing bottom depth. Defaults to 1.
    well_lithology_column : int, optional
        The column of well file containing lithology(s). Defaults to 2.
    
    Returns
    -------
    :class:`Well`
        The well read from `well_filename`.
        It may also be ammended with a base stratigraphic unit from the bottom of the well to basement.
    list of :class:`Well.DecompactedWell`
        The decompacted wells associated with the well.
    
    Raises
    ------
    ValueError
        If `lithology_column` is not the largest column number (must be last column).
    ValueError
        If `well_location` is not specified *and* the well location was not extracted from the well file.
    
    Notes
    -----
    Each attribute to read from well file (eg, bottom_age, bottom_depth, etc) has a column index to direct
    which column it should be read from.
    
    The tectonic subsidence at each age (of decompacted wells) is added as a `tectonic_subsidence` attribute
    to each decompacted well returned.
    """
    
    # Convert dynamic topography model name to list filename (if specified).
    if dynamic_topography_model_name is None:
        dynamic_topography_model_info = None
    else:
        try:
            dynamic_topography_model_info = BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_INFOS[dynamic_topography_model_name]
        except KeyError:
            raise ValueError("%s is not a valid dynamic topography model name" % dynamic_topography_model_name)
    
    # Convert sea level model name to filename (if specified).
    if sea_level_model_name is None:
        sea_level_filename = None
    else:
        try:
            sea_level_filename = BUNDLE_SEA_LEVEL_MODEL_FILES[sea_level_model_name]
        except KeyError:
            raise ValueError("%s is not a valid sea level model name" % sea_level_model_name)
    
    # Delegate to the 'backtrack' module.
    return pybacktrack.backtrack.backtrack(
        well_filename,
        lithologies_filename,
        age_grid_filename,
        topography_filename,
        total_sediment_thickness_filename,
        crustal_thickness_filename,
        dynamic_topography_model_info,
        sea_level_filename,
        base_lithology_name,
        ocean_age_to_depth_model,
        rifting_period,
        well_location,
        well_bottom_age_column,
        well_bottom_depth_column,
        well_lithology_column)


def backtrack_and_write_decompacted(
        decompacted_output_filename,
        well_filename,
        lithologies_filename=BUNDLE_LITHOLOGIES_FILENAME,
        age_grid_filename=BUNDLE_AGE_GRID_FILENAME,
        topography_filename=BUNDLE_TOPOGRAPHY_FILENAME,
        total_sediment_thickness_filename=BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,
        crustal_thickness_filename=BUNDLE_CRUSTAL_THICKNESS_FILENAME,
        dynamic_topography_model_name=None,
        sea_level_model_name=None,
        base_lithology_name=pybacktrack.backtrack.DEFAULT_BASE_LITHOLOGY_NAME,
        ocean_age_to_depth_model=pybacktrack.age_to_depth.DEFAULT_MODEL,
        rifting_period=None,
        decompacted_columns=pybacktrack.backtrack.default_decompacted_columns,
        well_location=None,
        well_bottom_age_column=0,
        well_bottom_depth_column=1,
        well_lithology_column=2,
        ammended_well_output_filename=None):
    """
    Backtrack well in 'well_filename' and write decompacted data to 'decompacted_output_filename'.
    
    Also optionally write ammended well data (ie, including extra stratigraphic base unit) to
    'ammended_well_output_filename' if specified.
    
    See 'backtrack()' and 'write_decompacted_wells()' for more details.
    """
    
    # Convert dynamic topography model name to list filename (if specified).
    if dynamic_topography_model_name is None:
        dynamic_topography_model_info = None
    else:
        try:
            dynamic_topography_model_info = BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_INFOS[dynamic_topography_model_name]
        except KeyError:
            raise ValueError("%s is not a valid dynamic topography model name" % dynamic_topography_model_name)
    
    # Convert sea level model name to filename (if specified).
    if sea_level_model_name is None:
        sea_level_filename = None
    else:
        try:
            sea_level_filename = BUNDLE_SEA_LEVEL_MODEL_FILES[sea_level_model_name]
        except KeyError:
            raise ValueError("%s is not a valid sea level model name" % sea_level_model_name)
    
    # Delegate to the 'backtrack' module.
    pybacktrack.backtrack.backtrack_and_write_decompacted(
        decompacted_output_filename,
        well_filename,
        lithologies_filename,
        age_grid_filename,
        topography_filename,
        total_sediment_thickness_filename,
        crustal_thickness_filename,
        dynamic_topography_model_info,
        sea_level_filename,
        base_lithology_name,
        ocean_age_to_depth_model,
        rifting_period,
        decompacted_columns,
        well_location,
        well_bottom_age_column,
        well_bottom_depth_column,
        well_lithology_column,
        ammended_well_output_filename)


if __name__ == '__main__':
    
    try:
        # Gather command-line options.
        # But don't add options for data that we've bundled.
        parser = pybacktrack.backtrack.get_command_line_parser(False)
        
        # Allow user to override default lithologies filename (if they don't want the one in the bundled data).
        parser.add_argument(
            '-l', '--lithologies_filename', type=pybacktrack.backtrack.argparse_unicode,
            default=BUNDLE_LITHOLOGIES_FILENAME,
            metavar='lithologies_filename',
            help='Optional lithologies filename used to lookup density, surface porosity and porosity decay. '
                 'Defaults to "{0}".'.format(BUNDLE_LITHOLOGIES_FILENAME))
        
        # Optional dynamic topography model name.
        parser.add_argument(
            '-y', '--dynamic_topography_model', type=str,
            metavar='dynamic_topography_model',
            help='Optional dynamic topography through time at well location. '
                 'Can be used both for oceanic floor and continental passive margin '
                 '(ie, well location inside or outside age grid). '
                 'Choices include {0}.'.format(', '.join(BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_NAMES)))
        
        parser.add_argument(
            '-sl', '--sea_level_model', type=str,
            metavar='sea_level_model',
            help='Optional sea level model used to obtain sea level (relative to present-day) over time. '
                 'Choices include {0}.'.format(', '.join(BUNDLE_SEA_LEVEL_MODEL_NAMES)))
        
        # Parse command-line options.
        args = parser.parse_args()
        
        # Do any necessary post-processing/validation of parsed options.
        decompacted_columns, ocean_age_to_depth_model = pybacktrack.backtrack.post_process_command_line(args)
        
        # Backtrack and write output data.
        backtrack_and_write_decompacted(
            args.output_filename,
            args.well_filename,
            args.lithologies_filename,
            dynamic_topography_model_name=args.dynamic_topography_model,
            sea_level_model_name=args.sea_level_model,
            base_lithology_name=args.base_lithology_name,
            ocean_age_to_depth_model=ocean_age_to_depth_model,
            rifting_period=(args.rift_start_time, args.rift_end_time),
            decompacted_columns=decompacted_columns,
            well_location=args.well_location,
            well_bottom_age_column=args.well_columns[0],
            well_bottom_depth_column=args.well_columns[1],
            well_lithology_column=args.well_columns[2],
            ammended_well_output_filename=args.output_well_filename)
        
        sys.exit(0)
        
    except Exception as exc:
        print('ERROR: {0}'.format(exc), file=sys.stderr)
        # Uncomment this to print traceback to location of raised exception.
        # traceback.print_exc()
        
        sys.exit(1)

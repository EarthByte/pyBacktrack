
"""
    Copyright (C) 2017 The University of Sydney, Australia
    
    This program is free software; you can redistribute it and/or modify it under
    the terms of the GNU General Public License, version 2, as published by
    the Free Software Foundation.
    
    This program is distributed in the hope that it will be useful, but WITHOUT
    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
    FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
    for more details.
    
    You should have received a copy of the GNU General Public License along
    with this program; if not, write to Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""


##############################################################################################################
# An easier-to-use version of the 'backtrack.py' script that includes bundled data                           #
# (age grid, sediment thickness grid, crustal thickness grid, topography grid and dynamic topography grids). #
##############################################################################################################


from __future__ import print_function
import argparse
import backtrack
import glob
import os.path
import sys
import traceback


BUNDLE_PATH = 'bundle_data'

BUNDLE_DEFAULT_LITHOLOGIES_FILENAME = os.path.join(BUNDLE_PATH, 'lithologies', 'lithologies.txt')
BUNDLE_AGE_GRID_FILENAME = os.path.join(BUNDLE_PATH, 'age', 'agegrid_6m.grd')
BUNDLE_TOPOGRAPHY_FILENAME = os.path.join(BUNDLE_PATH, 'topography', 'ETOPO1_0.1.grd')
BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME = os.path.join(BUNDLE_PATH, 'sediment_thickness', 'sedthick_world_v3_5min_epsg4326_cf.nc')
BUNDLE_CRUSTAL_THICKNESS_FILENAME = os.path.join(BUNDLE_PATH, 'crustal_thickness', 'crsthk.grd')

BUNDLE_DYNAMIC_TOPOGRAPHY_PATH = os.path.join(BUNDLE_PATH, 'dynamic_topography')
BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH = os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_PATH, 'models')
BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH = os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_PATH, 'reconstructions')
# Dict mapping dynamic topography model name to model information 3-tuple of (grid list filenames, static polygon filename and rotation filenames).
BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_INFOS = {
    'terra' :   (
                    os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH, 'terra.grids'),
                    os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'terra', 'Shephard_etal_ESR2013_Global_staticpolygons.gpmlz'),
                    [
                        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'terra', 'Shephard_etal_ESR2013_Global_EarthByte_2013.rot')
                    ]
                ),
    'M1' :      (
                    os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH, 'M1.grids'),
                    os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'M1_reconstruction', 'Global_EarthByte_GPlates_PresentDay_StaticPlatePolygons_20111012.gpmlz'),
                    [
                        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'M1_reconstruction', 'Caltech_Global_20101129.rot')
                    ]
                ),
    'M2' :      (
                    os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH, 'M2.grids'),
                    os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'Global_Model_WD_Internal_Release_2013.2-r213', 'Static_Polygons_Merged_01_07_2013.shp'),
                    [
                        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'Global_Model_WD_Internal_Release_2013.2-r213', 'Global_EarthByte_TPW_CK95G94_2013.2.rot')
                    ]
                ),
    'M3' :      (
                    os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH, 'M3.grids'),
                    os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'Global_Model_WD_Internal_Release_2015_v2', 'Global_EarthByte_GPlates_PresentDay_StaticPlatePolygons_2015_v2.gpmlz'),
                    [
                        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'Global_Model_WD_Internal_Release_2015_v2', 'Global_EB_250-0Ma_GK07_2015_v2.rot'),
                        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'Global_Model_WD_Internal_Release_2015_v2', 'Global_EB_410-250Ma_GK07_2015_v2.rot')
                    ]
                ),
    'M4' :      (
                    os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH, 'M4.grids'),
                    os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, '2014_1_401', 'Global_EarthByte_GPlates_PresentDay_StaticPlatePolygons_2014.1.shp'),
                    [
                        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, '2014_1_401', 'Global_EarthByte_TPW_GeeK07_2014.1_VanDerMeer_CrossoverFix.rot')
                    ]
                ),
    'M5' :      (
                    os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH, 'M5.grids'),
                    os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'Global_Model_WD_Internal_Release_2013.2-r213', 'Static_Polygons_Merged_01_07_2013.shp'),
                    [
                        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'Global_Model_WD_Internal_Release_2013.2-r213', 'Global_EarthByte_TPW_CK95G94_2013.2.rot')
                    ]
                ),
    'M6' :      (
                    os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH, 'M6.grids'),
                    os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'Global_Model_WD_Internal_Release_2015_v2', 'Global_EarthByte_GPlates_PresentDay_StaticPlatePolygons_2015_v2.gpmlz'),
                    [
                        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'Global_Model_WD_Internal_Release_2015_v2', 'Global_EB_250-0Ma_GK07_2015_v2.rot'),
                        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'Global_Model_WD_Internal_Release_2015_v2', 'Global_EB_410-250Ma_GK07_2015_v2.rot')
                    ]
                ),
    'M7' :      (
                    os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_PATH, 'M7.grids'),
                    os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'Global_Model_WD_Internal_Release_2015_v2', 'Global_EarthByte_GPlates_PresentDay_StaticPlatePolygons_2015_v2.gpmlz'),
                    [
                        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'Global_Model_WD_Internal_Release_2015_v2', 'Global_EB_250-0Ma_GK07_2015_v2.rot'),
                        os.path.join(BUNDLE_DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'Global_Model_WD_Internal_Release_2015_v2', 'Global_EB_410-250Ma_GK07_2015_v2.rot')
                    ]
                )
}
# Dynamic topography model names.
BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_NAMES = BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_INFOS.keys()

BUNDLE_SEA_LEVEL_PATH = os.path.join(BUNDLE_PATH, 'sea_level')
# Dict mapping sea level model name to model filename.
BUNDLE_SEA_LEVEL_MODEL_FILES = {
    'Haq87_SealevelCurve' : os.path.join(BUNDLE_SEA_LEVEL_PATH, 'Haq87_SealevelCurve.dat'),
    'Haq87_SealevelCurve_Longterm' : os.path.join(BUNDLE_SEA_LEVEL_PATH, 'Haq87_SealevelCurve_Longterm.dat')
}
# Sea level model names.
BUNDLE_SEA_LEVEL_MODEL_NAMES = BUNDLE_SEA_LEVEL_MODEL_FILES.keys()


if __name__ == '__main__':
    
    try:
        # Gather command-line options.
        # But don't add options for data that we've bundled.
        parser = backtrack.get_command_line_parser(False)
        
        # Allow user to override default lithologies filename
        # (if they don't want the one in the bundled data).
        parser.add_argument('-l', '--lithologies_filename', type=backtrack.argparse_unicode,
                default=BUNDLE_DEFAULT_LITHOLOGIES_FILENAME,
                metavar='lithologies_filename',
                help='Optional lithologies filename used to lookup density, surface porosity and porosity decay. '
                    'Defaults to "{0}".'.format(BUNDLE_DEFAULT_LITHOLOGIES_FILENAME))
        
        # Optional dynamic topography model name.
        parser.add_argument('-y', '--dynamic_topography_model', type=str,
                metavar='dynamic_topography_model',
                help='Optional dynamic topography through time at well location. '
                    'Can be used both for oceanic floor and continental passive margin '
                    '(ie, well location inside or outside age grid). '
                    'Choices include {0}.'.format(', '.join(BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_NAMES)))
        
        parser.add_argument('-sl', '--sea_level_model', type=str,
                metavar='sea_level_model',
                help='Optional sea level model used to obtain sea level (relative to present-day) over time. '
                    'Choices include {0}.'.format(', '.join(BUNDLE_SEA_LEVEL_MODEL_NAMES)))
        
        # Parse command-line options.
        args = parser.parse_args()
        
        # Do any necessary post-processing/validation of parsed options.
        decompacted_columns, ocean_age_to_depth_model = backtrack.post_process_command_line(args)
        
        # Convert dynamic topography model name to list filename (if specified).
        if args.dynamic_topography_model is None:
            dynamic_topography_model_info = None
        else:
            try:
                dynamic_topography_model_info = BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_INFOS[args.dynamic_topography_model]
            except KeyError:
                raise argparse.ArgumentTypeError("%s is not a valid dynamic topography model name" % args.dynamic_topography_model)
        
        # Convert sea level model name to filename (if specified).
        if args.sea_level_model is None:
            sea_level_filename = None
        else:
            try:
                sea_level_filename = BUNDLE_SEA_LEVEL_MODEL_FILES[args.sea_level_model]
            except KeyError:
                raise argparse.ArgumentTypeError("%s is not a valid sea level model name" % args.sea_level_model)
        
        # Backtrack and write output data.
        backtrack.backtrack_and_write_decompacted(
            args.output_filename,
            args.well_filename,
            args.lithologies_filename,
            BUNDLE_AGE_GRID_FILENAME,
            BUNDLE_TOPOGRAPHY_FILENAME,
            BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,
            BUNDLE_CRUSTAL_THICKNESS_FILENAME,
            dynamic_topography_model_info,
            sea_level_filename,
            args.base_lithology_name,
            ocean_age_to_depth_model,
            (args.rift_start_time, args.rift_end_time),
            decompacted_columns,
            args.well_location,
            args.well_columns[0], # well_bottom_age_column
            args.well_columns[1], # well_bottom_depth_column
            args.well_columns[2], # well_lithology_column
            args.output_well_filename)
        
        sys.exit(0)
        
    except Exception as exc:
        print('ERROR: {0}'.format(exc), file=sys.stderr)
        # Uncomment this to print traceback to location of raised exception.
        #traceback.print_exc()
        
        sys.exit(1)

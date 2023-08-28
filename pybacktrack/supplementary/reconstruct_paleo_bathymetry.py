
#
# Copyright (C) 2023 The University of Sydney, Australia
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

import csv
import os
import pybacktrack
import sys

#
# To install the above dependencies with conda:
#   conda create -n <conda-environment> -c conda-forge pybacktrack
#   conda activate <conda-environment>
# ...where <conda-environment> should be replaced with the name of your conda environment.
#


########################
# Command-line parsing #
########################

def main():
    
    __description__ = """Reconstruct a present-day location to get paleobathymetry (and reconstructed locations).
    
    NOTE: Separate the positional and optional arguments with '--' (workaround for bug in argparse module).
    For example...

    python reconstruct_paleo_bathymetry.py ... -x 0 0 -- paleo_bathymetry.txt
    """

    import argparse
    from pybacktrack.dynamic_topography import ArgParseDynamicTopographyAction
    from pybacktrack.lithology import ArgParseLithologyAction, DEFAULT_BUNDLED_LITHOLOGY_SHORT_NAME, BUNDLED_LITHOLOGY_SHORT_NAMES

    def argparse_unicode(value_string):
        try:
            if sys.version_info[0] >= 3:
                filename = value_string
            else:
                # Filename uses the system encoding - decode from 'str' to 'unicode'.
                filename = value_string.decode(sys.getfilesystemencoding())
        except UnicodeDecodeError:
            raise argparse.ArgumentTypeError("Unable to convert filename %s to unicode" % value_string)
        
        return filename
        
    def parse_positive_integer(value_string):
        try:
            value = int(value_string)
        except ValueError:
            raise argparse.ArgumentTypeError("%s is not an integer" % value_string)
        
        if value <= 0:
            raise argparse.ArgumentTypeError("%g is not a positive integer" % value)
        
        return value
        
    def parse_positive_float(value_string):
        try:
            value = float(value_string)
        except ValueError:
            raise argparse.ArgumentTypeError("%s is not a (floating-point) number" % value_string)
        
        if value <= 0:
            raise argparse.ArgumentTypeError("%g is not a positive (floating-point) number" % value)
        
        return value
        
    def parse_non_negative_float(value_string):
        try:
            value = float(value_string)
        except ValueError:
            raise argparse.ArgumentTypeError("%s is not a (floating-point) number" % value_string)
        
        if value < 0:
            raise argparse.ArgumentTypeError("%g is a negative (floating-point) number" % value)
        
        return value

    # Action to parse a longitude/latitude location.
    class ArgParseLongitudeLatitudeAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            if len(values) != 2:
                parser.error("need two values for (longitude, latitude)")
            
            try:
                # Convert strings to float.
                longitude = float(values[0])
                latitude = float(values[1])
            except ValueError:
                parser.error("encountered a longitude or latitude that is not a floating-point number")
                
            if longitude < -360 or longitude > 360:
                parser.error('longitude should be in the range [-360, 360]')
            if latitude < -90 or latitude > 90:
                parser.error('latitude should be in the range [-90, 90]')
            
            setattr(namespace, self.dest, (longitude, latitude))


    ocean_age_to_depth_model_name_dict = dict((model, model_name) for model, model_name, _ in pybacktrack.age_to_depth.ALL_MODELS)
    default_ocean_age_to_depth_model_name = ocean_age_to_depth_model_name_dict[pybacktrack.age_to_depth.DEFAULT_MODEL]
    

    #
    # Gather command-line options.
    #
    # Note: Most of these were copied from "pybacktrack.paleo_bathymetry".
    #
    
    # The command-line parser.
    parser = argparse.ArgumentParser(description=__description__, formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument('-i', '--time_increment', type=parse_positive_float, default=1,
            help='The time increment in My. Value must be positive (and can be non-integral). Defaults to 1 My.')
    
    parser.add_argument('--anchor', type=parse_positive_integer, default=0,
            dest='anchor_plate_id',
            help='Anchor plate id used when reconstructing paleobathymetry grid points. Defaults to zero.')
    
    parser.add_argument('-et', '--exclude_distances_to_trenches_kms', type=parse_non_negative_float, nargs=2,
            metavar=('SUBDUCTING_DISTANCE_KMS', 'OVERRIDING_DISTANCE_KMS'),
            help='The two distances to present-day trenches (on subducting and overriding sides, in that order) '
                 'to exclude bathymetry grid points (in kms). Defaults to using built-in per-trench defaults.')
    
    # Allow user to override the default lithology filename, and also specify bundled lithologies.
    parser.add_argument(
        '-l', '--lithology_filenames', nargs='+', action=ArgParseLithologyAction,
        metavar='lithology_filename',
        default=[pybacktrack.bundle_data.DEFAULT_BUNDLE_LITHOLOGY_FILENAME],
        help='Optional lithology filenames used to lookup density, surface porosity and porosity decay. '
             'If more than one file provided then conflicting lithologies in latter files override those in former files. '
             'You can also choose built-in (bundled) lithologies (in any order) - choices include {0}. '
             'Defaults to "{1}" if nothing specified.'.format(
                 ', '.join('"{0}"'.format(short_name) for short_name in BUNDLED_LITHOLOGY_SHORT_NAMES),
                 DEFAULT_BUNDLED_LITHOLOGY_SHORT_NAME))
    
    parser.add_argument(
        '-b', '--lithology_name', type=str, default=pybacktrack.DEFAULT_PALEO_BATHYMETRY_LITHOLOGY_NAME,
        metavar='lithology_name',
        help='Lithology name of the all sediment (must be present in lithologies file). '
             'The total sediment thickness at all sediment locations consists of a single lithology (in this workflow). '
             'Defaults to "{0}".'.format(pybacktrack.DEFAULT_PALEO_BATHYMETRY_LITHOLOGY_NAME))
    
    parser.add_argument(
        '-m', '--ocean_age_to_depth_model', nargs='+', action=pybacktrack.age_to_depth.ArgParseAgeModelAction,
        metavar='model_parameter',
        default=pybacktrack.age_to_depth.DEFAULT_MODEL,
        help='The oceanic model used to convert age to depth. '
             'It can be the name of an in-built oceanic age model: {0} (defaults to {1}). '
             'Or it can be an age model filename followed by two integers representing the age and depth column indices, '
             'where the file should contain at least two columns (one containing the age and the other the depth).'.format(
                 ', '.join(model_name for _, model_name, _ in pybacktrack.age_to_depth.ALL_MODELS),
                 default_ocean_age_to_depth_model_name))
    
    # Allow user to override default age grid filename (if they don't want the one in the bundled data).
    parser.add_argument(
        '-a', '--age_grid_filename', type=argparse_unicode,
        default=pybacktrack.bundle_data.BUNDLE_AGE_GRID_FILENAME,
        metavar='age_grid_filename',
        help='Optional age grid filename used to obtain age of oceanic crust. '
             'Crust is oceanic at locations inside masked age grid region, and continental outside. '
             'Defaults to the bundled data file "{0}".'.format(pybacktrack.bundle_data.BUNDLE_AGE_GRID_FILENAME))
    
    # Allow user to override default total sediment thickness filename (if they don't want the one in the bundled data).
    parser.add_argument(
        '-s', '--total_sediment_thickness_filename', type=argparse_unicode,
        default=pybacktrack.bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,
        metavar='total_sediment_thickness_filename',
        help='Optional filename used to obtain total sediment thickness grid. '
                'Defaults to the bundled data file "{0}".'.format(pybacktrack.bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME))
    
    # Allow user to override default crustal thickness filename (if they don't want the one in the bundled data).
    parser.add_argument(
        '-k', '--crustal_thickness_filename', type=argparse_unicode,
        default=pybacktrack.bundle_data.BUNDLE_CRUSTAL_THICKNESS_FILENAME,
        metavar='crustal_thickness_filename',
        help='Optional filename used to obtain crustal thickness grid. '
             'Defaults to the bundled data file "{0}".'.format(pybacktrack.bundle_data.BUNDLE_CRUSTAL_THICKNESS_FILENAME))
    
    # Allow user to override default topography filename (if they don't want the one in the bundled data).
    parser.add_argument(
        '-t', '--topography_filename', type=argparse_unicode,
        default=pybacktrack.bundle_data.BUNDLE_TOPOGRAPHY_FILENAME,
        metavar='topography_filename',
        help='Optional topography grid filename used to obtain water depth. '
             'Defaults to the bundled data file "{0}".'.format(pybacktrack.bundle_data.BUNDLE_TOPOGRAPHY_FILENAME))
    
    # Allow user to override default rotation filenames (used to reconstruct sediment-deposited crust).
    #
    # Defaults to built-in global rotations associated with topological model used to generate built-in rift start/end time grids.
    parser.add_argument(
        '-r', '--rotation_filenames', type=str, nargs='+',
        default=pybacktrack.bundle_data.BUNDLE_RECONSTRUCTION_ROTATION_FILENAMES,
        metavar='rotation_filename',
        help='One or more rotation files (to reconstruct sediment-deposited crust). '
             'Defaults to the bundled global rotations associated with topological model '
             'used to generate built-in rift start/end time grids: {0}'.format(pybacktrack.bundle_data.BUNDLE_RECONSTRUCTION_ROTATION_FILENAMES))
    
    # Allow user to override default static polygon filename (to assign plate IDs to points on sediment-deposited crust).
    #
    # Defaults to built-in static polygons associated with topological model used to generate built-in rift start/end time grids.
    parser.add_argument(
        '-p', '--static_polygon_filename', type=str,
        default=pybacktrack.bundle_data.BUNDLE_RECONSTRUCTION_STATIC_POLYGON_FILENAME,
        metavar='static_polygon_filename',
        help='File containing static polygons (to assign plate IDs to points on sediment-deposited crust). '
             'Defaults to the bundled static polygons associated with topological model '
             'used to generate built-in rift start/end time grids: {0}'.format(pybacktrack.bundle_data.BUNDLE_RECONSTRUCTION_STATIC_POLYGON_FILENAME))
    
    # Can optionally specify dynamic topography as a triplet of filenames or a model name (if using bundled data) but not both.
    dynamic_topography_argument_group = parser.add_mutually_exclusive_group()
    dynamic_topography_argument_group.add_argument(
        '-ym', '--bundle_dynamic_topography_model', type=str,
        metavar='bundle_dynamic_topography_model',
        help='Optional dynamic topography through time at well location. '
             'If no model specified then dynamic topography is ignored. '
             'Can be used both for oceanic floor and continental passive margin. '
             'Choices include {0}.'.format(', '.join(pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_NAMES)))
    dynamic_topography_argument_group.add_argument(
        '-y', '--dynamic_topography_model', nargs='+', action=ArgParseDynamicTopographyAction,
        metavar='dynamic_topography_filename',
        help='Optional dynamic topography through time. '
             'Can be used both for oceanic floor and continental passive margin. '
             'First filename contains a list of dynamic topography grids (and associated times). '
             'Note that each grid must be in the mantle reference frame. '
             'Second filename contains static polygons associated with dynamic topography model '
             '(used to assign plate ID to well location so it can be reconstructed). '
             'Third filename (and optional fourth, etc) are the rotation files associated with model '
             '(only the rotation files for static continents/oceans are needed - ie, deformation rotations not needed). '
             'Each row in the grid list file should contain two columns. First column containing '
             'filename (relative to directory of list file) of a dynamic topography grid at a particular time. '
             'Second column containing associated time (in Ma).')
    
    # Can optionally specify sea level as a filename or model name (if using bundled data) but not both.
    sea_level_argument_group = parser.add_mutually_exclusive_group()
    sea_level_argument_group.add_argument(
        '-slm', '--bundle_sea_level_model', type=str,
        metavar='bundle_sea_level_model',
        help='Optional sea level model used to obtain sea level (relative to present-day) over time. '
             'If no model (or filename) is specified then sea level is ignored. '
             'Choices include {0}.'.format(', '.join(pybacktrack.bundle_data.BUNDLE_SEA_LEVEL_MODEL_NAMES)))
    sea_level_argument_group.add_argument(
        '-sl', '--sea_level_model', type=argparse_unicode,
        metavar='sea_level_model',
        help='Optional file used to obtain sea level (relative to present-day) over time. '
             'If no filename (or model) is specified then sea level is ignored. '
             'If specified then each row should contain an age column followed by a column for sea level (in metres).')
    
    parser.add_argument(
        '-bp', '--output_positive_bathymetry_below_sea_level', action='store_true',
        help='Output positive bathymetry values below sea level (the same as backtracked water depths at a drill site). '
             'This is the opposite of typical topography/bathymetry grids that have negative values below sea level (and positive above). '
             'So the default matches typical topography/bathymetry grids (outputs negative bathymetry values below sea level).')

    parser.add_argument(
        '-ot', '--output_time', action='store_true',
        help='Output the reconstruction time (in Ma) as the last column. Default is not to output.')

    parser.add_argument(
        '-ol', '--output_long_lat', action='store_true',
        help='Output the reconstructed longitude and latitude as the first and second columns. Default is not to output.')

    parser.add_argument(
        '-mt', '--max_time', type=parse_non_negative_float,
        metavar='max_time',
        help='Output is not generated back beyond the specified time (in Ma). Value must not be negative. '
             'If not specified then defaults to age of crust (if location is oceanic) or rift start age (if location is continental).')
    
    parser.add_argument(
        '-x', '--longitude_latitude', nargs=2, action=ArgParseLongitudeLatitudeAction,
        required=True,
        metavar=('longitude', 'latitude'),
        help='Present-day location to reconstruct paleobathymetry. Specified as (longitude, latitude) in degrees.')
    
    parser.add_argument(
        'output_filename', type=argparse_unicode,
        metavar='output_filename',
        help='The name of file to contain the paleobathymetry (and reconstructed locations).')
    
    #
    # Parse command-line options.
    #
    args = parser.parse_args()
    
    #
    # Do any necessary post-processing/validation of parsed options.
    #
    
    # Get dynamic topography model info.
    if args.bundle_dynamic_topography_model is not None:
        try:
            # Convert dynamic topography model name to model info.
            # We don't need to do this (since DynamicTopography.create_from_model_or_bundled_model_name() will do it for us) but it helps check user errors.
            dynamic_topography_model = pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS[args.bundle_dynamic_topography_model]
        except KeyError:
            raise ValueError("%s is not a valid dynamic topography model name" % args.bundle_dynamic_topography_model)
    elif args.dynamic_topography_model is not None:
        dynamic_topography_model = args.dynamic_topography_model
    else:
        dynamic_topography_model = None
    
    # Get sea level filename.
    if args.bundle_sea_level_model is not None:
        try:
            # Convert sea level model name to filename.
            # We don't need to do this (since SeaLevel.create_from_model_or_bundled_model_name() will do it for us) but it helps check user errors.
            sea_level_model = pybacktrack.bundle_data.BUNDLE_SEA_LEVEL_MODELS[args.bundle_sea_level_model]
        except KeyError:
            raise ValueError("%s is not a valid sea level model name" % args.bundle_sea_level_model)
    elif args.sea_level_model is not None:
        sea_level_model = args.sea_level_model
    else:
        sea_level_model = None
    
    input_longitude, input_latitude = args.longitude_latitude
    
    # Reconstruct paleo bathymetry.
    paleo_bathymetry = pybacktrack.reconstruct_paleo_bathymetry(
        [(input_longitude, input_latitude)],
        args.max_time,
        args.time_increment,
        args.lithology_filenames,
        args.age_grid_filename,
        args.topography_filename,
        args.total_sediment_thickness_filename,
        args.crustal_thickness_filename,
        args.rotation_filenames,
        args.static_polygon_filename,
        dynamic_topography_model,
        sea_level_model,
        args.lithology_name,
        args.ocean_age_to_depth_model,
        args.exclude_distances_to_trenches_kms,
        None, # region_plate_ids
        args.anchor_plate_id,
        args.output_positive_bathymetry_below_sea_level)
    
    # Open the output file for writing.
    with open(args.output_filename, 'w', newline='') as output_file:
        # Write the header information.
        output_file.write('#' + os.linesep)
        output_file.write('# Longitude: {}'.format(input_longitude) + os.linesep)  # longitude
        output_file.write('# Latitude: {}'.format(input_latitude) + os.linesep)  # latitude
        output_file.write('#' + os.linesep)
        
        # Write reconstructed locations and paleobathymetry to the output file.
        drill_site_output_writer = csv.writer(output_file, delimiter=' ')
        for reconstruction_time, paleo_bathymetry_at_reconstruction_time in sorted(paleo_bathymetry.items()):
            # There's only one reconstructed location/bathymetry per reconstruction time (since we only specified a single input location).
            reconstructed_longitude, reconstructed_latitude, bathymetry = paleo_bathymetry_at_reconstruction_time[0]
            # Determine which columns go into the row.
            row = (bathymetry,)
            if args.output_long_lat:
                row = (reconstructed_longitude, reconstructed_latitude) + row  # add as first two columns
            if args.output_time:
                row = row + (reconstruction_time,)  # add as last column
            # Write the row to the output file.
            drill_site_output_writer.writerow(row)


if __name__ == '__main__':
    
    import traceback
    
    try:
        main()
        sys.exit(0)
    except Exception as exc:
        print('ERROR: {0}'.format(exc), file=sys.stderr)
        # Uncomment this to print traceback to location of raised exception.
        #traceback.print_exc()
        sys.exit(1)

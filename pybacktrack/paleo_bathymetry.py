
#
# Copyright (C) 2021 The University of Sydney, Australia
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

"""Generate paleo bathymetry grids through time.

:func:`pybacktrack.reconstruct_backtrack_bathymetry` reconstructs and backtracks
sediment-covered crust through time to get paleo bathymetry.
"""


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import math
import os.path
import pybacktrack.age_to_depth as age_to_depth
import pybacktrack.bundle_data
from pybacktrack.dynamic_topography import DynamicTopography
from pybacktrack.lithology import read_lithologies_files, DEFAULT_BASE_LITHOLOGY_NAME
from pybacktrack.sea_level import SeaLevel
from pybacktrack.util.call_system_command import call_system_command
import pybacktrack.version
from pybacktrack.well import Well
import pygplates
import sys
import warnings


# Default grid spacing (in degrees) when generating uniform lon/lat spacing of sample points.
DEFAULT_GRID_SPACING_DEGREES = 1


def reconstruct_backtrack_bathymetry(
        input_points,  # note: you can use 'generate_input_points_grid()' to generate a global lat/lon grid
        oldest_time,
        time_increment=1,
        lithology_filenames=[pybacktrack.bundle_data.DEFAULT_BUNDLE_LITHOLOGY_FILENAME],
        age_grid_filename=pybacktrack.bundle_data.BUNDLE_AGE_GRID_FILENAME,
        topography_filename=pybacktrack.bundle_data.BUNDLE_TOPOGRAPHY_FILENAME,
        total_sediment_thickness_filename=pybacktrack.bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,
        crustal_thickness_filename=pybacktrack.bundle_data.BUNDLE_CRUSTAL_THICKNESS_FILENAME,
        dynamic_topography_model=None,
        sea_level_model=None,
        base_lithology_name=DEFAULT_BASE_LITHOLOGY_NAME,
        ocean_age_to_depth_model=age_to_depth.DEFAULT_MODEL):
    # Adding function signature on first line of docstring otherwise Sphinx autodoc will print out
    # the expanded values of the bundle filenames.
    """reconstruct_backtrack_bathymetry(\
        input_points,\
        oldest_time,\
        time_increment=1,\
        lithology_filenames=[pybacktrack.DEFAULT_BUNDLE_LITHOLOGY_FILENAME],\
        age_grid_filename=pybacktrack.BUNDLE_AGE_GRID_FILENAME,\
        topography_filename=pybacktrack.BUNDLE_TOPOGRAPHY_FILENAME,\
        total_sediment_thickness_filename=pybacktrack.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,\
        crustal_thickness_filename=pybacktrack.BUNDLE_CRUSTAL_THICKNESS_FILENAME,\
        dynamic_topography_model=None,\
        sea_level_model=None,\
        base_lithology_name=pybacktrack.DEFAULT_BASE_LITHOLOGY_NAME,\
        ocean_age_to_depth_model=pybacktrack.AGE_TO_DEPTH_DEFAULT_MODEL)
    Reconstructs and backtracks sediment-covered crust through time to get paleo bathymetry.
    
    Parameters
    ----------
    input_points: sequence of (longitude, latitude) tuples
        The point locations to sample bathymetry at present day.
        Note that any samples outside the masked region of the total sediment thickness grid are ignored.
    oldest_time: int
        The oldest time (in Ma) that output is generated back to (from present day). Value must be positive.
    time_increment: int
        The time increment (in My) that output is generated (from present day back to oldest time). Value must be positive.
    lithology_filenames: list of string, optional
        One or more text files containing lithologies.
    age_grid_filename : string, optional
        Age grid filename.
        Used to obtain age of oceanic crust at present day.
        Crust is oceanic at locations inside masked age grid region, and continental outside.
    topography_filename : string, optional
        Topography filename.
        Used to obtain bathymetry at present day.
    total_sediment_thickness_filename : string, optional
        Total sediment thickness filename.
        Used to obtain total sediment thickness at present day.
    crustal_thickness_filename : string, optional
        Crustal thickness filename.
        Used to obtain crustal thickness at present day.
    dynamic_topography_model : string or tuple, optional
        Represents a time-dependent dynamic topography raster grid (in *mantle* frame).
        
        Can be either:
        
        * A string containing the name of a bundled dynamic topography model.
        
          Choices include ``terra``, ``M1``, ``M2``, ``M3``, ``M4``, ``M5``, ``M6``, ``M7``, ``ngrand``, ``s20rts`` and ``smean``.
        * A tuple containing the three elements (dynamic topography list filename, static polygon filename, rotation filenames).
        
          The first tuple element is the filename of file containing list of dynamic topography grids (and associated times).
          Each row in this list file should contain two columns.
          First column containing filename (relative to list file) of a dynamic topography grid at a particular time.
          Second column containing associated time (in Ma).
          The second tuple element is the filename of file containing static polygons associated with dynamic topography model.
          This is used to assign plate ID to well location so it can be reconstructed.
          The third tuple element is the filename of the rotation file associated with model.
          Only the rotation file for static continents/oceans is needed (ie, deformation rotations not needed).
        
    sea_level_model : string, optional
        Used to obtain sea levels relative to present day.
        Can be either the name of a bundled sea level model, or a sea level filename.
        Bundled sea level models include ``Haq87_SealevelCurve`` and ``Haq87_SealevelCurve_Longterm``.
    base_lithology_name : string, optional
        Lithology name of the all sediment (must be present in lithologies file).
        The total sediment thickness at all sediment locations is consists of a single lithology.
        Defaults to ``Shale``.
    ocean_age_to_depth_model : {pybacktrack.AGE_TO_DEPTH_MODEL_GDH1, pybacktrack.AGE_TO_DEPTH_MODEL_CROSBY_2007} or function, optional
        The model to use when converting ocean age to depth at well location
        (if on ocean floor - not used for continental passive margin).
        It can be one of the enumerated values, or a callable function accepting a single non-negative age parameter and returning depth (in metres).
    
    Raises
    ------
    ValueError
        If ``oldest_time`` is not a positive integer or if ``time_increment`` is not a positive integer.

    Notes
    -----
    Any input points outside the masked region of the total sediment thickness grid are ignored (since bathymetry relies on sediment decompaction over time).
    """
    
    if oldest_time <= 0:
        raise ValueError("'oldest_time' should be positive")
    if time_increment <= 0:
        raise ValueError("'time_increment' should be positive")
    
    # Read the lithologies from one or more text files.
    #
    # Read all the lithology files and merge their dicts.
    # Subsequently specified files override previous files in the list.
    # So if the first and second files have the same lithology then the second lithology is used.
    lithologies = read_lithologies_files(lithology_filenames)

    # Sample the total sediment thickness grid.
    total_sediment_thickness_grid_samples = _grdtrack(input_points, total_sediment_thickness_filename)

    # Ignore samples outside total sediment thickness grid (masked region) since we can only backtrack where there's sediment.
    #
    # Note: The 3rd value (index 2) of each sample is the total sediment thickness (first two values are longitude and latitude).
    #       A value of NaN means the sample is outside the masked region of the grid.
    total_sediment_thickness_grid_samples = [grid_sample for grid_sample in total_sediment_thickness_grid_samples if not math.isnan(grid_sample[2])]

    # Add age and topography to the total sediment thickness grid samples.
    total_sediment_thickness_and_age_and_topography_grid_samples = _grdtrack(total_sediment_thickness_grid_samples, age_grid_filename, topography_filename)

    # Separate grid samples into oceanic and continental.
    continental_grid_samples = []
    continental_points = []
    oceanic_grid_samples = []
    oceanic_points = []
    for longitude, latitude, total_sediment_thickness, age, topography in total_sediment_thickness_and_age_and_topography_grid_samples:

        # If topography sampled outside grid then set topography to zero.
        # Shouldn't happen since topography grid is not masked anywhere.
        if math.isnan(topography):
            topography = 0.0
    
        # Topography is negative in ocean but water depth is positive.
        water_depth = -topography
        # Clamp water depth so it's below sea level (ie, must be >= 0).
        water_depth = max(0, water_depth)

        point_on_sphere = pygplates.PointOnSphere(latitude, longitude)

        # If sampled outside age grid then is on continental crust near a passive margin.
        if math.isnan(age):
            continental_grid_samples.append(
                    (longitude, latitude, total_sediment_thickness, water_depth))
            continental_points.append(point_on_sphere)
        else:
            oceanic_grid_samples.append(
                    (longitude, latitude, total_sediment_thickness, water_depth, age))
            oceanic_points.append(point_on_sphere)

    # Grid filenames for continental rifting start/end times.
    rift_start_grid_filename = os.path.join(pybacktrack.bundle_data.BUNDLE_RIFTING_PATH, '2019_v2', 'rift_start_grid.nc')
    rift_end_grid_filename = os.path.join(pybacktrack.bundle_data.BUNDLE_RIFTING_PATH, '2019_v2', 'rift_end_grid.nc')

    # Add crustal thickness and rift start/end times to continental grid samples.
    continental_grid_samples = _grdtrack(continental_grid_samples, crustal_thickness_filename, rift_start_grid_filename, rift_end_grid_filename)

    # Iterate over the *oceanic* grid samples.
    for longitude, latitude, present_day_total_sediment_thickness, present_day_water_depth, age in oceanic_grid_samples:
        
        # Create a well at the current grid sample location with a single stratigraphic layer of total sediment thickness
        # that began sediment deposition at 'age' Ma (and finished at present day).
        well = Well()
        well.add_compacted_unit(0.0, age, 0.0, present_day_total_sediment_thickness, [(base_lithology_name, 1.0)], lithologies)
        well.longitude, well.latitude = longitude, latitude

        # Unload the present day sediment to get unloaded present day water depth.
        # Apply an isostatic correction to the total sediment thickness (we decompact the well at present day to find this).
        # Note that sea level variations don't apply here because they are zero at present day.
        present_day_tectonic_subsidence = present_day_water_depth + well.decompact(0.0).get_sediment_isostatic_correction()

    # Iterate over the *continental* grid samples.
    for longitude, latitude, present_day_total_sediment_thickness, present_day_water_depth, present_day_crustal_thickness, rift_start_age, rift_end_age in continental_grid_samples:
        
        # Create a well at the current grid sample location with a single stratigraphic layer of total sediment thickness
        # that began sediment deposition when rifting began (and finished at present day).
        well = Well()
        well.add_compacted_unit(0.0, rift_start_age, 0.0, present_day_total_sediment_thickness, [(base_lithology_name, 1.0)], lithologies)
        well.longitude, well.latitude = longitude, latitude

        # Unload the present day sediment to get unloaded present day water depth.
        # Apply an isostatic correction to the total sediment thickness (we decompact the well at present day to find this).
        # Note that sea level variations don't apply here because they are zero at present day.
        present_day_tectonic_subsidence = present_day_water_depth + well.decompact(0.0).get_sediment_isostatic_correction()


def generate_input_points_grid(grid_spacing_degrees):
    """
    Generate a global grid of points uniformly spaced in latitude and longitude.

    Returns a list of (longitude, latitude) tuples.
    """
    
    if grid_spacing_degrees == 0:
        raise ValueError('Grid spacing cannot be zero.')
    
    input_points = []
    
    # Data points start *on* dateline (-180).
    # If 180 is an integer multiple of grid spacing then final longitude also lands on dateline (+180).
    num_latitudes = int(math.floor(180.0 / grid_spacing_degrees)) + 1
    num_longitudes = int(math.floor(360.0 / grid_spacing_degrees)) + 1
    for lat_index in range(num_latitudes):
        lat = -90 + lat_index * grid_spacing_degrees
        
        for lon_index in range(num_longitudes):
            lon = -180 + lon_index * grid_spacing_degrees
            
            input_points.append((lon, lat))
    
    return input_points


def _grdtrack(
        input,
        *grid_filenames):
    """
    Samples one or more grid files at the specified locations.
    
    'input' is a list of (longitude, latitude, [other_values ...]) tuples where latitude and longitude are in degrees.
    Should at least have 2-tuples (longitude, latitude) but 'grdtrack' allows extra columns.
    
    Returns a list of tuples of float values.
    For example, if input was (longitude, latitude) tuples and one grid file specified then output is (longitude, latitude, sample) tuples.
    If input was (longitude, latitude, value) tuples and two grid file specified then output is (longitude, latitude, value, sample_grid1, sample_grid2) tuples.
    """
    
    # Create a multiline string (one line per lon/lat/value1/etc row).
    location_data = ''.join(
            ' '.join(str(item) for item in row) + '\n' for row in input)

    # The command-line strings to execute GMT 'grdtrack'.
    grdtrack_command_line = ["gmt", "grdtrack"]
    # One or more grid filenames to sample.
    for grid_filename in grid_filenames:
        grdtrack_command_line.append("-G{0}".format(grid_filename))
    
    # Call the system command.
    stdout_data = call_system_command(grdtrack_command_line, stdin=location_data, return_stdout=True)

    # Extract the sampled values.
    output_values = []
    for line in stdout_data.splitlines():
        # Each line returned by GMT grdtrack contains "longitude latitude grid1_value [grid2_value ...]".
        # Note that if GMT returns "NaN" then we'll return float('nan').
        output_value = tuple(float(value) for value in line.split())
        output_values.append(output_value)
    
    return output_values


########################
# Command-line parsing #
########################

def main():
    
    __description__ = """Generate paleo bathymetry grids through time.
    """

    import argparse
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

    # Action to parse dynamic topography model information.
    class ArgParseDynamicTopographyAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            if len(values) < 3:
                parser.error('Dynamic topography model info must have three or more parameters '
                             '(grid list filename, static polygons filename, rotation filename1 [, rotation filename2 [, ...]]).')
            
            grid_list_filename = values[0]
            static_polygons_filename = values[1]
            rotation_filenames = values[2:]  # Needs to be a list.
            
            setattr(namespace, self.dest, (grid_list_filename, static_polygons_filename, rotation_filenames))

    ocean_age_to_depth_model_name_dict = dict((model, model_name) for model, model_name, _ in age_to_depth.ALL_MODELS)
    default_ocean_age_to_depth_model_name = ocean_age_to_depth_model_name_dict[age_to_depth.DEFAULT_MODEL]
    
    #
    # Gather command-line options.
    #
    
    # The command-line parser.
    parser = argparse.ArgumentParser(description=__description__, formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument('--version', action='version', version=pybacktrack.version.__version__)
    
    parser.add_argument('-i', '--time_increment', type=parse_positive_integer, default=1,
            help='The time increment in My. Value must be a positive integer. Defaults to 1 My.')
        
    parser.add_argument('-g', '--grid_spacing', type=float,
            default=DEFAULT_GRID_SPACING_DEGREES,
            help='The grid spacing (in degrees) of sample points in lon/lat space. '
                'Defaults to {0} degrees.'.format(DEFAULT_GRID_SPACING_DEGREES))
    
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
        '-b', '--base_lithology_name', type=str, default=DEFAULT_BASE_LITHOLOGY_NAME,
        metavar='base_lithology_name',
        help='Lithology name of the all sediment (must be present in lithologies file). '
             'The total sediment thickness at all sediment locations is consists of a single lithology (in this workflow). '
             'Defaults to "{0}".'.format(DEFAULT_BASE_LITHOLOGY_NAME))
    
    parser.add_argument(
        '-m', '--ocean_age_to_depth_model', nargs='+', action=age_to_depth.ArgParseAgeModelAction,
        metavar='model_parameter',
        default=age_to_depth.DEFAULT_MODEL,
        help='The oceanic model used to convert age to depth. '
             'It can be the name of an in-built oceanic age model: {0} (defaults to {1}). '
             'Or it can be an age model filename followed by two integers representing the age and depth column indices, '
             'where the file should contain at least two columns (one containing the age and the other the depth).'.format(
                 ', '.join(model_name for _, model_name, _ in age_to_depth.ALL_MODELS),
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

    parser.add_argument('oldest_time', type=parse_positive_integer,
            metavar='oldest_time',
            help='Output is generated from present day back to the oldest time (in Ma). Value must be a positive integer.')
    
    parser.add_argument(
        'output_file_prefix', type=argparse_unicode,
        metavar='output_file_prefix',
        help='The prefix of the output paleo bathymetry grid filenames over time.')
    
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
            # We don't need to do this (since backtrack() will do it for us) but it helps check user errors.
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
            # We don't need to do this (since backtrack() will do it for us) but it helps check user errors.
            sea_level_model = pybacktrack.bundle_data.BUNDLE_SEA_LEVEL_MODELS[args.bundle_sea_level_model]
        except KeyError:
            raise ValueError("%s is not a valid sea level model name" % args.bundle_sea_level_model)
    elif args.sea_level_model is not None:
        sea_level_model = args.sea_level_model
    else:
        sea_level_model = None
    
    # Generate a global latitude/longitude grid of points (with the requested grid spacing).
    input_points = generate_input_points_grid(args.grid_spacing)
    
    # Generate paleo bathymetry grids over the requested time period.
    reconstruct_backtrack_bathymetry(
        input_points,
        args.oldest_time,
        args.time_increment,
        args.lithology_filenames,
        args.age_grid_filename,
        args.topography_filename,
        args.total_sediment_thickness_filename,
        args.crustal_thickness_filename,
        dynamic_topography_model,
        sea_level_model,
        args.base_lithology_name,
        args.ocean_age_to_depth_model)


if __name__ == '__main__':

    # User should not be using this module as a script. They should use 'paleo_bathymetry' when importing and 'paleo_bathymetry_cli' as a script.
    #raise RuntimeError("Use 'python -m pybacktrack.paleo_bathymetry_cli ...', instead of 'python -m pybacktrack.paleo_bathymetry ...'.")
    print("ERROR: Use 'python -m pybacktrack.paleo_bathymetry_cli ...', instead of 'python -m pybacktrack.paleo_bathymetry ...'.", file=sys.stderr)
    sys.exit(1)

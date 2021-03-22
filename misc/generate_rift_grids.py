
#
# Copyright (C) 2021 The University of Sydney, Australia
#
# This program is free software; you can redistribute it and/or modify it under
# the Free Software Foundation.
# the terms of the GNU General Public License, version 2, as published by
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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import itertools
import math
import multiprocessing
import os.path
import pybacktrack
import pygplates
import sys


# Required pygplates version.
# Need version 30 to be able to reconstruct 'using topologies'.
PYGPLATES_VERSION_REQUIRED = pygplates.Version(30)

# Currently using the 2019 v2 deforming model.
DEFORMING_MODEL_NAME = '2019_v2'
# We only go back to 250Ma. Rifting since Pangea began at 240Ma.
DEFORMING_MODEL_OLDEST_TIME = 250

# Default grid spacing (in degrees) when generating uniform lon/lat spacing of sample points.
DEFAULT_GRID_SPACING_DEGREES = 1.0
DEFAULT_GRID_SPACING_MINUTES = 60.0 * DEFAULT_GRID_SPACING_DEGREES


def generate_rift_parameter_points(
        input_points,
        total_sediment_thickness_filename,
        age_grid_filename,
        use_all_cpus=False):
    """Generate rift parameter grids (at non-NaN grid sample locations in total sediment thickness grid).

    Returns a list of tuples (longitude, latitude, rift_start_time, rift_end_time, rift_beta)
    """
    
    # Check the imported pygplates version.
    if pygplates.Version.get_imported_version() < PYGPLATES_VERSION_REQUIRED:
        raise RuntimeError('Using pygplates version {0} but version {1} or greater is required'.format(
                pygplates.Version.get_imported_version(), PYGPLATES_VERSION_REQUIRED))

    # Read the total sediment thickness grid file and gather a list of non-NaN grid locations (ie, (longitude, latitude) tuples).
    #print ('Reading sediment points...')
    sediment_points = [(sample[0], sample[1]) for sample in _gmt_grdtrack(input_points, total_sediment_thickness_filename) if not math.isnan(sample[2])]

    # Read the age grid file (at sediment locations) and only include those that have NaN values (representing non-oceanic points).
    #print ('Reading continent sediment points...')
    continent_sediment_points = [(sample[0], sample[1]) for sample in _gmt_grdtrack(sediment_points, age_grid_filename) if math.isnan(sample[2])]
    num_continent_sediment_points = len(continent_sediment_points)

    # If using a single CPU then just process all ocean/continent points in one call.
    #print ('Reconstructing', num_continent_sediment_points, 'continent sediment points...')
    if not use_all_cpus:
        continent_sediment_rift_parameter_point_list = find_continent_sediment_rift_parameters(continent_sediment_points)
        return continent_sediment_rift_parameter_point_list

    else:  # Use 'multiprocessing' pools to distribute across CPUs...
        # Number of CPUs for our multiprocessing pool.
        try:
            num_cpus = multiprocessing.cpu_count()
        except NotImplementedError:
            num_cpus = 1
        
        # Divide the points into a number of groups equal to twice the number of CPUs in case some groups of points take longer to process than others.
        num_continent_sediment_point_groups = 2 * num_cpus
        num_continent_sediment_point_per_group = math.ceil(float(num_continent_sediment_points) / num_continent_sediment_point_groups)

        # Distribute the groups of points across the multiprocessing pool.
        with multiprocessing.Pool(num_cpus) as pool:
            continent_sediment_rift_parameter_point_lists = pool.map(
                    find_continent_sediment_rift_parameters,
                    (
                        continent_sediment_points[
                            continent_sediment_point_group_index * num_continent_sediment_point_per_group :
                            (continent_sediment_point_group_index + 1) * num_continent_sediment_point_per_group]
                                    for continent_sediment_point_group_index in range(num_continent_sediment_point_groups)
                    ),
                    1) # chunksize
    
    return list(itertools.chain.from_iterable(continent_sediment_rift_parameter_point_lists))


def find_continent_sediment_rift_parameters(
        initial_points):
    """Find rift parameters for each continent-sediment input point that undergoes rift deformation.

    Returns a list of tuples (lon, lat, rift_start_time, rift_end_time, rift_beta).
    """

    # Load the deforming (topological) model.
    topological_model = _read_topological_model(DEFORMING_MODEL_NAME)

    num_continent_sediment_points = len(initial_points)

    rift_start_times = [None] * num_continent_sediment_points
    rift_end_times = [None] * num_continent_sediment_points
    rift_betas = [None] * num_continent_sediment_points
    
    # We start with initial points and reconstruct them through multiple time intervals.
    # At each time interval some points find their rift start/end times and are removed from these lists.
    reconstructed_points = [pygplates.PointOnSphere(lat, lon) for lon, lat in initial_points]
    reconstructed_point_indices = list(range(num_continent_sediment_points))
    reconstructed_crustal_stretching_factors = [1.0] * num_continent_sediment_points
    
    continent_sediment_rift_parameter_points = []

    # Iterate over time intervals.
    # In each time interval some points might have their rift start/end times found and hence do not need to be
    # reconstructed in subsequent time intervals (thus improving processing time).
    for initial_time in range(0, DEFORMING_MODEL_OLDEST_TIME, 10):
        final_time = initial_time + 10
        #print ('     reconstructing time', initial_time, final_time)

        # Reconstruct (using topologies) the initial reconstructed points over the time interval.
        time_spans = topological_model.reconstruct_geometry(
                reconstructed_points,
                initial_time=initial_time,
                oldest_time=final_time,
                youngest_time=initial_time,
                initial_scalars={pygplates.ScalarType.gpml_crustal_stretching_factor : reconstructed_crustal_stretching_factors})
        
        # Keep track of which points have found their rift start/end times (we'll remove these from subsequent time intervals).
        finished_reconstructed_point_indices = set()

        for time in range(initial_time, final_time + 1, 1):
            topology_point_locations = time_spans.get_topology_point_locations(time, return_inactive_points=True)
            crustal_stretching_factors = time_spans.get_scalar_values(time, return_inactive_points=True)[pygplates.ScalarType.gpml_crustal_stretching_factor]
            for reconstructed_point_index, topology_point_location in enumerate(topology_point_locations):
                # We didn't ask for any points to be deactivated, so this shouldn't happen, but check just in case.
                if not topology_point_location:
                    finished_reconstructed_point_indices.add(reconstructed_point_index)
                    continue

                # Skip current point if we've already finished with it.
                if reconstructed_point_index in finished_reconstructed_point_indices:
                    continue

                # Index into original rift start/end time arrays (for the current group of points).
                point_index = reconstructed_point_indices[reconstructed_point_index]

                # First find rift end time (we're processing backward in time) and then find rift start time.
                if rift_end_times[point_index] is None:
                    if topology_point_location.located_in_resolved_network():
                        rift_end_times[point_index] = time
                elif rift_start_times[point_index] is None:
                    if not topology_point_location.located_in_resolved_network():
                        # Only add rift start time if there's been stretching (we ignore compression since that's not rifting).
                        #
                        # Stretching factor is initial thickness over current thickness. And since initial thickness is at present day, crust that is
                        # stretching forward in time is actually thickening backward in time, so we need to invert the crustal stretching factor.
                        crustal_stretching_factor_forward_in_time = 1.0 / crustal_stretching_factors[reconstructed_point_index]
                        if crustal_stretching_factor_forward_in_time > 1.0:
                            rift_start_times[point_index] = time
                            rift_betas[point_index] = crustal_stretching_factor_forward_in_time
                        # Either we've found rift start (and end) times for the current point, or we've encountered compression (not extension).
                        # Either way we're finished with it.
                        finished_reconstructed_point_indices.add(reconstructed_point_index)
        
        # Get the reconstructed points/scalars at the final time of the time span.
        # These will be our initial points at the initial time of the next time span.
        reconstructed_points = time_spans.get_geometry_points(final_time, return_inactive_points=True)
        reconstructed_crustal_stretching_factors = time_spans.get_scalar_values(final_time, return_inactive_points=True)[pygplates.ScalarType.gpml_crustal_stretching_factor]

        # Remove those reconstructed points/scalars that we've found rift start/end times for.
        # Note: We process in reverse order so that indices are not affected by previous removals.
        for reconstructed_point_index in sorted(finished_reconstructed_point_indices, reverse=True):
            del reconstructed_points[reconstructed_point_index]
            del reconstructed_crustal_stretching_factors[reconstructed_point_index]
            del reconstructed_point_indices[reconstructed_point_index]
        
        # If we've found rift start/end times for all points in the group then we're done with the group.
        if not reconstructed_points:
            break

    
    # Output points that we have found a rift start and end time for.
    for point_index in range(num_continent_sediment_points):
        rift_start_time = rift_start_times[point_index]
        rift_end_time = rift_end_times[point_index]
        rift_beta = rift_betas[point_index]
        if (rift_start_time is not None and
            rift_end_time is not None and
            rift_beta is not None):
            initial_point = initial_points[point_index]
            continent_sediment_rift_parameter_points.append(
                    (initial_point[0], initial_point[1], rift_start_time, rift_end_time, rift_beta))

    return continent_sediment_rift_parameter_points


def _gmt_grdtrack(
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
    stdout_data = pybacktrack.util.call_system_command.call_system_command(grdtrack_command_line, stdin=location_data, return_stdout=True)

    # Extract the sampled values.
    output_values = []
    for line in stdout_data.splitlines():
        # Each line returned by GMT grdtrack contains "longitude latitude grid1_value [grid2_value ...]".
        # Note that if GMT returns "NaN" then we'll return float('nan').
        output_value = tuple(float(value) for value in line.split())
        output_values.append(output_value)
    
    return output_values


def _gmt_nearneighbor(
        input,
        grid_spacing_degrees,
        grid_filename):
    """
    Run 'gmt nearneighbor' on grid locations/values to output a grid file.
    
    'input' is a list of (longitude, latitude, value) tuples where latitude and longitude are in degrees.
    'grid_spacing_degrees' is spacing of output grid points in degrees.
    """
    
    # Create a multiline string (one line per lon/lat/value row).
    input_data = ''.join(
            ' '.join(str(item) for item in row) + '\n' for row in input)

    # The command-line strings to execute GMT 'nearneighbor'.
    nearneighbor_command_line = [
        "gmt",
        "nearneighbor",
        "-N4/1", # Divide search radius into 4 sectors but only require a value in 1 sector.
        "-S{0}d".format(0.7 * grid_spacing_degrees),
        "-I{0}".format(grid_spacing_degrees),
        # Use GMT gridline registration since our input point grid has data points on the grid lines.
        # Gridline registration is the default so we don't need to force pixel registration...
        # "-r", # Force pixel registration since data points are at centre of cells.
        "-Rg",
        "-G{0}".format(grid_filename)]
    
    # Call the system command.
    pybacktrack.util.call_system_command.call_system_command(nearneighbor_command_line, stdin=input_data)


def _read_topological_model(
        model_name):
    """
    Create a topological model given a file listing topological files and another file listing rotation files.

    The list filenames are "<model_name>_topology_files.txt" and "<model_name>_rotation_files.txt" (in the "deforming_model/" directory).
    
    Returns a pygplates.TopologicalModel (requires pyGPlates revision 30 or above).
    """
    
    deforming_model_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'deforming_model')

    topology_files_list_filename = os.path.join(deforming_model_path, '{0}_topology_files.txt'.format(model_name))
    with open(topology_files_list_filename, 'r') as topology_files_list_file:
        topology_filenames = [os.path.join(deforming_model_path, filename)
                for filename in topology_files_list_file.read().splitlines()]

    rotation_files_list_filename = os.path.join(deforming_model_path, '{0}_rotation_files.txt'.format(model_name))
    with open(rotation_files_list_filename, 'r') as rotation_files_list_file:
        rotation_filenames = [os.path.join(deforming_model_path, filename)
                for filename in rotation_files_list_file.read().splitlines()]

    return pygplates.TopologicalModel(topology_filenames, rotation_filenames)


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


if __name__ == '__main__':
    
    ########################
    # Command-line parsing #
    ########################
    
    import argparse
    
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
    
    
    def main():
        
        __description__ = """Create rift start and end time grids from a deforming plate model.
    
    NOTE: Separate the positional and optional arguments with '--' (workaround for bug in argparse module).
    For example...

    python generate_rift_grids.py ... --use_all_cpus -g 0.2 -- rift_start_grid.nc rift_end_grid.nc
    """
    
        #
        # Gather command-line options.
        #
        
        # The command-line parser.
        parser = argparse.ArgumentParser(description=__description__, formatter_class=argparse.RawDescriptionHelpFormatter)
            
        grid_spacing_argument_group = parser.add_mutually_exclusive_group()
        grid_spacing_argument_group.add_argument('-g', '--grid_spacing_degrees', type=float,
                help='The grid spacing (in degrees) of generate points in lon/lat space. '
                    'Defaults to {0} degrees.'.format(DEFAULT_GRID_SPACING_DEGREES))
        grid_spacing_argument_group.add_argument('-gm', '--grid_spacing_minutes', type=float,
                help='The grid spacing (in minutes) of generate points in lon/lat space. '
                    'Defaults to {0} minutes.'.format(DEFAULT_GRID_SPACING_MINUTES))
        
        # Allow user to override default total sediment thickness filename (if they don't want the one in the bundled data).
        parser.add_argument(
            '-s', '--total_sediment_thickness_filename', type=argparse_unicode,
            default=pybacktrack.bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,
            metavar='total_sediment_thickness_filename',
            help='Optional filename used to obtain total sediment thickness grid. '
                    'Defaults to the bundled data file "{0}".'.format(pybacktrack.bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME))
        
        # Allow user to override default age grid filename (if they don't want the one in the bundled data).
        parser.add_argument(
            '-a', '--age_grid_filename', type=argparse_unicode,
            default=pybacktrack.bundle_data.BUNDLE_AGE_GRID_FILENAME,
            metavar='age_grid_filename',
            help='Optional age grid filename used to distinguish between continental and oceanic crust. '
                'Crust is oceanic at locations inside masked age grid region, and continental outside. '
                'Defaults to the bundled data file "{0}".'.format(pybacktrack.bundle_data.BUNDLE_AGE_GRID_FILENAME))
        
        parser.add_argument(
            '--use_all_cpus', action='store_true',
            help='Use all CPUs (cores). Defaults to using a single CPU.')
        
        parser.add_argument(
            'rift_start_time_grid_filename', type=argparse_unicode,
            metavar='rift_start_time_grid_filename',
            help='The output grid filename containing rift start times.')
        
        parser.add_argument(
            'rift_end_time_grid_filename', type=argparse_unicode,
            metavar='rift_end_time_grid_filename',
            help='The output grid filename containing rift end times.')
        
        parser.add_argument(
            'rift_beta_grid_filename', type=argparse_unicode,
            metavar='rift_beta_grid_filename',
            help='The output grid filename containing rift betas (crustal stretching factors).')
        
        # Parse command-line options.
        args = parser.parse_args()
            
        #
        # Do any necessary post-processing/validation of parsed options.
        #
        if args.grid_spacing_degrees is not None:
            grid_spacing_degrees = args.grid_spacing_degrees
        elif args.grid_spacing_minutes is not None:
            grid_spacing_degrees = args.grid_spacing_minutes / 60.0
        else:
            grid_spacing_degrees = DEFAULT_GRID_SPACING_DEGREES
    
        # Generate a global latitude/longitude grid of points (with the requested grid spacing).
        input_points = generate_input_points_grid(grid_spacing_degrees)
        
        # Generate rift parameter points (at non-NaN grid sample locations in total sediment thickness grid).
        rift_parameter_points = generate_rift_parameter_points(
                input_points,
                args.total_sediment_thickness_filename,
                args.age_grid_filename,
                args.use_all_cpus)
        
        # Separate the combined rift parameters list into a separate list for each parameter.
        rift_start_points = []
        rift_end_points = []
        rift_beta_points = []
        for lon, lat, rift_start_time, rift_end_time, rift_beta in rift_parameter_points:
            rift_start_points.append((lon, lat, rift_start_time))
            rift_end_points.append((lon, lat, rift_end_time))
            rift_beta_points.append((lon, lat, rift_beta))

        # Create the rift parameter grids.
        #print ('Writing rift start/end/beta grids...')
        _gmt_nearneighbor(rift_start_points, grid_spacing_degrees, args.rift_start_time_grid_filename)
        _gmt_nearneighbor(rift_end_points, grid_spacing_degrees, args.rift_end_time_grid_filename)
        _gmt_nearneighbor(rift_beta_points, grid_spacing_degrees, args.rift_beta_grid_filename)
        
        sys.exit(0)
    
    import traceback
    
    try:
        main()
        sys.exit(0)
    except Exception as exc:
        print('ERROR: {0}'.format(exc), file=sys.stderr)
        # Uncomment this to print traceback to location of raised exception.
        #traceback.print_exc()
        sys.exit(1)

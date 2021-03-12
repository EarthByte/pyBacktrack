
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

# Default output grid filenames for rift start and end times.
DEFAULT_RIFT_START_TIME_GRID_FILENAME = 'rift_start_grid.nc'
DEFAULT_RIFT_END_TIME_GRID_FILENAME = 'rift_end_grid.nc'


def find_rift_start_end_times(
        total_sediment_thickness_filename,
        age_grid_filename,
        rift_start_time_grid_filename,
        rift_end_time_grid_filename):
    """Generate rift start/end times for each non-NaN grid sample in total sediment thickness grid.
    """
    
    # Check the imported pygplates version.
    if pygplates.Version.get_imported_version() < PYGPLATES_VERSION_REQUIRED:
        raise RuntimeError('Using pygplates version {0} but version {1} or greater is required'.format(
                pygplates.Version.get_imported_version(), PYGPLATES_VERSION_REQUIRED))
    
    # Read the total sediment thickness grid file and gather a list of non-NaN grid locations (ie, (longitude, latitude) tuples).
    #print ('Reading sediment points...')
    sediment_points = [(sample[0], sample[1]) for sample in _grd2xyz(total_sediment_thickness_filename) if not math.isnan(sample[2])]

    # Read the age grid file (at sediment locations) and only include those that have NaN values (representing non-oceanic points).
    #print ('Reading continent sediment points...')
    continent_sediment_points = [(sample[0], sample[1]) for sample in _grdtrack(sediment_points, age_grid_filename) if math.isnan(sample[2])]
    num_continent_sediment_points = len(continent_sediment_points)

    # Number of CPUs for our multiprocessing pool.
    try:
        num_cpus = multiprocessing.cpu_count()
    except NotImplementedError:
        num_cpus = 1
    
    # Divide the points into a number of groups equal to twice the number of CPUs in case some groups of points take longer to process than others.
    num_continent_sediment_point_groups = 2 * num_cpus
    num_continent_sediment_point_per_group = math.ceil(float(num_continent_sediment_points) / num_continent_sediment_point_groups)

    # Distribute the groups of points across the multiprocessing pool.
    #print ('Reconstructing', num_continent_sediment_points, 'continent sediment points...')
    with multiprocessing.Pool(num_cpus) as pool:
        continent_sediment_rift_start_end_point_lists = pool.map(
                find_continent_sediment_rift_start_end_times,
                (
                    continent_sediment_points[
                        continent_sediment_point_group_index * num_continent_sediment_point_per_group :
                        (continent_sediment_point_group_index + 1) * num_continent_sediment_point_per_group]
                                for continent_sediment_point_group_index in range(num_continent_sediment_point_groups)
                ),
                1) # chunksize
    
    # Combine the processed groups of points into a single rift start (and end) time list.
    continent_sediment_rift_start_points = []
    continent_sediment_rift_end_points = []
    for continent_sediment_rift_start_end_point_list in continent_sediment_rift_start_end_point_lists:
        # Separate rift start/end list into separate start and end lists (for separate start and end grids).
        for lon, lat, rift_start_time, rift_end_time in continent_sediment_rift_start_end_point_list:
            continent_sediment_rift_start_points.append((lon, lat, rift_start_time))
            continent_sediment_rift_end_points.append((lon, lat, rift_end_time))

    # Create the rift start and end time grids.
    #print ('Writing rift start/end grids...')
    _xyz2grd(continent_sediment_rift_start_points, rift_start_time_grid_filename)
    _xyz2grd(continent_sediment_rift_end_points, rift_end_time_grid_filename)


def find_continent_sediment_rift_start_end_times(
        initial_points):
    """Find rift start/end times for each continent-sediment input point that undergoes rift deformation.

    Returns a list of 4-tuples (lon, lat, rift_start_time, rift_end_time).
    """

    # Load the deforming (topological) model.
    topological_model = _read_topological_model(DEFORMING_MODEL_NAME)

    num_continent_sediment_points = len(initial_points)

    rift_start_times = [None] * num_continent_sediment_points
    rift_end_times = [None] * num_continent_sediment_points
    
    # We start with initial points and reconstruct them through multiple time intervals.
    # At each time interval some points find their rift start/end times and are removed from these lists.
    reconstructed_points = [pygplates.PointOnSphere(lat, lon) for lon, lat in initial_points]
    reconstructed_point_indices = list(range(num_continent_sediment_points))
    reconstructed_crustal_stretching_factors = [1.0] * num_continent_sediment_points
    
    continent_sediment_rift_start_end_points = []

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
                        # Stretching factor is initial thickness over current thickness. And since initial thickness is at present day,
                        # crust that is stretching forward in time is actually thickening backward in time. And thickening means a
                        # stretching factor less than 1.0.
                        if crustal_stretching_factors[reconstructed_point_index] < 1.0:
                            rift_start_times[point_index] = time
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
        if (rift_start_time is not None and
            rift_end_time is not None):
            initial_point = initial_points[point_index]
            continent_sediment_rift_start_end_points.append(
                    (initial_point[0], initial_point[1], rift_start_time, rift_end_time))

    return continent_sediment_rift_start_end_points


def _grd2xyz(
        grid_filename):
    """
    Run 'gmt grd2xyz' on a grid file and return grid locations/values.
    
    Returns a list of (longitude, latitude, grid_value) tuples.
    """

    # The command-line strings to execute GMT 'grd2xyz'.
    grd2xyz_command_line = ["gmt", "grd2xyz", "-s", grid_filename]
    
    # Call the system command.
    stdout_data = pybacktrack.util.call_system_command.call_system_command(grd2xyz_command_line, return_stdout=True)

    # Extract the sampled values.
    output_values = []
    for line in stdout_data.splitlines():
        # Each line returned by GMT grd2xyz contains "longitude latitude grid_value".
        output_value = tuple(float(value) for value in line.split())
        output_values.append(output_value)
    
    return output_values


def _xyz2grd(
        input,
        grid_filename):
    """
    Run 'gmt xyz2grd' on grid locations/values to output a grid file.
    """
    
    # Create a multiline string (one line per lon/lat/value1/etc row).
    location_data = ''.join(
            ' '.join(str(item) for item in row) + '\n' for row in input)

    # The command-line strings to execute GMT 'xyz2grd'.
    xyz2grd_command_line = ["gmt", "xyz2grd", "-Rg", "-I5m"]
    xyz2grd_command_line.append("-G{0}".format(grid_filename))
    
    # Call the system command.
    pybacktrack.util.call_system_command.call_system_command(xyz2grd_command_line, stdin=location_data)


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
    stdout_data = pybacktrack.util.call_system_command.call_system_command(grdtrack_command_line, stdin=location_data, return_stdout=True)

    # Extract the sampled values.
    output_values = []
    for line in stdout_data.splitlines():
        # Each line returned by GMT grdtrack contains "longitude latitude grid1_value [grid2_value ...]".
        # Note that if GMT returns "NaN" then we'll return float('nan').
        output_value = tuple(float(value) for value in line.split())
        output_values.append(output_value)
    
    return output_values


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
    """
    
        #
        # Gather command-line options.
        #
        
        # The command-line parser.
        parser = argparse.ArgumentParser(description=__description__, formatter_class=argparse.RawDescriptionHelpFormatter)
        
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
            '--rift_start_time_grid_filename', type=argparse_unicode,
            default=DEFAULT_RIFT_START_TIME_GRID_FILENAME,
            metavar='rift_start_time_grid_filename',
            help='The output grid filename containing rift start times. '
                'Defaults to "{0}".'.format(DEFAULT_RIFT_START_TIME_GRID_FILENAME))
        
        parser.add_argument(
            '--rift_end_time_grid_filename', type=argparse_unicode,
            default=DEFAULT_RIFT_END_TIME_GRID_FILENAME,
            metavar='rift_end_time_grid_filename',
            help='The output grid filename containing rift end times. '
                'Defaults to "{0}".'.format(DEFAULT_RIFT_END_TIME_GRID_FILENAME))
        
        # Parse command-line options.
        args = parser.parse_args()
        
        # Generate rift start/end times for each non-NaN grid sample in total sediment thickness grid.
        find_rift_start_end_times(
                args.total_sediment_thickness_filename,
                args.age_grid_filename,
                args.rift_start_time_grid_filename,
                args.rift_end_time_grid_filename)
        
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

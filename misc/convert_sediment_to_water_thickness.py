
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
import os.path
import pybacktrack
import sys


# Parameters of “average ocean floor sediment” lithology.
AVERAGE_OCEAN_FLOOR_SEDIMENT_SURFACE_POROSITY = 0.66
AVERAGE_OCEAN_FLOOR_SEDIMENT_POROSITY_DECAY = 1333


def convert_sediment_to_water(
        input_points,
        total_sediment_thickness_filename):
    """Convert sediment thickness into water thickness based on porosity assuming a single “average ocean floor sediment” lithology.

    Returns a list of tuples (longitude, latitude, water_thickness)
    """

    # Read the total sediment thickness grid file and remove NaN grid locations.
    #print ('Reading sediment points...')
    sediment_points = [sample for sample in _gmt_grdtrack(input_points, total_sediment_thickness_filename) if not math.isnan(sample[2])]

    water_points = []
    for longitude, latitude, sediment_thickness in sediment_points:
        #
        # Assuming the porosity decays exponentially, the volume of water within sediment of thickness 'T' is:
        #
        #    Integral(porosity(z), z = 0 -> 0 + T) = Integral(porosity(0) * exp(-z / decay), z = 0 -> 0 + T)
        #                                          = -decay * porosity(0) * (exp(-T/decay) - 1)
        #                                          = decay * porosity(0) * (1 - exp(-T/decay))
        #
        water_thickness = AVERAGE_OCEAN_FLOOR_SEDIMENT_POROSITY_DECAY * AVERAGE_OCEAN_FLOOR_SEDIMENT_SURFACE_POROSITY * (
                          1 - math.exp(-sediment_thickness / AVERAGE_OCEAN_FLOOR_SEDIMENT_POROSITY_DECAY))
        water_points.append((longitude, latitude, water_thickness))
    
    return water_points


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
    grdtrack_command_line = ["gmt", "grdtrack",
        # Geographic input/output coordinates...
        "-fg",
        # Use linear interpolation, and avoid anti-aliasing...
        "-nl+a+bg+t0.5"]
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
        "-fg",
        "-G{0}".format(grid_filename)]
    
    # Call the system command.
    pybacktrack.util.call_system_command.call_system_command(nearneighbor_command_line, stdin=input_data)


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
        
        __description__ = """Convert sediment thickness into water thickness based on porosity assuming a single “average ocean floor sediment” lithology.
    
    NOTE: Separate the positional and optional arguments with '--' (workaround for bug in argparse module).
    For example...

    python -gm 12 -- convert_sediment_to_water_thickness.py sediment_thickness.nc water_thickness.nc
    """
    
        #
        # Gather command-line options.
        #
        
        # The command-line parser.
        parser = argparse.ArgumentParser(description=__description__, formatter_class=argparse.RawDescriptionHelpFormatter)
            
        grid_spacing_argument_group = parser.add_mutually_exclusive_group(required=True)
        grid_spacing_argument_group.add_argument('-g', '--grid_spacing_degrees', type=float,
                help='The grid spacing (in degrees) of generate points in lon/lat space.')
        grid_spacing_argument_group.add_argument('-gm', '--grid_spacing_minutes', type=float,
                help='The grid spacing (in minutes) of generate points in lon/lat space.')
        
        parser.add_argument(
            'total_sediment_thickness_filename', type=argparse_unicode,
            metavar='total_sediment_thickness_filename',
            help='The total sediment thickness grid.')
        
        parser.add_argument(
            'water_thickness_grid_filename', type=argparse_unicode,
            metavar='water_thickness_grid_filename',
            help='The water thickness grid.')
        
        # Parse command-line options.
        args = parser.parse_args()
        
        #
        # Do any necessary post-processing/validation of parsed options.
        #
        if args.grid_spacing_degrees is not None:
            grid_spacing_degrees = args.grid_spacing_degrees
        else:
            grid_spacing_degrees = args.grid_spacing_minutes / 60.0
    
        # Generate a global latitude/longitude grid of points (with the requested grid spacing).
        input_points = generate_input_points_grid(grid_spacing_degrees)
        
        # Convert sediment thickness to water thickness.
        water_points = convert_sediment_to_water(
                input_points,
                args.total_sediment_thickness_filename)

        # Write water thickness grid.
        _gmt_nearneighbor(water_points, grid_spacing_degrees, args.water_thickness_grid_filename)
        
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

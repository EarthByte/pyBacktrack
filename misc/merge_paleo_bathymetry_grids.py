from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from functools import partial
import math
import multiprocessing
import os
import os.path
import pybacktrack
import sys
try:
    import xarray
except ImportError:
    have_xarray = False
else:
    have_xarray = True

# PyBacktrack paleobathymetry grids.
paleo_bathymetry_pybacktrack_prefix = r'C:\Users\John\Development\Usyd\source_code\repositories\Earthbyte\pyBacktrack\misc\paleo_bathymetry_output\paleo_bathymetry_12m_M7_RHCW18'
paleo_bathymetry_pybacktrack_basename = 'paleo_bathymetry'
paleo_bathymetry_pybacktrack_extension = 'nc'
# Typically either 0 or 1.
paleo_bathymetry_pybacktrack_decimal_places_in_time = 1

# Wright paleobathymetry grids.
paleo_bathymetry_wright_prefix = r'C:\Users\John\Development\Usyd\source_code\repositories\Earthbyte\pyBacktrack\misc\paleo_bathymetry_Wright\Paleobathymetry_RHCW18'
paleo_bathymetry_wright_basename = 'paleobathymetry'
paleo_bathymetry_wright_extension = 'nc'
# Typically either 0 or 1.
paleo_bathymetry_wright_decimal_places_in_time = 0

# Optional dynamic topography model to add to Wright paleobathymetry grids (the pybacktrack grids already have it applied).
#
# Can be any builtin dynamic topography model *name* supported by pyBacktrack
# (see the list at https://pybacktrack.readthedocs.io/en/latest/pybacktrack_backtrack.html#dynamic-topography).
#
# Note: This can be 'None' if no dynamic topography need be applied.
#dynamic_topography_model_name = None
dynamic_topography_model_name = 'M7'

# How far back in time to generate grids.
max_time = 140
time_increment = 1
# For best results set this to the same as Wright grids (they are higher resolution at 0.1 degrees).
merged_grid_spacing_degrees = 0.2

# Merged grids.
merged_grid_directory = os.path.join('paleo_bathymetry_output', 'merged', 'paleo_bathymetry_{0:.0f}m_M7_RHCW18'.format(merged_grid_spacing_degrees * 60.0))  # Insert grid spacing (in minutes) in output directory.
merged_grid_basename = 'paleo_bathymetry'

# Use the Python xarray module (if installed) to load the bathymetry grids.
#
# This enables faster loading of the grids (compared to GMT grdtrack) but any
# interpolated location that has any NaN neighbours (in 4x4 linear region) will itself be NaN
# (whereas GMT grdtrack will interpolate halfway from a non-NaN value, using option "-n+t0.5").
use_xarray_if_available = False

# Use all CPUs (if True then make sure you don't interrupt the process).
#
# If False then use a single CPU.
# If True then use all CPUs (cores).
# If a positive integer then use that many CPUs (cores).
#
#use_all_cpus = True
use_all_cpus = 4


# Create the dynamic topography model (from model name) if requested.
if dynamic_topography_model_name:
    dynamic_topography_model = pybacktrack.InterpolateDynamicTopography.create_from_bundled_model(dynamic_topography_model_name)
else:
    dynamic_topography_model = None


def merge_paleo_bathymetry_grids(
        time,
        input_points,
        dynamic_topography_at_present_day):
    
    # print('Time: {}'.format(time)); sys.stdout.flush()

    # Paleo bathymetry grids to merge (pybacktrack and Wright).
    #
    # Note that pybacktrack uses 1 decimal place for the time in the filename, whereas Wright does not.
    paleo_bathymetry_pybacktrack_filename = os.path.join(
            paleo_bathymetry_pybacktrack_prefix,
            '{0}_{1:.{2}f}.{3}'.format(paleo_bathymetry_pybacktrack_basename, time, paleo_bathymetry_pybacktrack_decimal_places_in_time, paleo_bathymetry_pybacktrack_extension))
    paleo_bathymetry_wright_filename = os.path.join(
            paleo_bathymetry_wright_prefix,
            '{0}_{1:.{2}f}.{3}'.format(paleo_bathymetry_wright_basename, time, paleo_bathymetry_wright_decimal_places_in_time, paleo_bathymetry_wright_extension))

    # Sample the paleo bathymetry grids that we're going to merge.
    # print('Reading input bathymetry grids...'); sys.stdout.flush()
    paleo_bathymetry_points = _load_bathymetry(
            input_points,
            paleo_bathymetry_pybacktrack_filename,
            paleo_bathymetry_wright_filename)
    
    if dynamic_topography_model:
        # Sample the dynamic topography at 'time'.
        # print('Sample dynamic topography at {}...'.format(time)); sys.stdout.flush()
        dynamic_topography = dynamic_topography_model.sample(time, input_points)
    
    # print('Merging...'); sys.stdout.flush()
    merged_points = []
    for point_index, paleo_bathymetry_point in enumerate(paleo_bathymetry_points):
        lon, lat, paleo_bathymetry_pybacktrack, paleo_bathymetry_wright = paleo_bathymetry_point
        if math.isnan(paleo_bathymetry_pybacktrack) and math.isnan(paleo_bathymetry_wright):
            # Skip point if no paleo bathymetry from pybacktrack or Wright.
            continue
        
        # Prefer pybacktrack paleobathymetry.
        if not math.isnan(paleo_bathymetry_pybacktrack):
            paleo_bathymetry = paleo_bathymetry_pybacktrack
        else:
            # Note that pybacktrack generates paleobathymetry grids with negative values below sea level by default
            # (the opposite of backtracking which outputs positive depths below sea level).
            # And this matches the Wright paleobathymetry grids (which also have negative values below sea level),
            # so we don't need to negate them to match pybacktrack-generated paleobathymetry.
            paleo_bathymetry = paleo_bathymetry_wright
            # Also apply dynamic topography to Wright grids if requested (pybacktrack already has it applied).
            if dynamic_topography_model:
                # Dynamic topography, like bathymetry, is positive going up and negative going down so we can just add it to bathymetry.
                paleo_bathymetry += dynamic_topography[point_index] - dynamic_topography_at_present_day[point_index]

        merged_points.append((lon, lat, paleo_bathymetry))
    
    # print('Nearneighbor gridding...'); sys.stdout.flush()
    merged_grid_filename = os.path.join(merged_grid_directory, '{0}_{1}.nc'.format(merged_grid_basename, time))
    _gmt_nearneighbor(merged_points, merged_grid_spacing_degrees, merged_grid_filename)


def _load_bathymetry(
        input_points,
        paleo_bathymetry_pybacktrack_filename,
        paleo_bathymetry_wright_filename):
    
    if use_xarray_if_available and have_xarray:

        # The input point longitudes and latitudes.
        lons = xarray.DataArray([lon for lon, lat in input_points])
        lats = xarray.DataArray([lat for lon, lat in input_points])

        with xarray.open_dataset(paleo_bathymetry_pybacktrack_filename) as bathymetry_pybacktrack_grid:
            # Get the lon, lat coordinates names (typically 'lon' and 'lat', and in that order).
            coord_names = list(bathymetry_pybacktrack_grid.coords.keys())
            lon_name = coord_names[0]
            lat_name = coord_names[1]
            # Get the z value name (typically 'z').
            z_name = list(bathymetry_pybacktrack_grid.data_vars.keys())[0]
            # Interpolate the bathymetry grid at the input point locations.
            bathymetry_pybacktrack_values = bathymetry_pybacktrack_grid[z_name].interp(dict({lon_name : lons, lat_name : lats}))
            # print(bathymetry_pybacktrack_grid.keys())
            # print(bathymetry_pybacktrack_values.shape)

        with xarray.open_dataset(paleo_bathymetry_wright_filename) as bathymetry_wright_grid:
            # Get the lon, lat coordinates names (typically 'lon' and 'lat', and in that order).
            coord_names = list(bathymetry_wright_grid.coords.keys())
            lon_name = coord_names[0]
            lat_name = coord_names[1]
            # Get the z value name (typically 'z').
            z_name = list(bathymetry_wright_grid.data_vars.keys())[0]
            # Interpolate the bathymetry grid at the input point locations.
            bathymetry_wright_values = bathymetry_wright_grid[z_name].interp(dict({lon_name : lons, lat_name : lats}))
            # print(bathymetry_wright_grid.keys())
            # print(bathymetry_wright_values.shape)

        output_values = []

        for point_index in range(len(lons)):
            lon, lat = input_points[point_index]
            output_value = (lon, lat, float(bathymetry_pybacktrack_values.item(point_index)), float(bathymetry_wright_values.item(point_index)))
            output_values.append(output_value)
    
        return output_values

    else:  # Use GMT grdtrack ...

        # Create a multiline string (one line per lon/lat/value1/etc row).
        location_data = ''.join(
                ' '.join(str(item) for item in row) + '\n' for row in input_points)

        # The command-line strings to execute GMT 'grdtrack'.
        grdtrack_command_line = ["gmt", "grdtrack",
            # Geographic input/output coordinates...
            "-fg",
            # Avoid anti-aliasing...
            "-n+a+bg+t0.5"]
        # One or more grid filenames to sample.
        for grid_filename in (paleo_bathymetry_pybacktrack_filename, paleo_bathymetry_wright_filename):
            grdtrack_command_line.append("-G{0}".format(grid_filename))
        
        # Call the system command.
        stdout_data = pybacktrack.util.call_system_command.call_system_command(grdtrack_command_line, stdin=location_data, return_stdout=True)

        output_values = []

        # Extract the sampled values.
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
    
    # Create a multiline string (one line per lon/lat/value row).
    input_data = ''.join(
            ' '.join(str(item) for item in row) + '\n' for row in input)

    # The command-line strings to execute GMT 'nearneighbor'.
    nearneighbor_command_line = [
        "gmt",
        "nearneighbor",
        "-N1/1", # Divide search radius into 1 sector and only require a value in 1 sector.
        "-S{0}d".format(0.1 * grid_spacing_degrees),
        "-I{0}".format(grid_spacing_degrees),
        # Use GMT gridline registration since our input point grid has data points on the grid lines.
        # Gridline registration is the default so we don't need to force pixel registration...
        # "-r", # Force pixel registration since data points are at centre of cells.
        "-Rg",
        "-fg",
        "-G{0}".format(grid_filename)]
    
    # Call the system command.
    pybacktrack.util.call_system_command.call_system_command(nearneighbor_command_line, stdin=input_data)


def _generate_input_points_grid(grid_spacing_degrees):
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
            # NOTE: For some reason xarray does not always like the range [-180, 180] (excludes half the globe).
            #       So use the range [0, 360] instead.
            lon = 0 + lon_index * grid_spacing_degrees
            
            input_points.append((lon, lat))
    
    return input_points


if __name__ == '__main__':
    
    # Make sure directory of merged grid files exists.
    if not os.path.exists(merged_grid_directory):
        os.makedirs(merged_grid_directory)

    # Generate a global latitude/longitude grid of points (with the requested grid spacing).
    input_points = _generate_input_points_grid(merged_grid_spacing_degrees)

    if dynamic_topography_model:
        # Sample the dynamic topography at present day.
        # print('Sample dynamic topography at {}...'.format(0)); sys.stdout.flush()
        dynamic_topography_at_present_day = dynamic_topography_model.sample(0, input_points)
    else:
        dynamic_topography_at_present_day = None
    
    # Create times from present day to 'max_time'.
    time_range = range(0, max_time+1, time_increment)
    
    if use_all_cpus:

        # If 'use_all_cpus' is a bool (and therefore must be True) then use all available CPUs...
        if isinstance(use_all_cpus, bool):
            try:
                num_cpus = multiprocessing.cpu_count()
            except NotImplementedError:
                num_cpus = 1
        # else 'use_all_cpus' is a positive integer specifying the number of CPUs to use...
        elif isinstance(use_all_cpus, int) and use_all_cpus > 0:
            num_cpus = use_all_cpus
        else:
            raise TypeError('{} is neither a bool nor a positive integer'.format(use_all_cpus))

        # Distribute writing of each grid to a different CPU.
        with multiprocessing.Pool(num_cpus) as pool:
            pool.map(
                    partial(
                        merge_paleo_bathymetry_grids,
                        input_points=input_points,
                        dynamic_topography_at_present_day=dynamic_topography_at_present_day),
                    time_range,
                    1) # chunksize

    else:
        for time in time_range:
            merge_paleo_bathymetry_grids(
                    time,
                    input_points,
                    dynamic_topography_at_present_day)

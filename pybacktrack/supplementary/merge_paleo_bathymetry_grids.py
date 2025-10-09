from functools import partial
import math
import multiprocessing
import os
import os.path
import pybacktrack
import sys


def merge_paleo_bathymetry_grids(
        max_time,
        time_increment,
        paleo_bathymetry_pybacktrack_filename_format,  # filename generated using str.format(time)
        paleo_bathymetry_wright_filename_format,  # filename generated using str.format(time)
        merged_grid_filename_format,  # filename generated using str.format(time)
        merged_grid_spacing_degrees,
        dynamic_topography_model_or_bundled_model_name=None,
        # Use all CPUs (if not False then make sure you don't interrupt the process).
        #
        # If False then use a single CPU.
        # If True then use all CPUs (cores).
        # If a positive integer then use that many CPUs (cores).
        use_all_cpus=False):

    # Generate a global latitude/longitude grid of points (with the requested grid spacing).
    input_points = _generate_input_points_grid(merged_grid_spacing_degrees)

    # Create the dynamic topography model (from model name) if requested.
    if dynamic_topography_model_or_bundled_model_name:
        interpolate_dynamic_topography_model = pybacktrack.InterpolateDynamicTopography.create_from_model_or_bundled_model_name(dynamic_topography_model_or_bundled_model_name)
        # Sample the dynamic topography at present day.
        # print('Sample dynamic topography at {}...'.format(0)); sys.stdout.flush()
        dynamic_topography_at_present_day = interpolate_dynamic_topography_model.sample(0, input_points)
    else:
        interpolate_dynamic_topography_model = None
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
                        merge_paleo_bathymetry_grid,
                        input_points=input_points,
                        paleo_bathymetry_pybacktrack_filename_format=paleo_bathymetry_pybacktrack_filename_format,
                        paleo_bathymetry_wright_filename_format=paleo_bathymetry_wright_filename_format,
                        merged_grid_filename_format=merged_grid_filename_format,
                        merged_grid_spacing_degrees=merged_grid_spacing_degrees,
                        interpolate_dynamic_topography_model=interpolate_dynamic_topography_model,
                        dynamic_topography_at_present_day=dynamic_topography_at_present_day),
                    time_range,
                    1) # chunksize

    else:
        for time in time_range:
            merge_paleo_bathymetry_grid(
                    time,
                    input_points,
                    paleo_bathymetry_pybacktrack_filename_format,
                    paleo_bathymetry_wright_filename_format,
                    merged_grid_filename_format,
                    merged_grid_spacing_degrees,
                    interpolate_dynamic_topography_model,
                    dynamic_topography_at_present_day)


def merge_paleo_bathymetry_grid(
        time,
        input_points,
        paleo_bathymetry_pybacktrack_filename_format,  # filename generated using str.format(time)
        paleo_bathymetry_wright_filename_format,  # filename generated using str.format(time)
        merged_grid_filename_format,  # filename generated using str.format(time)
        merged_grid_spacing_degrees,
        interpolate_dynamic_topography_model,
        dynamic_topography_at_present_day):
    
    # print('Time: {}'.format(time)); sys.stdout.flush()

    # Paleo bathymetry grids to merge (pybacktrack and Wright).
    paleo_bathymetry_pybacktrack_filename = paleo_bathymetry_pybacktrack_filename_format.format(time)
    paleo_bathymetry_wright_filename = paleo_bathymetry_wright_filename_format.format(time)

    # Sample the paleo bathymetry grids that we're going to merge.
    # print('Reading input bathymetry grids...'); sys.stdout.flush()
    paleo_bathymetry_points = _load_bathymetry(
            input_points,
            paleo_bathymetry_pybacktrack_filename,
            paleo_bathymetry_wright_filename)
    
    if interpolate_dynamic_topography_model:
        # Sample the dynamic topography at 'time'.
        # print('Sample dynamic topography at {}...'.format(time)); sys.stdout.flush()
        dynamic_topography = interpolate_dynamic_topography_model.sample(time, input_points)
    
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
            if interpolate_dynamic_topography_model:
                # Dynamic topography, like bathymetry, is positive going up and negative going down so we can just add it to bathymetry.
                paleo_bathymetry += dynamic_topography[point_index] - dynamic_topography_at_present_day[point_index]

        merged_points.append((lon, lat, paleo_bathymetry))
    
    # print('Nearneighbor gridding...'); sys.stdout.flush()
    merged_grid_filename = merged_grid_filename_format.format(time)
    _gmt_nearneighbor(merged_points, merged_grid_spacing_degrees, merged_grid_filename)


def _load_bathymetry(
        input_points,
        paleo_bathymetry_pybacktrack_filename,
        paleo_bathymetry_wright_filename):

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
    
    # Make sure directory containing the output grid file exists.
    if not os.path.exists(os.path.dirname(grid_filename)):
        os.makedirs(os.path.dirname(grid_filename))
    
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
            lon = -180 + lon_index * grid_spacing_degrees
            
            input_points.append((lon, lat))
    
    return input_points


if __name__ == '__main__':

    # PyBacktrack paleobathymetry grid filename format (ie, str.format(time) is applied to this string for each 'time').
    paleo_bathymetry_pybacktrack_filename_format = os.path.join(
        r'C:\Users\jcann\Development\Usyd\source_code\repositories\Earthbyte\pyBacktrack\misc\paleo_bathymetry_output\paleo_bathymetry_12m_M7_RHCW18',
        'paleo_bathymetry_{:.1f}.nc')  # 'time' part of filename is 1 decimal place

    # Wright paleobathymetry grids filename format (ie, str.format(time) is applied to this string for each 'time').
    paleo_bathymetry_wright_filename_format = os.path.join(
        r'C:\Users\jcann\Development\Usyd\source_code\repositories\Earthbyte\pyBacktrack\misc\paleo_bathymetry_Wright\Paleobathymetry_RHCW18',
        'paleobathymetry_{:.0f}.nc')  # 'time' part of filename is 0 decimal places

    # How far back in time to generate grids.
    max_time = 140
    time_increment = 1

    # For best results set this to the same as Wright grids (they are higher resolution at 0.1 degrees).
    merged_grid_spacing_degrees = 0.5

    # Merged grid filename format (ie, str.format(time) is applied to this string for each 'time').
    merged_grid_filename_format = os.path.join(
        r'C:\Users\jcann\Development\Usyd\source_code\repositories\Earthbyte\pyBacktrack\misc\paleo_bathymetry_output\merged',
        # Insert grid spacing (in minutes) in output directory name...
        'paleo_bathymetry_{:.0f}m_M7_RHCW18'.format(merged_grid_spacing_degrees * 60.0),  # this is formatted now
        'paleo_bathymetry_{:.0f}.nc')  # this is formatted later (with 'time')

    # Use all CPUs (if True then make sure you don't interrupt the process).
    #
    # If False then use a single CPU.
    # If True then use all CPUs (cores).
    # If a positive integer then use that many CPUs (cores).
    #
    use_all_cpus = True

    # Optional dynamic topography model to add to Wright paleobathymetry grids (the pybacktrack grids already have it applied).
    #
    # Can be any builtin dynamic topography model *name* supported by pyBacktrack
    # (see the list at https://pybacktrack.readthedocs.io/en/latest/pybacktrack_backtrack.html#dynamic-topography).
    #
    # Note: This can be 'None' if no dynamic topography need be applied.
    #dynamic_topography_model_name = None
    dynamic_topography_model_name = 'M7'

    
    merge_paleo_bathymetry_grids(
        max_time,
        time_increment=time_increment,
        paleo_bathymetry_pybacktrack_filename_format=paleo_bathymetry_pybacktrack_filename_format,  # filename generated using str.format(time)
        paleo_bathymetry_wright_filename_format=paleo_bathymetry_wright_filename_format,  # filename generated using str.format(time)
        merged_grid_filename_format=merged_grid_filename_format,  # filename generated using str.format(time)
        merged_grid_spacing_degrees=merged_grid_spacing_degrees,
        dynamic_topography_model_or_bundled_model_name=dynamic_topography_model_name,
        use_all_cpus=use_all_cpus)

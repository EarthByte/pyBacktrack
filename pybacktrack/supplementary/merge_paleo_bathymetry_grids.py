from functools import partial
import multiprocessing
import os
import os.path
import pybacktrack


#
# Merge backtracked paleobathymetry grids with external paleobathymetry grids (on synthetic crust).
#
# NOTE: This script essentially just calls the pyBacktrack function 'pybacktrack.merge_paleo_bathymetry_grid()' (and optionally in parallel).
#       Previously that functionality was in this script, but it was moved to the main pyBacktrack package in pyBacktrack 1.5.
#
# Instead of using this script, you can simultaneously generate backtracked paleobathymetry (on present day crust) and merge it with
# external synthetic paleobathymetry using the pyBacktrack function 'pybacktrack.reconstruct_backtrack_bathymetry_and_write_grids()',
# or running the pyBacktrack script 'python -m pybacktrack.paleo_bathymetry_cli ...' and specifying the grids to merge.
#


def merge_paleo_bathymetry_grids(
        max_time,
        time_increment,
        paleo_bathymetry_pybacktrack_filename_format,  # filename generated using str.format(time)
        paleo_bathymetry_external_filename_format,  # filename generated using str.format(time)
        merged_grid_filename_format,  # filename generated using str.format(time)
        merged_grid_spacing_degrees,
        dynamic_topography_model_or_bundled_model_name=None,
        external_bathymetry_is_positive_below_sea_level=False,
        output_positive_bathymetry_below_sea_level=False,
        # Use all CPUs (if not False then make sure you don't interrupt the process).
        #
        # If False then use a single CPU.
        # If True then use all CPUs (cores).
        # If a positive integer then use that many CPUs (cores).
        use_all_cpus=False):
    
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
                        paleo_bathymetry_pybacktrack_filename_format=paleo_bathymetry_pybacktrack_filename_format,
                        paleo_bathymetry_external_filename_format=paleo_bathymetry_external_filename_format,
                        merged_grid_filename_format=merged_grid_filename_format,
                        merged_grid_spacing_degrees=merged_grid_spacing_degrees,
                        interpolate_dynamic_topography_model=dynamic_topography_model_or_bundled_model_name,
                        external_bathymetry_is_positive_below_sea_level=external_bathymetry_is_positive_below_sea_level,
                        output_positive_bathymetry_below_sea_level=output_positive_bathymetry_below_sea_level),
                    time_range,
                    1) # chunksize

    else:
        for time in time_range:
            merge_paleo_bathymetry_grid(
                    time,
                    paleo_bathymetry_pybacktrack_filename_format=paleo_bathymetry_pybacktrack_filename_format,
                    paleo_bathymetry_external_filename_format=paleo_bathymetry_external_filename_format,
                    merged_grid_filename_format=merged_grid_filename_format,
                    merged_grid_spacing_degrees=merged_grid_spacing_degrees,
                    interpolate_dynamic_topography_model=dynamic_topography_model_or_bundled_model_name,
                    external_bathymetry_is_positive_below_sea_level=external_bathymetry_is_positive_below_sea_level,
                    output_positive_bathymetry_below_sea_level=output_positive_bathymetry_below_sea_level)


def merge_paleo_bathymetry_grid(
        time,
        paleo_bathymetry_pybacktrack_filename_format,  # filename generated using str.format(time)
        paleo_bathymetry_external_filename_format,  # filename generated using str.format(time)
        merged_grid_filename_format,  # filename generated using str.format(time)
        merged_grid_spacing_degrees,
        interpolate_dynamic_topography_model,
        external_bathymetry_is_positive_below_sea_level,
        output_positive_bathymetry_below_sea_level):
    
    pybacktrack.merge_paleo_bathymetry_grid(
        time,
        grid_spacing_degrees=merged_grid_spacing_degrees,
        output_filename=merged_grid_filename_format.format(time),
        backtracked_paleo_bathymetry_filename=paleo_bathymetry_pybacktrack_filename_format.format(time),
        external_paleo_bathymetry_filename=paleo_bathymetry_external_filename_format.format(time),
        interpolate_dynamic_topography_model=interpolate_dynamic_topography_model,
        external_bathymetry_is_positive_below_sea_level=external_bathymetry_is_positive_below_sea_level,
        output_positive_bathymetry_below_sea_level=output_positive_bathymetry_below_sea_level,
        output_xyz=False)


if __name__ == '__main__':

    # PyBacktrack paleobathymetry grid filename format (ie, str.format(time) is applied to this string for each 'time').
    paleo_bathymetry_pybacktrack_filename_format = os.path.join(
        r'C:\Users\jcann\Development\Usyd\source_code\repositories\Earthbyte\pyBacktrack\misc\paleo_bathymetry_output\paleo_bathymetry_12m_M7_RHCW18',
        'paleo_bathymetry_{:.1f}.nc')  # 'time' part of filename is 1 decimal place

    # Wright paleobathymetry grids filename format (ie, str.format(time) is applied to this string for each 'time').
    paleo_bathymetry_external_filename_format = os.path.join(
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

    # Optional dynamic topography model to add to external paleobathymetry grids (the pybacktrack grids already have it applied).
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
        paleo_bathymetry_external_filename_format=paleo_bathymetry_external_filename_format,  # filename generated using str.format(time)
        merged_grid_filename_format=merged_grid_filename_format,  # filename generated using str.format(time)
        merged_grid_spacing_degrees=merged_grid_spacing_degrees,
        dynamic_topography_model_or_bundled_model_name=dynamic_topography_model_name,
        external_bathymetry_is_positive_below_sea_level=False,
        output_positive_bathymetry_below_sea_level=False,
        use_all_cpus=use_all_cpus)

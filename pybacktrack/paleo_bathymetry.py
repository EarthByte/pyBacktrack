
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

:func:`pybacktrack.reconstruct_paleo_bathymetry` reconstructs and backtracks sediment-covered crust through time to get paleo bathymetry.

:func:`pybacktrack.generate_lon_lat_points` generates a global grid of points uniformly spaced in longitude and latitude.

:func:`pybacktrack.write_paleo_bathymetry_grids` grid paleo bathymetry into NetCDF grids files.

:func:`pybacktrack.reconstruct_paleo_bathymetry_grids` generates a global grid of points, reconstructs/backtracks their bathymetry and writes paleo bathymetry grids.
"""


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from functools import partial
import itertools
import math
import multiprocessing
import numpy as np
import os
import os.path
import pybacktrack.age_to_depth as age_to_depth
import pybacktrack.bundle_data
from pybacktrack.dynamic_topography import DynamicTopography
from pybacktrack.lithology import read_lithologies_files
import pybacktrack.rifting as rifting
from pybacktrack.sea_level import SeaLevel
from pybacktrack.util.call_system_command import call_system_command
import pybacktrack.version
from pybacktrack.well import Well
import pygplates
import sys
import warnings


# Default name of the lithology of all sediment (the total sediment thickness at all sediment locations
# consists of a single lithology). This lithology is the average of the ocean floor sediment.
# This differs from the base lithology of drill sites where the undrilled portions are usually
# below the CCD where shale dominates.
DEFAULT_LITHOLOGY_NAME = 'Average_ocean_floor_sediment'

# Default grid spacing (in degrees) when generating uniform lon/lat spacing of sample points.
DEFAULT_GRID_SPACING_DEGREES = 1.0
DEFAULT_GRID_SPACING_MINUTES = 60.0 * DEFAULT_GRID_SPACING_DEGREES

# Ignore locations where the rifting stretching factor (beta) estimate results in a
# tectonic subsidence inaccuracy (at present day) exceeding this amount (in metres)...
#
# Note: We make this smaller to in the 'backtrack' module since the error is usually quite small (< 1.0)
#       and anything larger usually means the optimization (to find a beta that matches present day subsidence)
#       is getting too large and consequently pre-rift crustal thickness too close to the lithospheric thickness.
_MAX_TECTONIC_SUBSIDENCE_RIFTING_RESIDUAL_ERROR = 10.0

# There's a static polygon (from the static polygons file) in the W Pacific that is stationary through time.
# This is because the age grid determines the age on oceanic crust (static polygons only determine plate ID) and
# in this region the age grid suffers from an interpolation artefact (in the age grid generation process) where it
# should have ages around ~33 Ma but is actually 100+ Ma due to interpolation with the nearby older Pacific crust.
#
# So until the age grid is fixed (and it is hard to fix these types of age grid errors) we will use the static polygon
# appearance age in place of the age grid age whenever the latter is older than the former by the following amount (in Myr).
#
# Nicky tested a range of values between 30 and 60 Myr and found 40 Myr was the best:
# - 30 Myr was problematic for the larger static polygons in the Atlantic because they include a large range of age grid values (ie, greater than 30 Myr).
# - 60 Myr avoids issues in the Atlantic but doesn't remove enough of the W Pacific polygon.
# - 40 Myr removes most of it (a small sliver remains) without creating issues in the Atlantic.
_MAX_AGE_GRID_ALLOWED_TO_EXCEED_OCEANIC_STATIC_POLYGON_AGE = 40.0


def reconstruct_backtrack_bathymetry(
        input_points,  # note: you can use 'generate_input_points_grid()' to generate a global lat/lon grid
        oldest_time=None,
        time_increment=1,
        lithology_filenames=[pybacktrack.bundle_data.DEFAULT_BUNDLE_LITHOLOGY_FILENAME],
        age_grid_filename=pybacktrack.bundle_data.BUNDLE_AGE_GRID_FILENAME,
        topography_filename=pybacktrack.bundle_data.BUNDLE_TOPOGRAPHY_FILENAME,
        total_sediment_thickness_filename=pybacktrack.bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,
        crustal_thickness_filename=pybacktrack.bundle_data.BUNDLE_CRUSTAL_THICKNESS_FILENAME,
        rotation_filenames=pybacktrack.bundle_data.BUNDLE_RECONSTRUCTION_ROTATION_FILENAMES,
        static_polygon_filename=pybacktrack.bundle_data.BUNDLE_RECONSTRUCTION_STATIC_POLYGON_FILENAME,
        dynamic_topography_model=None,
        sea_level_model=None,
        lithology_name=DEFAULT_LITHOLOGY_NAME,
        ocean_age_to_depth_model=age_to_depth.DEFAULT_MODEL,
        exclude_distances_to_trenches_kms=None,
        region_plate_ids=None,
        anchor_plate_id=0,
        output_positive_bathymetry_below_sea_level=False,
        use_all_cpus=False):
    # Adding function signature on first line of docstring otherwise Sphinx autodoc will print out
    # the expanded values of the bundle filenames.
    """reconstruct_paleo_bathymetry(\
        input_points,\
        oldest_time=None,\
        time_increment=1,\
        lithology_filenames=[pybacktrack.DEFAULT_BUNDLE_LITHOLOGY_FILENAME],\
        age_grid_filename=pybacktrack.BUNDLE_AGE_GRID_FILENAME,\
        topography_filename=pybacktrack.BUNDLE_TOPOGRAPHY_FILENAME,\
        total_sediment_thickness_filename=pybacktrack.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,\
        crustal_thickness_filename=pybacktrack.BUNDLE_CRUSTAL_THICKNESS_FILENAME,\
        rotation_filenames=pybacktrack.bundle_data.BUNDLE_RECONSTRUCTION_ROTATION_FILENAMES,\
        static_polygon_filename=pybacktrack.bundle_data.BUNDLE_RECONSTRUCTION_STATIC_POLYGON_FILENAME,\
        dynamic_topography_model=None,\
        sea_level_model=None,\
        lithology_name=pybacktrack.DEFAULT_PALEO_BATHYMETRY_LITHOLOGY_NAME,\
        ocean_age_to_depth_model=pybacktrack.AGE_TO_DEPTH_DEFAULT_MODEL,\
        exclude_distances_to_trenches_kms=None,\
        region_plate_ids=None,\
        anchor_plate_id=0,\
        output_positive_bathymetry_below_sea_level=False,\
        use_all_cpus=False)
    Reconstructs and backtracks sediment-covered crust through time to get paleo bathymetry.
    
    Parameters
    ----------
    input_points : sequence of (longitude, latitude) tuples
        The point locations to sample bathymetry at present day.
        Note that any samples outside the masked region of the total sediment thickness grid are ignored.
    oldest_time : float, optional
        The oldest time (in Ma) that output is generated back to (from present day). Value must not be negative.
        If not specified then the oldest of oceanic crustal ages (for those input points on oceanic crust) and rift start ages
        (for those input points on continental crust) is used instead.
    time_increment: float
        The time increment (in My) that output is generated (from present day back to oldest time). Value must be positive.
    lithology_filenames : list of string, optional
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
    rotation_filenames : list of string, optional
        List of filenames containing rotation features (to reconstruct sediment-deposited crust).
        If not specified then defaults to the built-in global rotations associated with the topological model
        used to generate the built-in rift start/end time grids.
    static_polygon_filename : string, optional
        Filename containing static polygon features (to assign plate IDs to points on sediment-deposited crust).
        If not specified then defaults to the built-in static polygons associated with the topological model
        used to generate the built-in rift start/end time grids.
    dynamic_topography_model : string or tuple, optional
        Represents a time-dependent dynamic topography raster grid (in *mantle* frame).
        
        Can be either:
        
        * A string containing the name of a bundled dynamic topography model.
        
          Choices include ``terra``, ``M1``, ``M2``, ``M3``, ``M4``, ``M5``, ``M6``, ``M7``, ``ngrand``, ``s20rts``, ``smean``, ``AY18``, ``KM16``, ``D10_gmcm9`` and ``gld428``.
        * A tuple containing the three elements (dynamic topography list filename, static polygon filename, rotation filenames).
        
          The first tuple element is the filename of file containing list of dynamic topography grids (and associated times).
          Each row in this list file should contain two columns.
          First column containing filename (relative to list file) of a dynamic topography grid at a particular time.
          Second column containing associated time (in Ma).
          The second tuple element is the filename of file containing static polygons associated with dynamic topography model.
          This is used to assign plate ID to a location so it can be reconstructed.
          The third tuple element is the filename of the rotation file associated with model.
          Only the rotation file for static continents/oceans is needed (ie, deformation rotations not needed).
        
    sea_level_model : string, optional
        Used to obtain sea levels relative to present day.
        Can be either the name of a bundled sea level model, or a sea level filename.
        Bundled sea level models include ``Haq87_SealevelCurve`` and ``Haq87_SealevelCurve_Longterm``.
    lithology_name : string, optional
        Lithology name of the all sediment (must be present in lithologies file).
        The total sediment thickness at all sediment locations consists of a single lithology.
        Defaults to ``Average_ocean_floor_sediment``.
    ocean_age_to_depth_model : {pybacktrack.AGE_TO_DEPTH_MODEL_RHCW18, pybacktrack.AGE_TO_DEPTH_MODEL_CROSBY_2007, pybacktrack.AGE_TO_DEPTH_MODEL_GDH1} or function, optional
        The model to use when converting ocean age to depth at a location
        (if on ocean floor - not used for continental passive margin).
        It can be one of the enumerated values, or a callable function accepting a single non-negative age parameter and returning depth (in metres).
    exclude_distances_to_trenches_kms : 2-tuple of float, optional
        The two distances to present-day trenches (on subducting and overriding sides, in that order) to exclude bathymetry grid points (in kms), or
        None to use built-in per-trench defaults. Default is None.
    region_plate_ids : list of int, optional
        Plate IDs of one or more plates to restrict paleobathymetry reconstruction to.
        Defaults to global.
    anchor_plate_id : int, optional
        The anchor plate id used when reconstructing paleobathymetry grid points. Defaults to zero.
    output_positive_bathymetry_below_sea_level : bool, optional
        Whether to output positive bathymetry values below sea level (the same as backtracked water depths at a drill site).
        However topography/bathymetry grids typically have negative values below sea level (and positive above).
        So the default (``False``) matches typical topography/bathymetry grids (ie, outputs negative bathymetry values below sea level).
    use_all_cpus : bool or int, optional
        If ``False`` (or zero) then use a single CPU.
        If ``True`` then distribute CPU processing across all CPUs (cores).
        If a positive integer then use that many CPUs (cores).
        Defaults to ``False`` (single CPU).
    
    Returns
    -------
    dict mapping each time to a list of 3-tuple (longitude, latitude, bathymetry)
        The reconstructed paleo bathymetry points from present day to the oldest time (see ``oldest_time``) in increments of ``time_increment``.
        Each key in the returned dict is one of those times and each value in the dict is a list of reconstructed paleo bathymetries
        represented as a 3-tuple containing reconstructed longitude, reconstructed latitude and paleo bathmetry.
    
    Raises
    ------
    ValueError
        If ``oldest_time`` is negative (if specified) or if ``time_increment`` is not positive.

    Notes
    -----
    The output paleo bathymetry values are negative below sea level by default.
    Note that this is the inverse of water depth (which is positive below sea level).

    Any input points outside the masked region of the total sediment thickness grid are ignored (since bathymetry relies on sediment decompaction over time).
        
    .. versionadded:: 1.4

    .. versionchanged:: 1.5
        ``oldest_time`` no longer needs to be specified (defaults to oldest of ocean crust ages and continental rift start ages of input points).
    """
   
    #
    # Determine number of CPUs to use.
    #
    if use_all_cpus:
        # If 'use_all_cpus' is a bool (and therefore is True) then use all available CPUs...
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
    else:
        num_cpus = 1
    
    if (oldest_time is not None and
        oldest_time < 0):
        raise ValueError("'oldest_time' should not be negative")
    if time_increment <= 0:
        raise ValueError("'time_increment' should be positive")
    
    # Read the lithologies from one or more text files.
    #
    # Read all the lithology files and merge their dicts.
    # Subsequently specified files override previous files in the list.
    # So if the first and second files have the same lithology then the second lithology is used.
    lithologies = read_lithologies_files(lithology_filenames)

    # All sediment is represented as a single lithology (of total sediment thickness).
    lithology_components = [(lithology_name, 1.0)]

    # Sample the total sediment thickness grid.
    grid_samples = _read_grid(input_points, total_sediment_thickness_filename, force_positive=True)

    # Ignore samples outside total sediment thickness grid (masked region) since we can only backtrack where there's sediment.
    #
    # Note: The 3rd value (index 2) of each sample is the total sediment thickness (first two values are longitude and latitude).
    #       A value of NaN means the sample is outside the masked region of the grid.
    grid_samples = [grid_sample for grid_sample in grid_samples if not math.isnan(grid_sample[2])]
    
    #
    # Assign reconstruction plate IDs.
    #
    # This appends to each grid sample:
    # - a reconstruction plate ID, and
    # - a partitioning polygon appearance age.
    #
    # Also excludes grid samples with plate IDs not in the region plate IDs (if region plate IDs specified).
    #
    if num_cpus == 1:
        grid_samples = _assign_reconstruction_plate_ids(
                grid_samples, static_polygon_filename, rotation_filenames, region_plate_ids)
    else:
        # Divide the grid samples into a number of groups equal to twice the number of CPUs in case some groups of samples take longer to process than others.
        num_grid_sample_groups = 2 * num_cpus
        num_grid_samples_per_group = math.ceil(float(len(grid_samples)) / num_grid_sample_groups)

        # Distribute the groups of grid samples across the multiprocessing pool.
        with multiprocessing.Pool(num_cpus) as pool:
            grid_samples_list = pool.map(
                    partial(
                        _assign_reconstruction_plate_ids,
                        static_polygon_filename=static_polygon_filename,
                        rotation_filenames=rotation_filenames,
                        region_plate_ids=region_plate_ids),
                    (
                        grid_samples[
                            grid_sample_group_index * num_grid_samples_per_group :
                            (grid_sample_group_index + 1) * num_grid_samples_per_group]
                                    for grid_sample_group_index in range(num_grid_sample_groups)
                    ),
                    1) # chunksize
        
        # Merge output lists back into one list.
        grid_samples = list(itertools.chain.from_iterable(grid_samples_list))
    
    #
    # Exclude grid samples near trenches.
    #
    if num_cpus == 1:
        grid_samples = _exclude_grid_samples_near_trenches(
                grid_samples, pybacktrack.bundle_data.BUNDLE_TRENCHES_FILENAME, pybacktrack.bundle_data.BUNDLE_SUBDUCTING_BOUNDARIES_FILENAME, exclude_distances_to_trenches_kms)
    else:
        # Divide the grid samples into a number of groups equal to twice the number of CPUs in case some groups of samples take longer to process than others.
        num_grid_sample_groups = 2 * num_cpus
        num_grid_samples_per_group = math.ceil(float(len(grid_samples)) / num_grid_sample_groups)

        # Distribute the groups of grid samples across the multiprocessing pool.
        with multiprocessing.Pool(num_cpus) as pool:
            grid_samples_list = pool.map(
                    partial(
                        _exclude_grid_samples_near_trenches,
                        trench_filename=pybacktrack.bundle_data.BUNDLE_TRENCHES_FILENAME,
                        subducting_boundary_filename=pybacktrack.bundle_data.BUNDLE_SUBDUCTING_BOUNDARIES_FILENAME,
                        threshold_distances_to_trenches_kms=exclude_distances_to_trenches_kms),
                    (
                        grid_samples[
                            grid_sample_group_index * num_grid_samples_per_group :
                            (grid_sample_group_index + 1) * num_grid_samples_per_group]
                                    for grid_sample_group_index in range(num_grid_sample_groups)
                    ),
                    1) # chunksize
        
        # Merge output lists back into one list.
        grid_samples = list(itertools.chain.from_iterable(grid_samples_list))

    # The plate IDs assigned above are integers but get converted to float by '_read_grid()' unless we tell it they are integers.
    grid_sample_integer_input_columns = [3]

    # Add age and topography to the total sediment thickness grid samples.
    grid_samples = _read_grid(grid_samples, age_grid_filename, integer_input_columns=grid_sample_integer_input_columns, force_positive=True)
    grid_samples = _read_grid(grid_samples, topography_filename, integer_input_columns=grid_sample_integer_input_columns)

    # Separate grid samples into oceanic and continental.
    continental_grid_samples = []
    oceanic_grid_samples = []
    for longitude, latitude, total_sediment_thickness, reconstruction_plate_id, partitioning_plate_appearance_age, age_grid_age, topography in grid_samples:

        # If topography sampled outside grid then set topography to zero.
        # Shouldn't happen since topography grid is not masked anywhere.
        if math.isnan(topography):
            topography = 0.0
    
        # Topography is negative in ocean but water depth is positive.
        water_depth = -topography
        # Clamp water depth so it's below sea level (ie, must be >= 0).
        water_depth = max(0, water_depth)

        # If sampled outside age grid then is on continental crust near a passive margin.
        if math.isnan(age_grid_age):
            # Use the age from the partitioning static polygon.
            age = partitioning_plate_appearance_age

            continental_grid_samples.append(
                    (longitude, latitude, total_sediment_thickness, water_depth, reconstruction_plate_id, age))
        else:  # oceanic...
            # Use the age from the age grid unless it is too old (ie, older than the partitioning static polygon appearance age by a fixed amount).
            if age_grid_age > partitioning_plate_appearance_age + _MAX_AGE_GRID_ALLOWED_TO_EXCEED_OCEANIC_STATIC_POLYGON_AGE:
                age = partitioning_plate_appearance_age
            else:
                age = age_grid_age
            
            oceanic_grid_samples.append(
                    (longitude, latitude, total_sediment_thickness, water_depth, reconstruction_plate_id, age))

    # The plate IDs assigned above are integers but get converted to float by '_read_grid()' unless we tell it they are integers.
    continental_grid_sample_integer_input_columns = [4]

    # Add crustal thickness and builtin rift start/end times to continental grid samples.
    #
    # Note: For some reason we get a GMT error if we combine these grids in a single 'grdtrack' call, so we separate them instead.
    continental_grid_samples = _read_grid(continental_grid_samples, crustal_thickness_filename, integer_input_columns=continental_grid_sample_integer_input_columns, force_positive=True)
    continental_grid_samples = _read_grid(continental_grid_samples, pybacktrack.bundle_data.BUNDLE_RIFTING_START_FILENAME, integer_input_columns=continental_grid_sample_integer_input_columns, force_positive=True)
    continental_grid_samples = _read_grid(continental_grid_samples, pybacktrack.bundle_data.BUNDLE_RIFTING_END_FILENAME, integer_input_columns=continental_grid_sample_integer_input_columns, force_positive=True)

    # Ignore continental samples with no rifting (no rift start/end times) since there is no sediment deposition without rifting and
    # also no tectonic subsidence.
    #
    # Note: The 8th and 9th values (indices 7 and 8) of each sample are the rift start and end ages.
    #       A value of NaN means there is no rifting at the sample location.
    continental_grid_samples = [grid_sample for grid_sample in continental_grid_samples
                                    if not (math.isnan(grid_sample[7]) or math.isnan(grid_sample[8]))]
    # Ensure rift start ages are not younger than associated rift end ages (due to filtering during grid sampling).
    for grid_sample_index in range(len(continental_grid_samples)):
        grid_sample = continental_grid_samples[grid_sample_index]
        rift_start_age, rift_end_age = grid_sample[7], grid_sample[8]
        if rift_start_age < rift_end_age:
            # Clamp rift start age to the rift end age.
            rift_start_age = rift_end_age
            # Create a new tuple with the rift start age replaced.
            grid_sample = grid_sample[:7] + (rift_start_age,) + grid_sample[8:]
            continental_grid_samples[grid_sample_index] = grid_sample
    
    # If the oldest time was not specified then instead use the oldest of ocean crust ages and continental rift start ages of the input points.
    if oldest_time is None:
        oldest_time = 0.0
        if oceanic_grid_samples:
            # Oceanic ages (at index 5 of each oceanic grid sample).
            oldest_oceanic_time = max(oceanic_grid_sample[5] for oceanic_grid_sample in oceanic_grid_samples)
            oldest_time = max(oldest_time, oldest_oceanic_time)
        if continental_grid_samples:
            # Continental rift start ages (at index 7 of each continental grid sample).
            oldest_continental_time = max(continental_grid_sample[7] for continental_grid_sample in continental_grid_samples)
            oldest_time = max(oldest_time, oldest_continental_time)
    
    # Create times from present day to the oldest requested time in the requested time increments.
    # Note: Using 1e-6 to ensure the oldest time gets included (if it's an exact multiple of the time increment, which it likely will be).
    time_range = [float(time) for time in np.arange(0, oldest_time + 1e-6, time_increment)]
    
    # Find the sea levels over the requested time period.
    if sea_level_model:
        _sea_level = SeaLevel.create_from_model_or_bundled_model_name(sea_level_model)
        # Calculate sea level (relative to present day) that is an average over each time increment in the requested time period.
        # This is a dict indexed by time.
        sea_levels = {time : _sea_level.get_average_level(time + time_increment, time) for time in time_range}
    else:
        sea_levels = None

    # If using a single CPU then just process all ocean/continent points in one call.
    if num_cpus == 1:
        oceanic_paleo_bathymetry = _reconstruct_backtrack_oceanic_bathymetry(
                oceanic_grid_samples,
                time_range,
                ocean_age_to_depth_model,
                lithologies,
                lithology_components,
                dynamic_topography_model,
                sea_levels,
                rotation_filenames,
                anchor_plate_id,
                output_positive_bathymetry_below_sea_level)
        
        continental_paleo_bathymetry = _reconstruct_backtrack_continental_bathymetry(
                continental_grid_samples,
                time_range,
                lithologies,
                lithology_components,
                dynamic_topography_model,
                sea_levels,
                rotation_filenames,
                anchor_plate_id,
                output_positive_bathymetry_below_sea_level)
        
        # Combine the oceanic and continental paleo bathymetry dicts into a single bathymetry dict.
        paleo_bathymetry = {time : [] for time in time_range}
        for paleo_bathymetry_dict in (oceanic_paleo_bathymetry, continental_paleo_bathymetry):
            for time, bathymetries in paleo_bathymetry_dict.items():
                paleo_bathymetry[time].extend(bathymetries)
        
        return paleo_bathymetry
     
    # Divide the oceanic grid samples into a number of groups equal to twice the number of CPUs in case some groups of samples take longer to process than others.
    num_oceanic_grid_sample_groups = 2 * num_cpus
    num_oceanic_grid_samples_per_group = math.ceil(float(len(oceanic_grid_samples)) / num_oceanic_grid_sample_groups)

    # Distribute the groups of oceanic points across the multiprocessing pool.
    with multiprocessing.Pool(num_cpus) as pool:
        oceanic_paleo_bathymetry_dict_list = pool.map(
                partial(
                    _reconstruct_backtrack_oceanic_bathymetry,
                    time_range=time_range,
                    ocean_age_to_depth_model=ocean_age_to_depth_model,
                    lithologies=lithologies,
                    lithology_components=lithology_components,
                    dynamic_topography_model=dynamic_topography_model,
                    sea_levels=sea_levels,
                    rotation_filenames=rotation_filenames,
                    anchor_plate_id=anchor_plate_id,
                    output_positive_bathymetry_below_sea_level=output_positive_bathymetry_below_sea_level),
                (
                    oceanic_grid_samples[
                        oceanic_grid_sample_group_index * num_oceanic_grid_samples_per_group :
                        (oceanic_grid_sample_group_index + 1) * num_oceanic_grid_samples_per_group]
                                for oceanic_grid_sample_group_index in range(num_oceanic_grid_sample_groups)
                ),
                1) # chunksize
    
    # Divide the continental grid samples into a number of groups equal to twice the number of CPUs in case some groups of samples take longer to process than others.
    num_continental_grid_sample_groups = 2 * num_cpus
    num_continental_grid_samples_per_group = math.ceil(float(len(continental_grid_samples)) / num_continental_grid_sample_groups)

    # Distribute the groups of continental points across the multiprocessing pool.
    with multiprocessing.Pool(num_cpus) as pool:
        continental_paleo_bathymetry_dict_list = pool.map(
                partial(
                    _reconstruct_backtrack_continental_bathymetry,
                    time_range=time_range,
                    lithologies=lithologies,
                    lithology_components=lithology_components,
                    dynamic_topography_model=dynamic_topography_model,
                    sea_levels=sea_levels,
                    rotation_filenames=rotation_filenames,
                    anchor_plate_id=anchor_plate_id,
                    output_positive_bathymetry_below_sea_level=output_positive_bathymetry_below_sea_level),
                (
                    continental_grid_samples[
                        continental_grid_sample_group_index * num_continental_grid_samples_per_group :
                        (continental_grid_sample_group_index + 1) * num_continental_grid_samples_per_group]
                                for continental_grid_sample_group_index in range(num_continental_grid_sample_groups)
                ),
                1) # chunksize
    
    # Combine the pool bathymetry dicts into a single bathymetry dict.
    paleo_bathymetry = {time : [] for time in time_range}
    for paleo_bathymetry_dict_list in (oceanic_paleo_bathymetry_dict_list, continental_paleo_bathymetry_dict_list):
        for paleo_bathymetry_dict in paleo_bathymetry_dict_list:
            for time, bathymetries in paleo_bathymetry_dict.items():
                paleo_bathymetry[time].extend(bathymetries)
    
    return paleo_bathymetry


def _reconstruct_backtrack_oceanic_bathymetry(
        oceanic_grid_samples,
        time_range,
        ocean_age_to_depth_model,
        lithologies,
        lithology_components,
        dynamic_topography_model,
        sea_levels,
        rotation_filenames,
        anchor_plate_id,
        output_positive_bathymetry_below_sea_level):

    # Rotation model used to reconstruct the grid points.
    # Cache enough internal reconstruction trees so that we're not constantly recreating them as we move from point to point.
    rotation_model = pygplates.RotationModel(rotation_filenames, reconstruction_tree_cache_size = len(time_range))
    
    # Create time-dependent grid object for sampling dynamic topography (if requested).
    if dynamic_topography_model:
        # Gather all the sample positions and their ages.
        longitudes, latitudes, ages = [], [], []
        for longitude, latitude, _, _, _, age in oceanic_grid_samples:
            longitudes.append(longitude)
            latitudes.append(latitude)
            ages.append(age)
        dynamic_topography_model = DynamicTopography.create_from_model_or_bundled_model_name(dynamic_topography_model, longitudes, latitudes, ages)

        # Pre-calculate dynamic topography for all decompaction times (including present day) and all ocean sample points.
        # At each time we have a list of dynamic topographies (one per ocean sample point) which is stored in a dictionary (keyed by time).
        dynamic_topography = {}
        for decompaction_time in time_range:
            dynamic_topography[decompaction_time] = dynamic_topography_model.sample(decompaction_time)
        if 0.0 not in dynamic_topography:  # present day
            dynamic_topography[0.0] = dynamic_topography_model.sample(0.0)
    else:
        dynamic_topography = None
    
    # Paleo bathymetry is stored as a dictionary mapping each age in time range to a list of 3-tuples (lon, lat, bathymetry).
    paleo_bathymetry = {time : [] for time in time_range}

    # Iterate over the *oceanic* grid samples.
    for grid_sample_index, (longitude, latitude, present_day_total_sediment_thickness, present_day_water_depth, reconstruction_plate_id, age) in enumerate(oceanic_grid_samples):
        
        # Create a well at the current grid sample location with a single stratigraphic layer of total sediment thickness
        # that began sediment deposition at 'age' Ma (and finished at present day).
        well = Well()
        well.add_compacted_unit(0.0, age, 0.0, present_day_total_sediment_thickness, lithology_components, lithologies)
        # If we're reconstructing to times prior to 'age' then add an extra stratigraphic layer with zero thickness to cover the period prior
        # to ocean crust formation at the mid-ocean ridge. We won't actually reconstruct prior to crust formation, but having this zero thickness layer
        # means we don't have to test if None is returned by 'well.decompact(decompaction_time)' for special cases like an age grid value of zero
        # (where we'd still like to create a bathmetry value at present day). Also this extra layer is similar to how it's done with continental crust. 
        if time_range[-1] >= age:
            well.add_compacted_unit(age, time_range[-1] + 1, present_day_total_sediment_thickness, present_day_total_sediment_thickness, lithology_components, lithologies)

        # Unload the present day sediment to get unloaded present day water depth.
        # Apply an isostatic correction to the total sediment thickness (we decompact the well at present day to find this).
        # Note that sea level variations don't apply here because they are zero at present day.
        present_day_decompacted_well = well.decompact(0.0)
        present_day_tectonic_subsidence = present_day_water_depth + present_day_decompacted_well.get_sediment_isostatic_correction()

        # Present-day tectonic subsidence calculated from age-to-depth model.
        present_day_tectonic_subsidence_from_model = age_to_depth.convert_age_to_depth(age, ocean_age_to_depth_model)
        
        # There will be a difference between unloaded water depth and subsidence based on age-to-depth model.
        # Assume this offset is constant for all ages and use it to adjust the subsidence obtained from age-to-depth model for other ages.
        tectonic_subsidence_model_adjustment = present_day_tectonic_subsidence - present_day_tectonic_subsidence_from_model

        # If we have dynamic topography then get present-day dynamic topography.
        if dynamic_topography:
            dynamic_topography_at_present_day = dynamic_topography[0.0][grid_sample_index]
        
        present_day_location = pygplates.PointOnSphere(latitude, longitude)
        
        for decompaction_time in time_range:
            # If the decompaction time has exceeded the age of ocean crust (bottom age of well) then we're finished with current well.
            # That is, the current time exceeded the age grid value. Which means the ocean crust at the current point has been reconstructed
            # back prior to the time it was created. So we're finished with it (because the remaining times in the loop are even older).
            if decompaction_time > age:
                break

            # Decompact at the current time.
            decompacted_well = well.decompact(decompaction_time)

            # Age of the ocean basin at location when it's decompacted to the current decompaction age.
            paleo_age_of_crust_at_decompaction_time = age - decompaction_time
            
            # Use age-to-depth model to lookup depth given the age.
            tectonic_subsidence_from_model = age_to_depth.convert_age_to_depth(paleo_age_of_crust_at_decompaction_time, ocean_age_to_depth_model)
            
            # We add in the constant offset between the age-to-depth model (at age of well) and unloaded water depth at present day.
            decompacted_well.tectonic_subsidence = tectonic_subsidence_from_model + tectonic_subsidence_model_adjustment
            
            # If we have dynamic topography then add in the difference at current decompaction time compared to present-day.
            if dynamic_topography:
                dynamic_topography_at_decompaction_time = dynamic_topography[decompaction_time][grid_sample_index]
                
                # Dynamic topography is elevation but we want depth (subsidence) so subtract (instead of add).
                decompacted_well.tectonic_subsidence -= dynamic_topography_at_decompaction_time - dynamic_topography_at_present_day
            
            # If we have sea levels then store the sea level (relative to present day) at current decompaction time
            # in the decompacted well (it'll get used later when calculating water depth).
            if sea_levels:
                decompacted_well.sea_level = sea_levels[decompaction_time]
            
            # Calculate water depth (from decompacted sediment, tectonic subsidence, sea level and dynamic topography).
            bathymetry = decompacted_well.get_water_depth()

            # If we're outputting negative bathymetry values below sea level then we should negate our water depths.
            if not output_positive_bathymetry_below_sea_level:
                # Topography/bathymetry grids typically have negative values below sea level (and positive above).
                bathymetry = -bathymetry
        
            # Get rotation from present day to current decompaction time using the reconstruction plate ID of the location.
            #
            # NOTE: We specify 'from_time=0' since there could be a non-zero finite rotation at present day (generally there shouldn't be) and
            #       we don't want our present day location to move when 'decompaction_time' is zero (or have this offset for non-zero times).
            rotation = rotation_model.get_rotation(decompaction_time, reconstruction_plate_id, from_time=0, anchor_plate_id=anchor_plate_id)
            # Reconstruct location to current decompaction time.
            reconstructed_location = rotation * present_day_location
            reconstructed_latitude, reconstructed_longitude = reconstructed_location.to_lat_lon()

            # Add the bathymetry (and its reconstructed location) to the list of bathymetry points for the current decompaction time.
            paleo_bathymetry[decompaction_time].append((reconstructed_longitude, reconstructed_latitude, bathymetry))

    return paleo_bathymetry


def _reconstruct_backtrack_continental_bathymetry(
        continental_grid_samples,
        time_range,
        lithologies,
        lithology_components,
        dynamic_topography_model,
        sea_levels,
        rotation_filenames,
        anchor_plate_id,
        output_positive_bathymetry_below_sea_level):

    # Rotation model used to reconstruct the grid points.
    # Cache enough internal reconstruction trees so that we're not constantly recreating them as we move from point to point.
    rotation_model = pygplates.RotationModel(rotation_filenames, reconstruction_tree_cache_size = len(time_range))
    
    # Use integral rift start ages when caching dynamic topography to avoid an excessive number of dynamic topography samples
    # (which can happen since the rift start ages are linearly filtered from rift start age grid and can therefore have many different values).
    def get_dynamic_topography_rift_start_age(rift_start_age):
        return math.ceil(rift_start_age)
    
    # Create time-dependent grid object for sampling dynamic topography (if requested).
    if dynamic_topography_model:
        # Gather all the sample positions and their ages.
        longitudes, latitudes, ages = [], [], []
        dynamic_topography_rift_start_ages = set()
        for longitude, latitude, _, _, _, _, _, rift_start_age, _ in continental_grid_samples:
            longitudes.append(longitude)
            latitudes.append(latitude)
            ages.append(rift_start_age)
            dynamic_topography_rift_start_ages.add(get_dynamic_topography_rift_start_age(rift_start_age))
        dynamic_topography_model = DynamicTopography.create_from_model_or_bundled_model_name(dynamic_topography_model, longitudes, latitudes, ages)

        # Pre-calculate dynamic topography for all decompaction times (including present day) and all continent sample points.
        # At each time we have a list of dynamic topographies (one per continent sample point) which is stored in a dictionary (keyed by time).
        dynamic_topography = {}
        for decompaction_time in time_range:
            dynamic_topography[decompaction_time] = dynamic_topography_model.sample(decompaction_time)
        if 0.0 not in dynamic_topography:  # present day
            dynamic_topography[0.0] = dynamic_topography_model.sample(0.0)
        
        # Also make sure we have dynamic topography for all the (integral) rift start ages since they can be outside
        # the range (and time increment) of present day to oldest time.
        #
        # Note that we use integral ages to avoid an excessive number of dynamic topography samples
        # (which can happen since the rift start ages are linearly filtered from the rift start age grid and
        # therefore we can get a lot of different values).
        for dynamic_topography_rift_start_age in dynamic_topography_rift_start_ages:
            if dynamic_topography_rift_start_age not in dynamic_topography:
                dynamic_topography[dynamic_topography_rift_start_age] = dynamic_topography_model.sample(dynamic_topography_rift_start_age)
    else:
        dynamic_topography = None
    
    # Paleo bathymetry is stored as a dictionary mapping each age in time range to a list of 3-tuples (lon, lat, bathymetry).
    paleo_bathymetry = {time : [] for time in time_range}

    # Iterate over the *continental* grid samples.
    for grid_sample_index, (longitude, latitude, present_day_total_sediment_thickness, present_day_water_depth, reconstruction_plate_id, age, present_day_crustal_thickness, rift_start_age, rift_end_age) in enumerate(continental_grid_samples):
        
        # Create a well at the current grid sample location with a single stratigraphic layer of total sediment thickness
        # that began sediment deposition when rifting began (and finished at present day).
        well = Well()
        well.add_compacted_unit(0.0, rift_start_age, 0.0, present_day_total_sediment_thickness, lithology_components, lithologies)
        # If we're reconstructing to times prior to rifting then add an extra stratigraphic layer with zero thickness to cover the period prior to rifting.
        # Having this zero thickness layer prevents us from prematurely ending bathymetry reconstruction for times prior to rifting by ensuring
        # 'well.decompact(decompaction_time)' does not return None (when 'decompaction_time >= rift_start_age').
        # The tectonic subsidence will be zero during this time period.
        # It also allows us to easily see other effects prior to sediment deposition (eg, sea level, dynamic topography). 
        if time_range[-1] >= rift_start_age:
            well.add_compacted_unit(rift_start_age, time_range[-1] + 1, present_day_total_sediment_thickness, present_day_total_sediment_thickness, lithology_components, lithologies)

        # Unload the present day sediment to get unloaded present day water depth.
        # Apply an isostatic correction to the total sediment thickness (we decompact the well at present day to find this).
        # Note that sea level variations don't apply here because they are zero at present day.
        present_day_decompacted_well = well.decompact(0.0)
        present_day_tectonic_subsidence = present_day_water_depth + present_day_decompacted_well.get_sediment_isostatic_correction()
        
        # If we have dynamic topography then get dynamic topography at rift start and at present day.
        if dynamic_topography:
            dynamic_topography_at_present_day = dynamic_topography[0.0][grid_sample_index]
            # Note that we only guaranteed to have dynamic topography values at *integral* rift start ages
            # (and obtained using 'get_dynamic_topography_rift_start_age').
            dynamic_topography_at_rift_start = dynamic_topography[get_dynamic_topography_rift_start_age(rift_start_age)][grid_sample_index]
            
            # Estimate how much of present-day subsidence is due to dynamic topography.
            # We crudely remove the relative difference of dynamic topography between rift start and present day
            # so we can see how much subsidence between those two times is due to stretching and thermal subsidence.
            # Dynamic topography is elevation but we want depth (subsidence) so add (instead of subtract).
            present_day_tectonic_subsidence += dynamic_topography_at_present_day - dynamic_topography_at_rift_start

        # Attempt to estimate rifting stretching factor (beta) that generates the present day tectonic subsidence.
        rift_beta, subsidence_residual = rifting.estimate_beta(
            present_day_tectonic_subsidence,
            present_day_crustal_thickness,
            rift_end_age)
        
        # Skip the current grid sample if the rifting stretching factor (beta) estimate results in a
        # tectonic subsidence inaccuracy (at present day) exceeding this amount (in metres).
        #
        # This can happen if the actual subsidence is quite deep and the beta value required to achieve
        # this subsidence would be unrealistically large and result in a pre-rift crustal thickness that
        # exceeds typical lithospheric thicknesses.
        if math.fabs(subsidence_residual) > _MAX_TECTONIC_SUBSIDENCE_RIFTING_RESIDUAL_ERROR:
            continue
        
        # Initial (pre-rift) crustal thickness is beta times present day crustal thickness.
        pre_rift_crustal_thickness = rift_beta * present_day_crustal_thickness
        
        present_day_location = pygplates.PointOnSphere(latitude, longitude)
        
        for decompaction_time in time_range:
            # If the decompaction time has exceeded the age of continental crust then we're finished with current well.
            # That is, the current time exceeded the begin time of static polygon. Which means the continental crust at the current point has been
            # reconstructed back prior to the time it was created. So we're finished with it (because the remaining times in the loop are even older).
            if decompaction_time > age:
                break

            # Decompact at the current time.
            decompacted_well = well.decompact(decompaction_time)

            # Calculate rifting subsidence at decompaction time.
            decompacted_well.tectonic_subsidence = rifting.total_subsidence(
                    rift_beta, pre_rift_crustal_thickness, decompaction_time, rift_end_age, rift_start_age)
        
            # If we have dynamic topography then add in the difference at current decompaction time compared to rift start.
            if dynamic_topography:
                dynamic_topography_at_decompaction_time = dynamic_topography[decompaction_time][grid_sample_index]
                
                # Account for any change in dynamic topography between rift start and current decompaction time.
                # Dynamic topography is elevation but we want depth (subsidence) so subtract (instead of add).
                decompacted_well.tectonic_subsidence -= dynamic_topography_at_decompaction_time - dynamic_topography_at_rift_start
            
            # If we have sea levels then store the sea level (relative to present day) at current decompaction time
            # in the decompacted well (it'll get used later when calculating water depth).
            if sea_levels:
                decompacted_well.sea_level = sea_levels[decompaction_time]
            
            # Calculate water depth (from decompacted sediment, tectonic subsidence, sea level and dynamic topography).
            bathymetry = decompacted_well.get_water_depth()

            # If we're outputting negative bathymetry values below sea level then we should negate our water depths.
            if not output_positive_bathymetry_below_sea_level:
                # Topography/bathymetry grids typically have negative values below sea level (and positive above).
                bathymetry = -bathymetry
        
            # Get rotation from present day to current decompaction time using the reconstruction plate ID of the location.
            #
            # NOTE: We specify 'from_time=0' since there could be a non-zero finite rotation at present day (generally there shouldn't be) and
            #       we don't want our present day location to move when 'decompaction_time' is zero (or have this offset for non-zero times).
            rotation = rotation_model.get_rotation(decompaction_time, reconstruction_plate_id, from_time=0, anchor_plate_id=anchor_plate_id)
            # Reconstruct location to current decompaction time.
            reconstructed_location = rotation * present_day_location
            reconstructed_latitude, reconstructed_longitude = reconstructed_location.to_lat_lon()

            # Add the bathymetry (and its reconstructed location) to the list of bathymetry points for the current decompaction time.
            paleo_bathymetry[decompaction_time].append((reconstructed_longitude, reconstructed_latitude, bathymetry))

    return paleo_bathymetry


def _assign_reconstruction_plate_ids(
        grid_samples,
        static_polygon_filename,
        rotation_filenames,
        region_plate_ids=None):
    
    # Static polygons partitioner used to assign plate IDs to the grid points.
    plate_partitioner = pygplates.PlatePartitioner(static_polygon_filename, rotation_filenames)

    updated_grid_samples = []
    for grid_sample in grid_samples:
        # Find the plate ID of the static polygon containing the present day location (or zero if not in any plates, which shouldn't happen).
        longitude, latitude = grid_sample[0], grid_sample[1]
        present_day_location = pygplates.PointOnSphere(latitude, longitude)
        partitioning_plate = plate_partitioner.partition_point(present_day_location)
        if not partitioning_plate:
            # Not contained by any plates. Shouldn't happen since static polygons have global coverage,
            # but might if there's tiny cracks between polygons.
            continue

        reconstruction_plate_id = partitioning_plate.get_feature().get_reconstruction_plate_id()

        # If any regions were specified then skip any grid samples outside all specified regions.
        if region_plate_ids:
            if reconstruction_plate_id not in region_plate_ids:
                # Skip current grid sample.
                continue

        # The appearance age of the partitioning polygon (static polygon covering this point).
        partitioning_plate_appearance_age, _ = partitioning_plate.get_feature().get_valid_time()
        
        # Append the assigned reconstruction plate ID and the partitioning polygon appearance age to the grid sample.
        updated_grid_sample = tuple(grid_sample) + (reconstruction_plate_id, partitioning_plate_appearance_age)

        updated_grid_samples.append(updated_grid_sample)

    return updated_grid_samples


def _exclude_grid_samples_near_trenches(
        grid_samples,
        trench_filename,
        subducting_boundary_filename,
        threshold_distances_to_trenches_kms=None):

    trench_features = pygplates.FeatureCollection(trench_filename)

    subducting_boundary_features = pygplates.FeatureCollection(subducting_boundary_filename)
    subducting_boundary_polygons_dict = {
            feature.get_feature_id().get_string() : feature.get_geometry(lambda property: True)
                    for feature in subducting_boundary_features}

    # Extract the trench geometries and threshold distances from the trench features.
    trench_geometries = []
    trench_distances = []
    trench_subducting_boundary_polygons = []
    for trench_feature in trench_features:
        if threshold_distances_to_trenches_kms is None:
            # Default to using built-in per-trench defaults (each trench potentially has different distances extracted from the trench feature).
            trench_subduction_distance_radians = trench_feature.get_shapefile_attribute('exclude_subducting_distance_to_trenches_kms') / pygplates.Earth.mean_radius_in_kms
            trench_overriding_distance_radians = trench_feature.get_shapefile_attribute('exclude_overriding_distance_to_trenches_kms') / pygplates.Earth.mean_radius_in_kms
        else:
            # User has specified a global default distance for the subducting and overriding sides of all trenches.
            trench_subduction_distance_radians = threshold_distances_to_trenches_kms[0] / pygplates.Earth.mean_radius_in_kms
            trench_overriding_distance_radians = threshold_distances_to_trenches_kms[1] / pygplates.Earth.mean_radius_in_kms
        
        # Get the subducting polygon attached to the current trench segment.
        subducting_boundary_polygon = None
        subducting_boundary_feature_id_string = trench_feature.get_shapefile_attribute('subducting_boundary_feature_id')
        if subducting_boundary_feature_id_string:
            subducting_boundary_polygon = subducting_boundary_polygons_dict.get(subducting_boundary_feature_id_string)
        # There should always be one since the pre-processing script has ensured this.
        # If for some reason there isn't then we'll just skip the current trench segment.
        if not subducting_boundary_polygon:
            continue
        
        # During pre-processing we've ensured that each feature will have a single geometry.
        # We don't really know what the geometry property *name* is, so let's not require it to be the default geometry property name (in case it isn't).
        trench_geometries.append(trench_feature.get_geometry(lambda property: True))
        trench_distances.append((trench_subduction_distance_radians, trench_overriding_distance_radians))
        trench_subducting_boundary_polygons.append(subducting_boundary_polygon)

    included_grid_samples = []
    for grid_sample in grid_samples:
        # Extract the grid sample location.
        grid_longitude, grid_latitude = grid_sample[0], grid_sample[1]
        grid_location = pygplates.PointOnSphere(grid_latitude, grid_longitude)

        # See if current grid sample is near any trenches.
        mask_grid_location = False
        for trench_index in range(len(trench_geometries)):
            trench_geometry = trench_geometries[trench_index]
            trench_subduction_distance_radians, trench_overriding_distance_radians = trench_distances[trench_index]
            trench_subducting_boundary_polygon = trench_subducting_boundary_polygons[trench_index]

            is_grid_location_on_subducting_side_of_trench = None  # None means haven't done point-in-subducting-polygon test yet.

            # First test if current grid location is near the subducting side of the trench.
            if trench_subduction_distance_radians:  # Only need to test if distance is non-zero.
                if pygplates.GeometryOnSphere.distance(grid_location, trench_geometry, trench_subduction_distance_radians) is not None:
                    # Current grid sample is near the current trench (within subduction distance threshold).
                    # So see if it's on the subducting side of the current trench.
                    # This is done by testing if current grid sample is inside the subducting polygon adjoining the current trench.
                    if is_grid_location_on_subducting_side_of_trench is None:  # First do point-in-polygon test if not yet done.
                        is_grid_location_on_subducting_side_of_trench = trench_subducting_boundary_polygon.is_point_in_polygon(grid_location)
                    if is_grid_location_on_subducting_side_of_trench:
                        mask_grid_location = True
                        # We've got our result so skip all remaining trench segments.
                        break

            # Next test if current grid location is near the overriding side of the trench.
            if trench_overriding_distance_radians:  # Only need to test if distance is non-zero.
                if pygplates.GeometryOnSphere.distance(grid_location, trench_geometry, trench_overriding_distance_radians) is not None:
                    # Current grid sample is near the current trench (within overriding distance threshold).
                    # So see if it's on the overriding side of the current trench.
                    # This is done by testing if current grid sample is *not* inside the subducting polygon adjoining the current trench.
                    if is_grid_location_on_subducting_side_of_trench is None:  # First do point-in-polygon test if not yet done.
                        is_grid_location_on_subducting_side_of_trench = trench_subducting_boundary_polygon.is_point_in_polygon(grid_location)
                    if not is_grid_location_on_subducting_side_of_trench:
                        mask_grid_location = True
                        # We've got our result so skip all remaining trench segments.
                        break

        # Skip current grid sample if it should be masked.
        if mask_grid_location:
            continue
        
        included_grid_samples.append(grid_sample)

    return included_grid_samples


def generate_lon_lat_points(grid_spacing_degrees):
    """generate_lon_lat_points(grid_spacing_degrees)
    Generates a global grid of points uniformly spaced in longitude and latitude.

    Parameters
    ----------
    grid_spacing_degrees : float
        Spacing between points (in degrees).
    
    Returns
    -------
    list of (longitude, latitude) tuples
    
    Raises
    ------
    ValueError
        If ``grid_spacing_degrees`` is negative or zero.

    Notes
    -----
    Longitudes start at -180 (dateline) and latitudes start at -90.
    If 180 is an integer multiple of ``grid_spacing_degrees`` then the final longitude is also on the dateline (+180).
        
    .. versionadded:: 1.4
    """
    
    if grid_spacing_degrees <= 0:
        raise ValueError('Grid spacing must be positive (and non-zero).')
    
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


def _read_grid(
        input,
        grid_filename,
        integer_input_columns=None,
        force_positive=False):
    """
    Samples a grid file at the specified locations.
    
    'input' is a list of (longitude, latitude, [other_values ...]) sequences where latitude and longitude are in degrees.
    Should at least have 2-sequences (longitude, latitude) but 'grdtrack' allows extra columns.
    
    Returns a list of tuples of float values.
    For example, if input was (longitude, latitude) sequences then output is (longitude, latitude, sample) tuples.
    If input was (longitude, latitude, value) sequences then output is (longitude, latitude, value, sample_grid) tuples.
    """
    
    # Create a multiline string (one line per lon/lat/value1/etc row).
    location_data = ''.join(
            ' '.join(str(item) for item in row) + '\n' for row in input)

    # The command-line strings to execute GMT 'grdtrack'.
    grdtrack_command_line = ["gmt", "grdtrack",
        # Geographic input/output coordinates...
        "-fg",
        # Avoid anti-aliasing...
        "-n+a+bg+t0.5",
        "-G{0}".format(grid_filename)]
    
    # Call the system command.
    stdout_data = call_system_command(grdtrack_command_line, stdin=location_data, return_stdout=True)

    # Extract the sampled values.
    output_values = []
    for line in stdout_data.splitlines():
        # Each line returned by GMT grdtrack contains "longitude latitude grid1_value [grid2_value ...]".
        # Note that if GMT returns "NaN" then we'll return float('nan').
        
        # If any columns should be 'int' (instead of 'float') then convert them to 'int'.
        if integer_input_columns:
            output_value = tuple(
                (float(column_value) if column not in integer_input_columns else int(column_value))
                for column, column_value in enumerate(line.split()))
        else:
            # All columns are 'float'.
            output_value = tuple(float(column_value) for column_value in line.split())

        # If requested to clamp negative samples to zero.
        # Note: value just sampled is the last column.
        if force_positive and output_value[-1] < 0.0:
            # Make last column (just sampled) be zero.
            output_value = output_value[:-1] + (0.0,)
        
        output_values.append(output_value)
    
    return output_values


def _write_grid(
        input,
        grid_spacing_degrees,
        grid_filename,
        xyz_filename=None):
    """
    Grid the input data and write to an output grid file.
    
    'input' is a list of (longitude, latitude, value) sequences where latitude and longitude are in degrees.
    'grid_spacing_degrees' is spacing of output grid points in degrees.
    If 'xyz_filename' is specified then an xyz file is also created (from 'input').
    """
    
    # Create a multiline string (one line per lon/lat/value row).
    input_data = ''.join(
            ' '.join(str(item) for item in row) + '\n' for row in input)

    # The command-line strings to execute GMT 'nearneighbor'.
    #
    # Our first call to GMT 'nearneighbor' essentially creates a mask of non-NaN regions using a small search radius.
    #
    # This mask will ensure that we don't expand the final output grid too far into NaN regions
    # (because the second GMT 'nearneighbor' will use a larger search radius that would normally cause this expansion).
    #
    # First generate a temporary grid filename (based on output grid filename so that multiprocessing processes don't clobber each other).
    non_nan_mask_filename, _ = os.path.splitext(grid_filename)
    non_nan_mask_filename += '_non_nan_mask.nc'
    non_nan_mask_command_line = [
        "gmt",
        "nearneighbor",
        "-N1+m1", # Divide search radius into 1 sectors and require a value in that sector.
        "-S{0}d".format(0.9 * grid_spacing_degrees), # Search radius is a smaller multiple of the grid spacing.
        "-I{0}".format(grid_spacing_degrees),
        # Use GMT gridline registration since our input point grid has data points on the grid lines.
        # Gridline registration is the default so we don't need to force pixel registration...
        # "-r", # Force pixel registration since data points are at centre of cells.
        "-Rg",
        "-fg",
        "-G{0}".format(non_nan_mask_filename)]
    
    # Call the system command.
    call_system_command(non_nan_mask_command_line, stdin=input_data)
    
    # The command-line strings to execute GMT 'nearneighbor'.
    #
    # Our second call to GMT 'nearneighbor' increases the search radius for the following reasons:
    #
    # As the present day grid of points is rotated/reconstructed, it sweeps across the static output grid
    # (used by GMT nearneighbor) and should be sampled/filtered appropriately for the high spatial-frequency
    # bathymetry elevations (due to present day bathymetry grid). If it's not then bathymetry peaks/hills
    # (especially really spikey ones) appear to bob up and down as you animate the paleobathymetry grids through time.
    #
    # It seems a search radius of 3.0 (times grid spacing) works well, although it does wash/blur the detail out a little
    # (conversely 1.5 retains more detail but still has a little too much aliasing). And with 3.0, specifying -N8+m6 looks
    # less aliased than -N4+m3, probably due to averaging/smoothing over 8 sectors instead of 4.
    # This was gleamed from looking for pixels, at bathymetry peaks/hills, that have a flickering colour as the grids are
    # animated through time in GPlates (loaded as a time-dependent raster).
    #
    # And using a 75% min-sector/total-sector ratio (eg, -N8+m6) rather than 100% means the bathymetry boundary
    # (between non-NaN and NaN) isn't brought too far inward towards the interior non-NaN regions since not
    # all sectors are required to contain data (bathymetry).
    #
    # First generate a temporary grid filename (based on output grid filename so that multiprocessing processes don't clobber each other).
    anti_aliasing_filename, _ = os.path.splitext(grid_filename)
    anti_aliasing_filename += '_anti_aliasing.nc'
    nearneighbor_command_line = [
        "gmt",
        "nearneighbor",
        "-N8+m6", # Divide search radius into 8 sectors but only require values in 6 sectors.
        "-S{0}d".format(3.0 * grid_spacing_degrees), # Search radius is a larger multiple the grid spacing.
        "-I{0}".format(grid_spacing_degrees),
        # Use GMT gridline registration since our input point grid has data points on the grid lines.
        # Gridline registration is the default so we don't need to force pixel registration...
        # "-r", # Force pixel registration since data points are at centre of cells.
        "-Rg",
        "-fg",
        "-G{0}".format(anti_aliasing_filename)]
    
    # Call the system command.
    call_system_command(nearneighbor_command_line, stdin=input_data)
    
    # The command-line strings to execute GMT 'grdmath'.
    #
    # This combines the previous two GMT 'nearneighbor' grids such that the output is NaN where
    # 'non_nan_mask_filename' is NaN, otherwise the value from 'anti_aliasing_filename' (which also has NaNs).
    grdmath_command_line = [
        "gmt",
        "grdmath",
        anti_aliasing_filename,  # A
        non_nan_mask_filename,   # B
        "OR",  # GMT: NaN if B == NaN, else A
        "=",
        grid_filename]
    
    # Call the system command.
    call_system_command(grdmath_command_line)

    # Remove the two temporary grid files.
    if os.access(non_nan_mask_filename, os.R_OK):
        os.remove(non_nan_mask_filename)
    if os.access(anti_aliasing_filename, os.R_OK):
        os.remove(anti_aliasing_filename)
    
    # Also create an xyz file (from 'input') if requested.
    if xyz_filename is not None:
        with open(xyz_filename, 'w') as xyz_file:
            xyz_file.write(input_data)


def _write_grid_multiprocessing(
        paleo_bathymetry_and_reconstruction_time,
        grid_spacing,
        grid_file_prefix,
        output_xyz):
    
    paleo_bathymetry, reconstruction_time = paleo_bathymetry_and_reconstruction_time
    # Generate paleo bathymetry grid from list of reconstructed points.
    paleo_bathymetry_grid_filename = '{0}_{1}.nc'.format(grid_file_prefix, reconstruction_time)
    # Also create xyz file if requested.
    paleo_bathymetry_xyz_filename = None
    if output_xyz:
        paleo_bathymetry_xyz_filename, _ = os.path.splitext(paleo_bathymetry_grid_filename)
        paleo_bathymetry_xyz_filename += '.xyz'
    _write_grid(paleo_bathymetry, grid_spacing, paleo_bathymetry_grid_filename, paleo_bathymetry_xyz_filename)


def write_bathymetry_grids(
        paleo_bathymetry,
        grid_spacing_degrees,
        output_file_prefix,
        output_xyz=False,
        use_all_cpus=False):
    """write_paleo_bathymetry_grids(\
        paleo_bathymetry,\
        grid_spacing_degrees,\
        output_file_prefix,\
        output_xyz=False,\
        use_all_cpus=False)
    Grid paleo bathymetry into a NetCDF grid for each time step.
    
    Parameters
    ----------
    paleo_bathymetry : dict
        A dict mapping each reconstructed time to a list of 3-tuple (longitude, latitude, bathymetry)
        The reconstructed paleo bathymetry points over a sequence of reconstructed times.
        Each key in the returned dict is one of those times and each value in the dict is a list of reconstructed paleo bathymetries
        represented as a 3-tuple containing reconstructed longitude, reconstructed latitude and paleo bathmetry.
    grid_spacing_degrees : float
        Lat/lon grid spacing (in degrees). Ideally this should match the spacing of the input points used to generate the paleo bathymetries.
    output_file_prefix : string
        The prefix of the output paleo bathymetry grid filenames over time, with "_<time>.nc" appended.
    output_xyz : bool, optional
        Whether to also create a GMT xyz file (with ".xyz" extension) for each output paleo bathymetry grid.
        Each row of each xyz file contains "longitude latitude bathymetry".
        Default is to only create grid files (no xyz).
    use_all_cpus : bool or int, optional
        If ``False`` (or zero) then use a single CPU.
        If ``True`` then distribute CPU processing across all CPUs (cores).
        If a positive integer then use that many CPUs (cores).
        Defaults to ``False`` (single CPU).
        
    Notes
    -----
    .. versionadded:: 1.4
    """
    
    # Generate a paleo bathymetry grid file for each reconstruction time in the requested time period.
    if not use_all_cpus:
        for reconstruction_time, paleo_bathymetry_at_reconstruction_time in paleo_bathymetry.items():
            # Get the list of (reconstructed_longitude, reconstructed_latitude, reconstructed_bathymetry) at current reconstruction time.
            # Generate paleo bathymetry grid from list of reconstructed points.
            paleo_bathymetry_grid_filename = '{0}_{1}.nc'.format(output_file_prefix, reconstruction_time)
            # Also create xyz file if requested.
            paleo_bathymetry_xyz_filename = None
            if output_xyz:
                paleo_bathymetry_xyz_filename, _ = os.path.splitext(paleo_bathymetry_grid_filename)
                paleo_bathymetry_xyz_filename += '.xyz'
            _write_grid(paleo_bathymetry_at_reconstruction_time, grid_spacing_degrees, paleo_bathymetry_grid_filename, paleo_bathymetry_xyz_filename)

    else:  # Use 'multiprocessing' pools to distribute across CPUs...

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
                        _write_grid_multiprocessing,
                        grid_spacing=grid_spacing_degrees,
                        grid_file_prefix=output_file_prefix,
                        output_xyz=output_xyz),
                    (
                        (paleo_bathymetry_at_reconstruction_time, reconstruction_time)
                            for reconstruction_time, paleo_bathymetry_at_reconstruction_time in paleo_bathymetry.items()
                    ),
                    1) # chunksize


def reconstruct_backtrack_bathymetry_and_write_grids(
        output_file_prefix,
        grid_spacing_degrees,
        oldest_time=None,
        time_increment=1,
        lithology_filenames=[pybacktrack.bundle_data.DEFAULT_BUNDLE_LITHOLOGY_FILENAME],
        age_grid_filename=pybacktrack.bundle_data.BUNDLE_AGE_GRID_FILENAME,
        topography_filename=pybacktrack.bundle_data.BUNDLE_TOPOGRAPHY_FILENAME,
        total_sediment_thickness_filename=pybacktrack.bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,
        crustal_thickness_filename=pybacktrack.bundle_data.BUNDLE_CRUSTAL_THICKNESS_FILENAME,
        rotation_filenames=pybacktrack.bundle_data.BUNDLE_RECONSTRUCTION_ROTATION_FILENAMES,
        static_polygon_filename=pybacktrack.bundle_data.BUNDLE_RECONSTRUCTION_STATIC_POLYGON_FILENAME,
        dynamic_topography_model=None,
        sea_level_model=None,
        lithology_name=DEFAULT_LITHOLOGY_NAME,
        ocean_age_to_depth_model=age_to_depth.DEFAULT_MODEL,
        exclude_distances_to_trenches_kms=None,
        region_plate_ids=None,
        anchor_plate_id=0,
        output_positive_bathymetry_below_sea_level=False,
        output_xyz=False,
        use_all_cpus=False):
    # Adding function signature on first line of docstring otherwise Sphinx autodoc will print out
    # the expanded values of the bundle filenames.
    """reconstruct_paleo_bathymetry_grids(\
        output_file_prefix,\
        grid_spacing_degrees,\
        oldest_time=None,\
        time_increment=1,\
        lithology_filenames=[pybacktrack.DEFAULT_BUNDLE_LITHOLOGY_FILENAME],\
        age_grid_filename=pybacktrack.BUNDLE_AGE_GRID_FILENAME,\
        topography_filename=pybacktrack.BUNDLE_TOPOGRAPHY_FILENAME,\
        total_sediment_thickness_filename=pybacktrack.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,\
        crustal_thickness_filename=pybacktrack.BUNDLE_CRUSTAL_THICKNESS_FILENAME,\
        rotation_filenames=pybacktrack.bundle_data.BUNDLE_RECONSTRUCTION_ROTATION_FILENAMES,\
        static_polygon_filename=pybacktrack.bundle_data.BUNDLE_RECONSTRUCTION_STATIC_POLYGON_FILENAME,\
        dynamic_topography_model=None,\
        sea_level_model=None,\
        lithology_name=pybacktrack.DEFAULT_PALEO_BATHYMETRY_LITHOLOGY_NAME,\
        ocean_age_to_depth_model=pybacktrack.AGE_TO_DEPTH_DEFAULT_MODEL,\
        exclude_distances_to_trenches_kms=None,\
        region_plate_ids=None,\
        anchor_plate_id=0,\
        output_positive_bathymetry_below_sea_level=False,\
        output_xyz=False,\
        use_all_cpus=False)
    Same as :func:`pybacktrack.reconstruct_paleo_bathymetry` but also generates present day input points on a lat/lon grid and
    outputs paleobathymetry as a NetCDF grid for each time step.
    
    Parameters
    ----------
    output_file_prefix : string
        The prefix of the output paleo bathymetry grid filenames over time, with "_<time>.nc" appended.
    grid_spacing_degrees : float
        Spacing between lat/lon points (in degrees) to sample bathymetry at present day.
        Note that any samples outside the masked region of the total sediment thickness grid are ignored.
    oldest_time : float, optional
        The oldest time (in Ma) that output is generated back to (from present day). Value must not be negative.
        If not specified then the oldest of oceanic crustal ages (for those grid points on oceanic crust) and rift start ages
        (for those grid points on continental crust) is used instead.
    time_increment: float
        The time increment (in My) that output is generated (from present day back to oldest time). Value must be positive.
    lithology_filenames : list of string, optional
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
    rotation_filenames : list of string, optional
        List of filenames containing rotation features (to reconstruct sediment-deposited crust).
        If not specified then defaults to the built-in global rotations associated with the topological model
        used to generate the built-in rift start/end time grids.
    static_polygon_filename : string, optional
        Filename containing static polygon features (to assign plate IDs to points on sediment-deposited crust).
        If not specified then defaults to the built-in static polygons associated with the topological model
        used to generate the built-in rift start/end time grids.
    dynamic_topography_model : string or tuple, optional
        Represents a time-dependent dynamic topography raster grid (in *mantle* frame).
        
        Can be either:
        
        * A string containing the name of a bundled dynamic topography model.
        
          Choices include ``terra``, ``M1``, ``M2``, ``M3``, ``M4``, ``M5``, ``M6``, ``M7``, ``ngrand``, ``s20rts``, ``smean``, ``AY18``, ``KM16``, ``D10_gmcm9`` and ``gld428``.
        * A tuple containing the three elements (dynamic topography list filename, static polygon filename, rotation filenames).
        
          The first tuple element is the filename of file containing list of dynamic topography grids (and associated times).
          Each row in this list file should contain two columns.
          First column containing filename (relative to list file) of a dynamic topography grid at a particular time.
          Second column containing associated time (in Ma).
          The second tuple element is the filename of file containing static polygons associated with dynamic topography model.
          This is used to assign plate ID to a location so it can be reconstructed.
          The third tuple element is the filename of the rotation file associated with model.
          Only the rotation file for static continents/oceans is needed (ie, deformation rotations not needed).
        
    sea_level_model : string, optional
        Used to obtain sea levels relative to present day.
        Can be either the name of a bundled sea level model, or a sea level filename.
        Bundled sea level models include ``Haq87_SealevelCurve`` and ``Haq87_SealevelCurve_Longterm``.
    lithology_name : string, optional
        Lithology name of the all sediment (must be present in lithologies file).
        The total sediment thickness at all sediment locations consists of a single lithology.
        Defaults to ``Average_ocean_floor_sediment``.
    ocean_age_to_depth_model : {pybacktrack.AGE_TO_DEPTH_MODEL_RHCW18, pybacktrack.AGE_TO_DEPTH_MODEL_CROSBY_2007, pybacktrack.AGE_TO_DEPTH_MODEL_GDH1} or function, optional
        The model to use when converting ocean age to depth at a location
        (if on ocean floor - not used for continental passive margin).
        It can be one of the enumerated values, or a callable function accepting a single non-negative age parameter and returning depth (in metres).
    exclude_distances_to_trenches_kms : 2-tuple of float, optional
        The two distances to present-day trenches (on subducting and overriding sides, in that order) to exclude bathymetry grid points (in kms), or
        None to use built-in per-trench defaults. Default is None.
    region_plate_ids : list of int, optional
        Plate IDs of one or more plates to restrict paleobathymetry reconstruction to.
        Defaults to global.
    anchor_plate_id : int, optional
        The anchor plate id used when reconstructing paleobathymetry grid points. Defaults to zero.
    output_positive_bathymetry_below_sea_level : bool, optional
        Whether to output positive bathymetry values below sea level (the same as backtracked water depths at a drill site).
        However topography/bathymetry grids typically have negative values below sea level (and positive above).
        So the default (``False``) matches typical topography/bathymetry grids (ie, outputs negative bathymetry values below sea level).
    output_xyz : bool, optional
        Whether to also create a GMT xyz file (with ".xyz" extension) for each output paleo bathymetry grid.
        Each row of each xyz file contains "longitude latitude bathymetry".
        Default is to only create grid files (no xyz).
    use_all_cpus : bool or int, optional
        If ``False`` (or zero) then use a single CPU.
        If ``True`` then distribute CPU processing across all CPUs (cores).
        If a positive integer then use that many CPUs (cores).
        Defaults to ``False`` (single CPU).
    
    Raises
    ------
    ValueError
        If ``oldest_time`` is negative (if specified) or if ``time_increment`` is not positive.

    Notes
    -----
    The output paleo bathymetry grids have negative values below sea level by default.
    Note that this is the inverse of water depth (which is positive below sea level).

    Any input points outside the masked region of the total sediment thickness grid are ignored (since bathymetry relies on sediment decompaction over time).
        
    .. versionadded:: 1.4

    .. versionchanged:: 1.5
        ``oldest_time`` no longer needs to be specified (defaults to oldest of ocean crust ages and continental rift start ages of grid points).
    """

    # Generate a global latitude/longitude grid of points (with the requested grid spacing).
    input_points = generate_lon_lat_points(grid_spacing_degrees)
    
    # Generate reconstructed paleo bathymetry points over the requested time period.
    paleo_bathymetry = reconstruct_backtrack_bathymetry(
        input_points,
        oldest_time,
        time_increment,
        lithology_filenames,
        age_grid_filename,
        topography_filename,
        total_sediment_thickness_filename,
        crustal_thickness_filename,
        rotation_filenames,
        static_polygon_filename,
        dynamic_topography_model,
        sea_level_model,
        lithology_name,
        ocean_age_to_depth_model,
        exclude_distances_to_trenches_kms,
        region_plate_ids,
        anchor_plate_id,
        output_positive_bathymetry_below_sea_level,
        use_all_cpus)
    
    # Generate a NetCDF grid for each reconstructed time of the paleobathmetry.
    write_bathymetry_grids(
        paleo_bathymetry,
        grid_spacing_degrees,
        output_file_prefix,
        output_xyz,
        use_all_cpus)


########################
# Command-line parsing #
########################

def main():
    
    __description__ = """Generate paleo bathymetry grids through time.
    
    NOTE: Separate the positional and optional arguments with '--' (workaround for bug in argparse module).
    For example...

    python -m pybacktrack.paleo_bathymetry_cli ... --use_all_cpus -g 0.2 -- 240 paleo_bathymetry_12m
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
    
    # Basically an argparse.RawDescriptionHelpFormatter that will also preserve formatting of
    # argument help messages if they start with "R|".
    class PreserveHelpFormatter(argparse.RawDescriptionHelpFormatter):
        def _split_lines(self, text, width):
            if text.startswith('R|'):
                return text[2:].splitlines()
            return super(PreserveHelpFormatter, self)._split_lines(text, width)

    ocean_age_to_depth_model_name_dict = dict((model, model_name) for model, model_name, _ in age_to_depth.ALL_MODELS)
    default_ocean_age_to_depth_model_name = ocean_age_to_depth_model_name_dict[age_to_depth.DEFAULT_MODEL]
    
    #
    # Gather command-line options.
    #
    
    # The command-line parser.
    parser = argparse.ArgumentParser(description=__description__, formatter_class=PreserveHelpFormatter)
    
    parser.add_argument('--version', action='version', version=pybacktrack.version.__version__)
    
    parser.add_argument('-i', '--time_increment', type=parse_positive_float, default=1,
            help='The time increment in My. Value must be positive (and can be non-integral). Defaults to 1 My.')
        
    grid_spacing_argument_group = parser.add_mutually_exclusive_group()
    grid_spacing_argument_group.add_argument('-g', '--grid_spacing_degrees', type=float,
            help='The grid spacing (in degrees) of sample points in lon/lat space. '
                 'Defaults to {0} degrees.'.format(DEFAULT_GRID_SPACING_DEGREES))
    grid_spacing_argument_group.add_argument('-gm', '--grid_spacing_minutes', type=float,
            help='The grid spacing (in minutes) of sample points in lon/lat space. '
                 'Defaults to {0} minutes.'.format(DEFAULT_GRID_SPACING_MINUTES))
    
    parser.add_argument('--anchor', type=parse_positive_integer, default=0,
            dest='anchor_plate_id',
            help='Anchor plate id used when reconstructing paleobathymetry grid points. Defaults to zero.')
    
    parser.add_argument('--region', type=parse_positive_integer, nargs='+',
            metavar='PLATE_ID',
            dest='region_plate_ids',
            help='Plate IDs of one or more plates to restrict paleobathymetry reconstruction to. Defaults to global.')
    
    parser.add_argument('-et', '--exclude_distances_to_trenches_kms', type=parse_non_negative_float, nargs=2,
            metavar=('SUBDUCTING_DISTANCE_KMS', 'OVERRIDING_DISTANCE_KMS'),
            help='The two distances to present-day trenches (on subducting and overriding sides, in that order) '
                 'to exclude bathymetry grid points (in kms). Defaults to using built-in per-trench defaults.')
    
    # Allow user to override the default lithology filename, and also specify bundled lithologies.
    parser.add_argument(
        '-l', '--lithology_filenames', nargs='+', action=ArgParseLithologyAction,
        metavar='lithology_filename',
        default=[pybacktrack.bundle_data.DEFAULT_BUNDLE_LITHOLOGY_FILENAME],
        help='R|Optional lithology filenames used to lookup density, surface porosity and porosity decay.\n'
             'If more than one file provided then conflicting lithologies in latter files override those in former files.\n'
             'You can also choose built-in (bundled) lithologies (in any order) - choices include {}\n'
             '(see {}).\n'
             'Defaults to "{}" if nothing specified.'
             .format(
                 ', '.join('"{0}"'.format(short_name) for short_name in BUNDLED_LITHOLOGY_SHORT_NAMES),
                 pybacktrack.bundle_data.BUNDLE_LITHOLOGY_DOC_URL,
                 DEFAULT_BUNDLED_LITHOLOGY_SHORT_NAME))
    
    parser.add_argument(
        '-b', '--lithology_name', type=str, default=DEFAULT_LITHOLOGY_NAME,
        metavar='lithology_name',
        help='Lithology name of the all sediment (must be present in lithologies file). '
             'The total sediment thickness at all sediment locations consists of a single lithology (in this workflow). '
             'Defaults to "{0}".'.format(DEFAULT_LITHOLOGY_NAME))
    
    parser.add_argument(
        '-m', '--ocean_age_to_depth_model', nargs='+', action=age_to_depth.ArgParseAgeModelAction,
        metavar='model_parameter',
        default=age_to_depth.DEFAULT_MODEL,
        help='R|The oceanic model used to convert age to depth.\n'
             'It can be the name of an in-built oceanic age model: {} (defaults to {})\n'
             '(see {}).\n'
             'Or it can be an age model filename followed by two integers representing the age and depth column indices,\n'
             'where the file should contain at least two columns (one containing the age and the other the depth).'
             .format(
                 ', '.join(model_name for _, model_name, _ in age_to_depth.ALL_MODELS),
                 default_ocean_age_to_depth_model_name,
                 pybacktrack.bundle_data.BUNDLE_AGE_TO_DEPTH_MODEL_DOC_URL))
    
    # Allow user to override default age grid filename (if they don't want the one in the bundled data).
    parser.add_argument(
        '-a', '--age_grid_filename', type=argparse_unicode,
        default=pybacktrack.bundle_data.BUNDLE_AGE_GRID_FILENAME,
        metavar='age_grid_filename',
        help='R|Optional age grid filename used to obtain age of oceanic crust.\n'
             'Crust is oceanic at locations inside masked age grid region, and continental outside.\n'
             'Defaults to the bundled data file "{}"\n'
             '(see {}).'.format(pybacktrack.bundle_data.BUNDLE_AGE_GRID_FILENAME, pybacktrack.bundle_data.BUNDLE_AGE_GRID_DOC_URL))
    
    # Allow user to override default total sediment thickness filename (if they don't want the one in the bundled data).
    parser.add_argument(
        '-s', '--total_sediment_thickness_filename', type=argparse_unicode,
        default=pybacktrack.bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,
        metavar='total_sediment_thickness_filename',
        help='R|Optional filename used to obtain total sediment thickness grid.\n'
             'Defaults to the bundled data file "{}"\n'
             '(see {}).'
             .format(
                    pybacktrack.bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,
                    pybacktrack.bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_DOC_URL))
    
    # Allow user to override default crustal thickness filename (if they don't want the one in the bundled data).
    parser.add_argument(
        '-k', '--crustal_thickness_filename', type=argparse_unicode,
        default=pybacktrack.bundle_data.BUNDLE_CRUSTAL_THICKNESS_FILENAME,
        metavar='crustal_thickness_filename',
        help='R|Optional filename used to obtain crustal thickness grid.\n'
             'Defaults to the bundled data file "{}"\n'
             '(see {}).'
             .format(
                    pybacktrack.bundle_data.BUNDLE_CRUSTAL_THICKNESS_FILENAME,
                    pybacktrack.bundle_data.BUNDLE_CRUSTAL_THICKNESS_DOC_URL))
    
    # Allow user to override default topography filename (if they don't want the one in the bundled data).
    parser.add_argument(
        '-t', '--topography_filename', type=argparse_unicode,
        default=pybacktrack.bundle_data.BUNDLE_TOPOGRAPHY_FILENAME,
        metavar='topography_filename',
        help='R|Optional topography grid filename used to obtain water depth.\n'
             'Defaults to the bundled data file "{}"\n'
             '(see {}).'.format(pybacktrack.bundle_data.BUNDLE_TOPOGRAPHY_FILENAME, pybacktrack.bundle_data.BUNDLE_TOPOGRAPHY_DOC_URL))
    
    # Allow user to override default rotation filenames (used to reconstruct sediment-deposited crust).
    #
    # Defaults to built-in global rotations associated with topological model used to generate built-in rift start/end time grids.
    parser.add_argument(
        '-r', '--rotation_filenames', type=str, nargs='+',
        default=pybacktrack.bundle_data.BUNDLE_RECONSTRUCTION_ROTATION_FILENAMES,
        metavar='rotation_filename',
        help='R|One or more rotation files (to reconstruct sediment-deposited crust).\n'
             'Defaults to the bundled global rotations (associated with topological model used to generate built-in rift start/end time grids):\n'
             '{}\n'
             '(see {}).'
             .format(pybacktrack.bundle_data.BUNDLE_RECONSTRUCTION_ROTATION_FILENAMES, pybacktrack.bundle_data.BUNDLE_PALEOBATHYMETRY_GRIDDING_DOC_URL))
    
    # Allow user to override default static polygon filename (to assign plate IDs to points on sediment-deposited crust).
    #
    # Defaults to built-in static polygons associated with topological model used to generate built-in rift start/end time grids.
    parser.add_argument(
        '-p', '--static_polygon_filename', type=str,
        default=pybacktrack.bundle_data.BUNDLE_RECONSTRUCTION_STATIC_POLYGON_FILENAME,
        metavar='static_polygon_filename',
        help='R|File containing static polygons (to assign plate IDs to points on sediment-deposited crust).\n'
             'Defaults to the bundled static polygons (associated with topological model used to generate built-in rift start/end time grids):\n'
             '"{}"\n'
             '(see {}).'
             .format(pybacktrack.bundle_data.BUNDLE_RECONSTRUCTION_STATIC_POLYGON_FILENAME, pybacktrack.bundle_data.BUNDLE_PALEOBATHYMETRY_GRIDDING_DOC_URL))
    
    # Can optionally specify dynamic topography as a triplet of filenames or a model name (if using bundled data) but not both.
    dynamic_topography_argument_group = parser.add_mutually_exclusive_group()
    dynamic_topography_argument_group.add_argument(
        '-ym', '--bundle_dynamic_topography_model', type=str,
        metavar='bundle_dynamic_topography_model',
        help='R|Optional dynamic topography through time.\n'
             'If no model specified then dynamic topography is ignored.\n'
             'Can be used both for oceanic floor and continental passive margin.\n'
             'Choices include {}\n'
             '(see {}).'
             .format(
                    ', '.join(pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_NAMES),
                    pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS_DOC_URL))
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
        help='R|Optional sea level model used to obtain sea level (relative to present-day) over time.\n'
             'If no model (or filename) is specified then sea level is ignored.\n'
             'Choices include {}\n'
             '(see {}).'
             .format(
                    ', '.join(pybacktrack.bundle_data.BUNDLE_SEA_LEVEL_MODEL_NAMES),
                    pybacktrack.bundle_data.BUNDLE_SEA_LEVEL_MODELS_DOC_URL))
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
        '--output_xyz', action='store_true',
        help='Also create a GMT xyz file (with ".xyz" extension) for each output paleo bathymetry grid. '
             'Each row of each xyz file contains "longitude latitude bathymetry". '
             'Default is to only create grid files (no xyz).')
    
    parser.add_argument(
        '--use_all_cpus', nargs='?', type=parse_positive_integer,
        const=True, default=False,
        metavar='NUM_CPUS',
        help='Use all CPUs (cores), or if an optional integer is also specified then use the specified number of CPUs. '
             'Defaults to using a single CPU.')

    parser.add_argument('oldest_time', nargs='?', type=parse_non_negative_float,
            metavar='oldest_time',
            help='Output is generated from present day back to the oldest time (in Ma). Value must not be negative. '
                 'If not specified then defaults to oldest of ocean crust ages and continental rift start ages of grid points.')
    
    parser.add_argument(
        'output_file_prefix', type=argparse_unicode,
        metavar='output_file_prefix',
        help='The prefix of the output paleo bathymetry grid filenames over time, with "_<time>.nc" appended.')
    
    #
    # Parse command-line options.
    #
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
    
    # Generate reconstructed paleo bathymetry grids over the requested time period.
    paleo_bathymetry = reconstruct_backtrack_bathymetry_and_write_grids(
        args.output_file_prefix,
        grid_spacing_degrees,
        args.oldest_time,
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
        args.region_plate_ids,
        args.anchor_plate_id,
        args.output_positive_bathymetry_below_sea_level,
        args.output_xyz,
        args.use_all_cpus)


if __name__ == '__main__':

    # User should not be using this module as a script. They should use 'paleo_bathymetry' when importing and 'paleo_bathymetry_cli' as a script.
    #raise RuntimeError("Use 'python -m pybacktrack.paleo_bathymetry_cli ...', instead of 'python -m pybacktrack.paleo_bathymetry ...'.")
    print("ERROR: Use 'python -m pybacktrack.paleo_bathymetry_cli ...', instead of 'python -m pybacktrack.paleo_bathymetry ...'.", file=sys.stderr)
    sys.exit(1)

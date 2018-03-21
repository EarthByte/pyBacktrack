
#
# Copyright (C) 2017 The University of Sydney, Australia
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

"""Find decompacted total sediment thickness and water depth through time.

:func:`backtrack` finds decompacted total sediment thickness and water depth for each age in a well.

:func:`write_decompacted_wells` writes decompacted parameters as columns in a text file.

:func:`backtrack_and_write_decompacted` both backtracks well and writes decompacted data.
"""


from __future__ import print_function
import argparse
import codecs
import math
import os.path
import pybacktrack.age_to_depth as age_to_depth
from pybacktrack.lithology import read_lithologies_file
import pybacktrack.rifting as rifting
from pybacktrack.sea_level import SeaLevel
from pybacktrack.util.call_system_command import call_system_command
import pybacktrack.version
from pybacktrack.well import read_well_file, write_well_file, write_well_metadata
import pygplates
import sys


# The name of the lithology of the stratigraphic unit at the base of the well to use by default
# (if no 'base_lithology_name' parameter passed to function).
DEFAULT_BASE_LITHOLOGY_NAME = 'Shale'

# Density in kg/m3.
DENSITY_WATER = 1030.0
DENSITY_CRUST = 2800.0
DENSITY_MANTLE = 3330.0

# Warn the user if the rifting stretching factor (beta) estimate results in a
# tectonic subsidence inaccuracy (at present day) exceeding this amount (in metres)...
MAX_TECTONIC_SUBSIDENCE_RIFTING_RESIDUAL_ERROR = 100


def backtrack(
        well_filename,
        lithologies_filename,
        age_grid_filename,
        topography_filename,
        total_sediment_thickness_filename,
        crustal_thickness_filename,
        dynamic_topography_model_info=None,
        sea_level_filename=None,
        base_lithology_name=DEFAULT_BASE_LITHOLOGY_NAME,
        ocean_age_to_depth_model=age_to_depth.DEFAULT_MODEL,
        rifting_period=None,
        well_location=None,
        well_bottom_age_column=0,
        well_bottom_depth_column=1,
        well_lithology_column=2):
    """Finds decompacted total sediment thickness and water depth for each age in a well.
    
    Parameters
    ----------
    well_filename : string
        Name of well text file.
    lithologies_filename : string
        Name of lithologies text file.
    age_grid_filename : string
        Age grid filename.
        Used to obtain age of seafloor at well location.
    topography_filename : string
        Topography filename.
        Used to obtain water depth at well location.
    total_sediment_thickness_filename : string
        Total sediment thickness filename.
        Used to obtain total sediment thickness at well location.
    crustal_thickness_filename : string
        Crustal thickness filename.
        Used to obtain crustal thickness at well location.
    dynamic_topography_model_info : tuple, optional
        Represents a time-dependent dynamic topography raster grid.
        Currently only used for oceanic floor (ie, well location inside age grid)
        it is not used if well is on continental crust (passive margin).
        This is a text file containing a list of dynamic topography grids and associated times.
        The tuple argument contains the three elements (dynamic topography list filename, static polygon filename, rotation filenames).
        The first tuple element is the filename of file containing list of dynamic topography grids (and associated times).
        Each row in this list file should contain two columns.
        First column containing filename (relative to list file) of a dynamic topography grid at a particular time.
        Second column containing associated time (in Ma).
        The second tuple element is the filename of file containing static polygons associated with dynamic topography model.
        This is used to assign plate ID to well location so it can be reconstructed.
        The third tuple element is the filename of the rotation file associated with model.
        Only the rotation file for static continents/oceans is needed (ie, deformation rotations not needed).
    sea_level_filename : string, optional
        Sea level filename.
        Used to obtain sea levels relative to present day.
    base_lithology_name : string, optional
        Lithology name of the stratigraphic unit at the base of the well (must be present in lithologies file).
        The stratigraphic units in the well might not record the full depth of sedimentation.
        The base unit covers the remaining depth from bottom of well to the total sediment thickness.
        Defaults to 'Shale'.
    ocean_age_to_depth_model : {'age_to_depth.MODEL_GDH1', 'age_to_depth.MODEL_CROSBY_2007'}, optional
        The model to use when converting ocean age to depth at well location
        (if on ocean floor - not used for continental passive margin).
    rifting_period : tuple, optional
        Optional time period of rifting (if on continental passive margin - not used for oceanic floor).
        If specified then should be a 2-tuple (rift_start_age, rift_end_age) where rift_start_age can be None
        (in which case rifting is considered instantaneous from a stretching point-of-view, not thermal).
        If specified then overrides value in well file.
        If well is on continental passive margin then at least rift end age should be specified
        either here or in well file.
    well_location : tuple, optional
        Optional location of well.
        If not provided then is extracted from the `well_filename` file.
        If specified then overrides value in well file.
        If specified then must be a 2-tuple (longitude, latitude) in degrees.
    well_bottom_age_column : int, optional
        The column of well file containing bottom age. Defaults to 0.
    well_bottom_depth_column : int, optional
        The column of well file containing bottom depth. Defaults to 1.
    well_lithology_column : int, optional
        The column of well file containing lithology(s). Defaults to 2.
    
    Returns
    -------
    :class:`Well`
        The well read from `well_filename`.
        It may also be ammended with a base stratigraphic unit from the bottom of the well to basement.
    list of :class:`Well.DecompactedWell`
        The decompacted wells associated with the well.
    
    Raises
    ------
    ValueError
        If `lithology_column` is not the largest column number (must be last column).
    ValueError
        If `well_location` is not specified *and* the well location was not extracted from the well file.
    
    Notes
    -----
    Each attribute to read from well file (eg, bottom_age, bottom_depth, etc) has a column index to direct
    which column it should be read from.
    
    The tectonic subsidence at each age (of decompacted wells) is added as a `tectonic_subsidence` attribute
    to each decompacted well returned.
    """
    
    # Read the lithologies from a text file.
    lithologies = read_lithologies_file(lithologies_filename)
    
    # Read the well from a file.
    well = load_well(
        well_filename,
        lithologies,
        rifting_period,
        well_location,
        well_bottom_age_column,
        well_bottom_depth_column,
        well_lithology_column)
    
    # There should be at least one stratigraphic unit - if not then return empty decompaction list.
    if not well.stratigraphic_units:
        return []
    
    # Sample age grid at well location.
    age = sample_grid(well.longitude, well.latitude, age_grid_filename)
    # If sampled outside age grid then well is on continental crust near a passive margin.
    # In this case we'll using passive margin rifting to calculate tectonic subsidence instead of
    # ocean floor age-to-depth models.
    if math.isnan(age):
        age = None
    
    # If well is on continental passive margin then rift end age needs to be
    # specified by user or obtained from well file.
    if age is None:
        if well.rift_end_age is None:
            raise ValueError('Well is on continental passive margin but rift end age was '
                             'not extracted from well file and was not specified by user. '
                             'Either add RiftEndAge to the well file or specify rift end age on command-line.')
    
    # Sample topography grid at well location.
    present_day_topography = sample_grid(well.longitude, well.latitude, topography_filename)
    # If sampled outside topography grid then set topography to zero.
    # Shouldn't happen since topography grid is not masked anywhere.
    if math.isnan(present_day_topography):
        present_day_topography = 0.0
    
    # Topography is negative in ocean but water depth is positive.
    present_day_water_depth = -present_day_topography
    # Clamp water depth so it's below sea level (ie, must be >= 0).
    present_day_water_depth = max(0, present_day_water_depth)
    
    # Sample total sediment thickness grid at well location.
    present_day_total_sediment_thickness = sample_grid(well.longitude, well.latitude, total_sediment_thickness_filename)
    # If sampled outside total sediment thickness grid then set total sediment thickness to zero.
    # This will result in a base stratigraphic layer not getting added underneath the well to fill
    # in the total sediment thickness (but the well is probably close to the coastlines where it's shallow
    # and hence probably includes all layers in the total sediment thickness anyway).
    if math.isnan(present_day_total_sediment_thickness):
        present_day_total_sediment_thickness = 0.0
    
    # Sample crustal thickness grid at well location.
    present_day_crustal_thickness = sample_grid(well.longitude, well.latitude, crustal_thickness_filename)
    # If sampled outside crustal thickness then set crustal thickness to zero.
    # Shouldn't happen since crustal thickness grid is not masked anywhere.
    if math.isnan(present_day_crustal_thickness):
        present_day_crustal_thickness = 0.0
    
    # Add a base stratigraphic unit from the bottom of the well to basement if the stratigraphic units
    # in the well do not record the total sediment thickness.
    add_stratigraphic_unit_to_basement(
        well,
        present_day_total_sediment_thickness,
        lithologies,
        base_lithology_name,
        age)
    
    # Each decompacted well (in returned list) represents decompaction at the age of a stratigraphic unit in the well.
    decompacted_wells = well.decompact()
    
    # Calculate sea level (relative to present day) for each decompaction age (unpacking of stratigraphic units)
    # that is an average over the decompacted surface layer's period of deposition.
    if sea_level_filename:
        add_sea_level(
            well,
            decompacted_wells,
            # Create sea level object for integrating sea level over time periods...
            SeaLevel(sea_level_filename))
    
    # Isostatic correction for total sediment thickness.
    #
    # For ocean floor we could use a simple formula using only total sediment thickness based on Sykes et al. 1996
    # (although we'd still need something for continental crust).
    # However the first decompaction age of the well contains an isostatic correction based on its lithology units which
    # is more accurate so we'll use that instead. It also means the decompacted water depth at age zero (ie, top of well)
    # will match the water depth we obtained from topography above.
    #
    # present_day_total_sediment_isostatic_correction = calc_ocean_total_sediment_thickness_isostatic_correction(present_day_total_sediment_thickness)
    present_day_total_sediment_isostatic_correction = decompacted_wells[0].get_sediment_isostatic_correction()
    
    # Unload the sediment to get unloaded water depth.
    # Note that sea level variations don't apply here because they are zero at present day.
    present_day_tectonic_subsidence = present_day_water_depth + present_day_total_sediment_isostatic_correction
    
    # Create time-dependent grid object for sampling dynamic topography (if requested).
    if dynamic_topography_model_info:
        dynamic_topography_list_filename, dynamic_topography_static_polygon_filename, dynamic_topography_rotation_filenames = dynamic_topography_model_info
        dynamic_topography = DynamicTopography(
            dynamic_topography_list_filename, dynamic_topography_static_polygon_filename, dynamic_topography_rotation_filenames,
            well.longitude, well.latitude, age)
    else:
        dynamic_topography = None
    
    # Calculate tectonic subsidence (unloaded water depth) at each decompaction age (unpacking of stratigraphic units).
    # The tectonic subsidence curve can later be used to calculate paleo (loaded) water depths.
    if age is not None:
        # Oceanic crust.
        add_oceanic_tectonic_subsidence(
            well,
            decompacted_wells,
            present_day_tectonic_subsidence,
            ocean_age_to_depth_model,
            age,
            dynamic_topography)
    else:
        # Continental crust.
        add_continental_tectonic_subsidence(
            well,
            decompacted_wells,
            present_day_tectonic_subsidence,
            present_day_crustal_thickness,
            dynamic_topography)
    
    return well, decompacted_wells
    
    
def load_well(
        well_filename,
        lithologies,
        rifting_period=None,
        well_location=None,
        well_bottom_age_column=0,
        well_bottom_depth_column=1,
        well_lithology_column=2):
    """
    Read the well file and its backtracking metadata.
    
    well_filename: Name of well text file.
    
    lithologies: a dict mapping lithology names to lithology.Lithology objects.
    
    rifting_period: Optional time period of rifting (if on continental passive margin - not used for oceanic floor).
                    If specified then should be a 2-tuple (rift_start_age, rift_end_age) where rift_start_age can be None
                    (in which case rifting is considered instantaneous from a stretching point-of-view, not thermal).
                    If specified then overrides value in well file.
                    If well is on continental passive margin then at least rift end age should be specified
                    either here or in well file.
    
    well_location: Optional location of well. If not provided then is extracted from 'well_filename' file.
                   If specified then overrides value in well file.
                   If specified then must be a 2-tuple (longitude, latitude) in degrees.
    
    <well columns>: Each column attribute to read from well file (bottom_age, bottom_depth and lithology(s))
                    has a column index to direct which column it should be read from.
    
    Returns: Well
    
    The tectonic subsidence at each age (of decompacted wells) is added as a 'tectonic_subsidence' attribute
    to each decompacted well returned.
    
    Each attribute to read from well file (eg, bottom_age, bottom_depth, etc) has a column index to direct
    which column it should be read from.
    
    Raises ValueError if 'lithology_column' is not the largest column number (must be last column).
    Raises ValueError if 'well_location' is not specified *and* the well location was not extracted from the well file.
    """
    
    def read_longitude(string):
        longitude = float(string)
        if longitude < -360 or longitude > 360:
            raise ValueError('Longitude {0} is not a number in range [-360, 360]'.format(longitude))
        return longitude
    
    def read_latitude(string):
        latitude = float(string)
        if latitude < -90 or latitude > 90:
            raise ValueError('Latitude {0} is not a number in range [-90, 90]'.format(latitude))
        return latitude
    
    def read_age(string):
        age = float(string)
        if age < 0:
            raise ValueError('Age {0} cannot be negative'.format(age))
        return age
    
    def read_depth(string):
        depth = float(string)
        if depth < 0:
            raise ValueError('Depth {0} cannot be negative'.format(depth))
        return depth
    
    # Read the well from a text file.
    well = read_well_file(
        well_filename,
        lithologies,
        well_bottom_age_column,
        well_bottom_depth_column,
        well_lithology_column,
        # Attributes to read from file metadata into returned well object...
        well_attributes={
            'SiteLongitude': ('longitude', read_longitude),
            'SiteLatitude': ('latitude', read_latitude),
            'RiftStartAge': ('rift_start_age', read_age),
            'RiftEndAge': ('rift_end_age', read_age),
            'WaterDepth': ('water_depth', read_depth)})
    
    # If the well location was specified then override the location read from the well file (if a location was read).
    if well_location is not None:
        well.longitude, well.latitude = well_location
    # Needs to be specified by user or obtained from well file.
    if well.longitude is None or well.latitude is None:
        raise ValueError('Well location was not extracted from well file and was not specified by user.')
    
    # If the rifting period was specified then override the value read from the well file (if read).
    if rifting_period is not None:
        rift_start_age, rift_end_age = rifting_period
        if rift_start_age is not None:
            well.rift_start_age = rift_start_age
        if rift_end_age is not None:
            well.rift_end_age = rift_end_age
    
    return well


def add_stratigraphic_unit_to_basement(
        well,
        present_day_total_sediment_thickness,
        lithologies,
        base_lithology_name,
        age=None):
    """
    Add a base stratigraphic unit from the bottom of the well to basement if the stratigraphic units
    in the well do not record the total sediment thickness.
    
    age: The ocean basement age at well location (if in age grid), otherwise None for continental passive margins.
    """
    
    # The well depth/thickness is the bottom depth of the deepest stratigraphic unit (they are sorted from youngest to oldest).
    deepest_well_unit = well.stratigraphic_units[-1]
    well_sediment_thickness = deepest_well_unit.bottom_depth
    if well_sediment_thickness < present_day_total_sediment_thickness:
        base_unit_thickness = present_day_total_sediment_thickness - well_sediment_thickness
        base_unit_top_depth = well_sediment_thickness
        base_unit_bottom_depth = base_unit_top_depth + base_unit_thickness
        
        # Age at the top of the base unit (age at which deposition ended for base unit) is
        # the bottom age of the unit above it (deepest unit of well).
        base_unit_top_age = deepest_well_unit.bottom_age
        
        # Age at the bottom of the base unit represents the basement age which is:
        # - in the age grid for oceanic crust, or
        # - the rift start age for continental crust.
        if age is not None:
            base_unit_bottom_age = age
        else:
            # If we have a rift start time then use it, otherwise use the rift end time.
            # Presumably sediment started filling when rifting (and hence subsidence) began.
            if well.rift_start_age is not None:
                base_unit_bottom_age = well.rift_start_age
            else:
                base_unit_bottom_age = well.rift_end_age
        # If it happens to be younger than the top age then we just set it to the top age.
        base_unit_bottom_age = max(base_unit_bottom_age, base_unit_top_age)
        
        # One lithology component comprising the full fraction.
        base_unit_lithogy_components = [(base_lithology_name, 1.0)]
        
        well.add_compacted_unit(
            base_unit_top_age, base_unit_bottom_age,
            base_unit_top_depth, base_unit_bottom_depth,
            base_unit_lithogy_components, lithologies)
        
    elif well_sediment_thickness - present_day_total_sediment_thickness > 0.01 * well_sediment_thickness:
        # Warn the user that the well thickness exceeds the total sediment thickness - requested by Dietmar.
        # This can happen as a result of the large uncertainties in the sediment thickness grid.
        print('WARNING: Well thickness {0} is larger than the total sediment thickness grid {1} at well location ({2}, {3}). '
              'Ignoring total sediment thickness grid. '.format(
                  well_sediment_thickness, present_day_total_sediment_thickness, well.longitude, well.latitude),
              file=sys.stderr)


def add_sea_level(
        well,
        decompacted_wells,
        sea_level):
    """
    Calculate average sea levels (relative to present day) for the stratigraphic layers in a well.
    
    The sea level (relative to present day) is integrated over the period of deposition of each
    stratigraphic layer (in decompacted wells) and added as a 'sea_level' attribute to each decompacted well.
    """
    
    for decompacted_well in decompacted_wells:
        decompacted_well.sea_level = sea_level.get_average_level(
            decompacted_well.surface_unit.bottom_age,
            decompacted_well.surface_unit.top_age)


def add_oceanic_tectonic_subsidence(
        well,
        decompacted_wells,
        present_day_tectonic_subsidence,
        ocean_age_to_depth_model,
        age,
        dynamic_topography=None):
    """
    Calculate tectonic subsidence for a well on oceanic crust (inside age grid).
    
    The tectonic subsidence at each age (of decompacted wells) is added as a 'tectonic_subsidence' attribute
    to each decompacted well.
    """
    
    # Present-day tectonic subsidence calculated from age-to-depth model.
    present_day_tectonic_subsidence_from_model = age_to_depth.age_to_depth(age, ocean_age_to_depth_model)
    
    # NOT NEEDED: Initially the idea was to determine contribution of dynamic topography to
    # present-day subsidence (compared to contribution of anomalous ocean crustal thickness) and
    # use the same scale ratio to determine the contribution of dynamic topography at paleo times.
    # However now we just use a constant offset and then add in the difference of dynamic topography
    # from its present-day value.
    #
    #
    # # Regular crustal thickness (in metres) of oceanic crust unaffected by plumes.
    # OCEAN_CRUSTAL_THICKNESS = 7000
    # # Uncertainty in regular crustal thickness (in metres) of oceanic crust unaffected by plumes.
    # OCEAN_CRUSTAL_THICKNESS_UNCERTAINTY = 500
    # # Contribution to present-day tectonic subsidence from anomalous thickness (if present).
    # # If ocean crust thickness deviates too far from normal then we'll need to account for its effect
    # # on the age-to-depth model (which assumes normal crustal thickness).
    # if math.fabs(present_day_crustal_thickness - OCEAN_CRUSTAL_THICKNESS) > OCEAN_CRUSTAL_THICKNESS_UNCERTAINTY:
    #     # Contribution will be negative if crust is thicker that normal (positive if thinner) implying the
    #     # age-to-depth modelled subsidence should be reduced (increased) to estimate actual subsidence.
    #     present_day_tectonic_subsidence_from_model += (
    #             (OCEAN_CRUSTAL_THICKNESS - present_day_crustal_thickness) *
    #             (DENSITY_MANTLE - DENSITY_CRUST) / (DENSITY_MANTLE - DENSITY_WATER))
    
    # There will be a difference between unloaded water depth and subsidence based on age-to-depth model.
    # Assume this offset is constant for all ages and use it to adjust the subsidence obtained from age-to-depth model for other ages.
    tectonic_subsidence_model_adjustment = present_day_tectonic_subsidence - present_day_tectonic_subsidence_from_model
    
    # Get present-day dynamic topography (if requested).
    if dynamic_topography:
        dynamic_topography_at_present_day = dynamic_topography.sample(0.0)
        if math.isnan(dynamic_topography_at_present_day):
            # Warn the user if the dynamic topography model does not provide a value at present day.
            # This shouldn't happen since mantle-frame grids should provide global coverage.
            print(u'WARNING: Dynamic topography model "{0}" does not cover well location ({1}, {2}) at present day. '
                  'Ignoring dynamic topography.'.format(
                      dynamic_topography.grids.grid_list_filename, well.longitude, well.latitude),
                  file=sys.stderr)
            
            # Stop using dynamic topography.
            dynamic_topography = None
    
    for decompacted_well in decompacted_wells:
        # The current decompaction time (age of the surface of the current decompacted column of the well).
        decompaction_time = decompacted_well.get_age()
        
        # Age of the ocean basin at well location when it's decompacted to the current decompaction age.
        paleo_age_of_crust_at_decompaction_time = max(0, age - decompaction_time)
        
        # Use age-to-depth model to lookup depth given the age.
        tectonic_subsidence_from_model = age_to_depth.age_to_depth(paleo_age_of_crust_at_decompaction_time, ocean_age_to_depth_model)
        
        # We add in the constant offset between the age-to-depth model (at age of well) and unloaded water depth at present day.
        decompacted_well.tectonic_subsidence = tectonic_subsidence_from_model + tectonic_subsidence_model_adjustment
        
        # If we have dynamic topography then add in the difference at current decompaction time compared to present-day.
        if dynamic_topography:
            dynamic_topography_at_decompaction_time = dynamic_topography.sample(decompaction_time)
            if math.isnan(dynamic_topography_at_decompaction_time):
                # The decompaction time is between two dynamic topography grids where one grid (or both) is older
                # than the ocean floor at the well location and hence we cannot interpolate between the two grids.
                #
                # So we'll just sample the oldest dynamic topography grid that is younger than the ocean floor.
                dynamic_topography_at_decompaction_time, dynamic_topography_age = dynamic_topography.sample_oldest()
                if math.isnan(dynamic_topography_at_decompaction_time):
                    # This shouldn't happen because we've already obtained a value at present day (so we should at least get that here).
                    raise AssertionError(u'Internal error: Dynamic topography model "{0}" does not cover well location ({1}, {2}) at any time.'.format(
                        dynamic_topography.grids.grid_list_filename, well.longitude, well.latitude))
                
                # Warn the user if the dynamic topography model does not include the current decompaction time.
                print(u'WARNING: Dynamic topography model "{0}" does not cover, or cannot interpolate, well location ({1}, {2}) at '
                      'stratigraphic unit surface time {3}. Using dynamic topography grid at {4}.'.format(
                          dynamic_topography.grids.grid_list_filename,
                          well.longitude, well.latitude,
                          decompaction_time, dynamic_topography_age),
                      file=sys.stderr)
            
            # Dynamic topography is elevation but we want depth (subsidence) so subtract (instead of add).
            decompacted_well.tectonic_subsidence -= dynamic_topography_at_decompaction_time - dynamic_topography_at_present_day


def add_continental_tectonic_subsidence(
        well,
        decompacted_wells,
        present_day_tectonic_subsidence,
        present_day_crustal_thickness,
        dynamic_topography=None):
    """
    Calculate tectonic subsidence for a well on continental passive margin (outside age grid).
    
    The tectonic subsidence at each age (of decompacted wells) is added as a 'tectonic_subsidence' attribute
    to each decompacted well.
    """
    
    # Get dynamic topography at rift start (if requested) and remove contribution of dynamic topography
    # to subsidence at present day so we can estimate subsidence due to stretching and thermal effects only.
    if dynamic_topography:
        dynamic_topography_at_present_day = dynamic_topography.sample(0.0)
        if math.isnan(dynamic_topography_at_present_day):
            # Warn the user if the dynamic topography model does not provide a value at present day.
            # This shouldn't happen since mantle-frame grids should provide global coverage.
            print(u'WARNING: Dynamic topography model "{0}" does not cover well location ({1}, {2}) at present day. '
                  'Ignoring dynamic topography.'.format(
                      dynamic_topography.grids.grid_list_filename, well.longitude, well.latitude),
                  file=sys.stderr)
            
            # Stop using dynamic topography.
            dynamic_topography = None
        else:
            if well.rift_start_age is not None:
                rift_start_age = well.rift_start_age
            else:
                rift_start_age = well.rift_end_age
            
            dynamic_topography_at_rift_start = dynamic_topography.sample(rift_start_age)
            if math.isnan(dynamic_topography_at_rift_start):
                # This shouldn't happen because the well is in continental passive margin which should be much older than the rift start time.
                # However we'll just sample the oldest dynamic topography grid that is younger than the continental crust.
                dynamic_topography_at_rift_start, rift_start_dynamic_topography_age = dynamic_topography.sample_oldest()
                if math.isnan(dynamic_topography_at_rift_start):
                    # This shouldn't happen because we've already obtained a value at present day (so we should at least get that here).
                    raise AssertionError(u'Internal error: Dynamic topography model "{0}" does not cover well location ({1}, {2}) at any time.'.format(
                        dynamic_topography.grids.grid_list_filename, well.longitude, well.latitude))
                
                # Warn the user if the dynamic topography model does not include the rift start time.
                print(u'WARNING: Dynamic topography model "{0}" does not cover, or cannot interpolate, well location ({1}, {2}) at '
                      'rift start time {3}. Using dynamic topography grid at {4}.'.format(
                          dynamic_topography.grids.grid_list_filename,
                          well.longitude, well.latitude,
                          rift_start_age, rift_start_dynamic_topography_age),
                      file=sys.stderr)
            
            # Estimate how much of present-day subsidence is due to dynamic topography.
            # We crudely remove the relative difference of dynamic topography between rift start and present day
            # so we can see how much subsidence between those two times is due to stretching and thermal subsidence.
            # Dynamic topography is elevation but we want depth (subsidence) so add (instead of subtract).
            present_day_tectonic_subsidence += dynamic_topography_at_present_day - dynamic_topography_at_rift_start
    
    # Attempt to estimate rifting stretching factor (beta) that generates the present day tectonic subsidence.
    beta, subsidence_residual = rifting.estimate_beta(
        present_day_tectonic_subsidence,
        present_day_crustal_thickness,
        well.rift_end_age)
    
    # Initial (pre-rift) crustal thickness is beta times present day crustal thickness.
    pre_rift_crustal_thickness = beta * present_day_crustal_thickness
    
    # Warn the user if the rifting stretching factor (beta) estimate results in a
    # tectonic subsidence inaccuracy (at present day) exceeding this amount (in metres).
    #
    # This can happen if the actual subsidence is quite deep and the beta value required to achieve
    # this subsidence would be unrealistically large and result in a pre-rift crustal thickness that
    # exceeds typical lithospheric thicknesses.
    # In this case the beta factor is clamped to avoid this but, as a result, the calculated subsidence
    # is not as deep as the actual subsidence.
    if math.fabs(subsidence_residual) > MAX_TECTONIC_SUBSIDENCE_RIFTING_RESIDUAL_ERROR:
        print('WARNING: Unable to accurately estimate rifting stretching factor (beta) at well location ({0}, {1}) '
              'where unloaded subsidence is {2}, crustal thickness is {3} and rift end time is {4}. '
              'Tectonic subsidence estimates will be inaccurate on the order of {5} metres. '
              '.'.format(
                  well.longitude, well.latitude,
                  present_day_tectonic_subsidence, present_day_crustal_thickness, well.rift_end_age,
                  math.fabs(subsidence_residual)),
              file=sys.stderr)
    
    for decompacted_well in decompacted_wells:
        # The current decompaction time (age of the surface of the current decompacted column of the well).
        decompaction_time = decompacted_well.get_age()
        
        # Calculate rifting subsidence at decompaction time.
        decompacted_well.tectonic_subsidence = rifting.total_subsidence(
            beta, pre_rift_crustal_thickness, decompaction_time, well.rift_end_age, well.rift_start_age)
        
        # If we have dynamic topography then add in the difference at current decompaction time compared to rift start.
        if dynamic_topography:
            dynamic_topography_at_decompaction_time = dynamic_topography.sample(decompaction_time)
            if math.isnan(dynamic_topography_at_decompaction_time):
                # This shouldn't happen because the well is in continental passive margin which should be much older than the decompaction time.
                # However we'll just sample the oldest dynamic topography grid that is younger than the continental crust.
                dynamic_topography_at_decompaction_time, dynamic_topography_age = dynamic_topography.sample_oldest()
                if math.isnan(dynamic_topography_at_decompaction_time):
                    # This shouldn't happen because we've already obtained a value at present day (so we should at least get that here).
                    raise AssertionError(u'Internal error: Dynamic topography model "{0}" does not cover well location ({1}, {2}) at any time.'.format(
                        dynamic_topography.grids.grid_list_filename, well.longitude, well.latitude))
                
                # Warn the user if the dynamic topography model does not include the current decompaction time.
                print(u'WARNING: Dynamic topography model "{0}" does not cover, or cannot interpolate, well location ({1}, {2}) at '
                      'stratigraphic unit surface time {3}. Using dynamic topography grid at {4}.'.format(
                          dynamic_topography.grids.grid_list_filename,
                          well.longitude, well.latitude,
                          decompaction_time, dynamic_topography_age),
                      file=sys.stderr)
            
            # Account for any change in dynamic topography between rift start and current decompaction time.
            # Dynamic topography is elevation but we want depth (subsidence) so subtract (instead of add).
            decompacted_well.tectonic_subsidence -= dynamic_topography_at_decompaction_time - dynamic_topography_at_rift_start


def sample_grid(longitude, latitude, grid_filename):
    """
    Samples the grid file 'grid_filename' at the longitude/latitude location (in degrees).
    
    Returns sampled float value (which can be NaN if location is in a masked region of grid).
    """
    
    location_data = '{0} {1}\n'.format(longitude, latitude)

    # The command-line strings to execute GMT 'grdtrack'.
    grdtrack_command_line = ["gmt", "grdtrack", "-G{0}".format(grid_filename.encode(sys.getfilesystemencoding()))]
    
    # Call the system command.
    stdout_data = call_system_command(grdtrack_command_line, stdin=location_data, return_stdout=True)
    
    # GMT grdtrack returns a single line containing "longitude latitude sampled_value".
    # Note that if GMT returns "NaN" then we'll return float('nan').
    return float(stdout_data.split()[2])


class TimeDependentGrid(object):
    """
    Class to sample the time-dependent grid files.
    """
    
    def __init__(self, grid_list_filename):
        """
        Load grid filenames and associated ages from grid list file 'grid_list_filename'.
        
        Raises ValueError if:
        - not all rows contain a grid filename followed by age, or
        - there are two ages in list file with same age, or
        - list file contains fewer than two grids.
        """
        
        self.grid_list_filename = grid_list_filename
        
        self.grid_ages_and_filenames = []
        
        # Grid filenames in the list file are relative to the directory of the list file.
        grids_relative_dir = os.path.dirname(grid_list_filename)
        
        # Read list of grids and associated ages.
        #
        # Assume file is encoded as UTF8 (which includes basic 7-bit ascii).
        detect_duplicate_ages = set()
        with codecs.open(grid_list_filename, 'r', 'utf-8') as grid_list_file:
            for line_number, line in enumerate(grid_list_file):
                line_number = line_number + 1  # Make line number 1-based instead of 0-based.
                if line.strip().startswith('#'):  # Skip comments.
                    continue
                row = line.split()
                if len(row) != 2:
                    raise ValueError(u'Grid list file "{0}" does not contain two columns at line {1}.'.format(
                        grid_list_filename, line_number))
                
                grid_filename = os.path.join(grids_relative_dir, row[0])
                try:
                    grid_age = float(row[1])
                except ValueError:
                    # Re-raise error with different error message.
                    raise ValueError(u'Grid list file "{0}" does not contain a valid age (2nd column) at line {1}.'.format(
                        grid_list_filename, line_number))
                
                # Make sure same age doesn't appear twice.
                if grid_age in detect_duplicate_ages:
                    raise ValueError(u'There are two ages in grid list file "{0}" with the same value {1}.'.format(
                        grid_list_filename, grid_age))
                detect_duplicate_ages.add(grid_age)
                
                self.grid_ages_and_filenames.append((grid_age, grid_filename))
        
        # Sort in order of increasing age.
        self.grid_ages_and_filenames.sort()
        
        # Need at least two grids.
        if len(self.grid_ages_and_filenames) < 2:
            raise ValueError(u'The grid list file "{0}" contains fewer than two grids.'.format(grid_list_filename))
    
    def sample(self, longitude, latitude, time):
        """
        Samples the time-dependent grid files at 'time' and the 'longitude' / 'latitude' location (in degrees).
        
        Returns sampled float value (which can be NaN if location is in a masked region of grid).
        """
        
        # Search for ages neighbouring 'time'.
        grids_bounding_time = self.get_grids_bounding_time(time)
        # Return NaN if 'time' outside age range of grids.
        if grids_bounding_time is None:
            return float('nan')
        
        (grid_age_0, grid_filename_0), (grid_age_1, grid_filename_1) = grids_bounding_time
        
        # If 'time' matches either grid age then sample associated grid.
        if math.fabs(time - grid_age_0) < 1e-6:
            return sample_grid(longitude, latitude, grid_filename_0)
        if math.fabs(time - grid_age_1) < 1e-6:
            return sample_grid(longitude, latitude, grid_filename_1)
        
        grid_value_0 = sample_grid(longitude, latitude, grid_filename_0)
        grid_value_1 = sample_grid(longitude, latitude, grid_filename_1)
        
        # If either value is NaN then return NaN.
        if math.isnan(grid_value_0) or math.isnan(grid_value_1):
            # Need to interpolate between grids but one grid's value is invalid.
            return float('nan')
        
        # Linearly interpolate.
        # We've already verified in constructor that no two ages are the same (so divide-by-zero is not possible).
        return ((grid_age_1 - time) * grid_value_0 + (time - grid_age_0) * grid_value_1) / (grid_age_1 - grid_age_0)
    
    def get_grids_bounding_time(self, time):
        """
        Returns the two adjacent grid files (and associated times) that surround 'time' as the 2-tuple
        ((grid_age_0, grid_filename_0), (grid_age_1, grid_filename_1)).
        
        Returns None if 'time' is outside time range of grids.
        """
        
        # Search for ages neighbouring 'time'.
        first_grid_age, _ = self.grid_ages_and_filenames[0]
        if time < first_grid_age - 1e-6:
            # Time is outside grid age range ('time' is less than first grid age).
            return None
        
        for grid_index in range(1, len(self.grid_ages_and_filenames)):
            grid_age_1, grid_filename_1 = self.grid_ages_and_filenames[grid_index]
            
            if time < grid_age_1 + 1e-6:
                grid_age_0, grid_filename_0 = self.grid_ages_and_filenames[grid_index - 1]
                return (
                    (grid_age_0, grid_filename_0),
                    (grid_age_1, grid_filename_1)
                )
        
        # Time is outside grid age range ('time' is greater than last grid age).
        return None
    
    def sample_oldest_unmasked(self, longitude, latitude):
        """
        Samples the oldest grid file that gives an unmasked value (non-NaN) at the 'longitude' / 'latitude' location (in degrees).
        
        This function is useful when 'sample()' has already been called but returns NaN due to the specific time being
        older than the ocean floor at that location (or the plate frame grids were reconstructed using static polygons
        but without using age grid, resulting in static-polygon-sized chunks of the grid disappearing back through time rather
        than the more gradual disappearance due to using age grid for appearance times in reconstruction as opposed to using
        appearance times from static polygons).
        
        Returns 2-tuple (value, age) where sampled value can be still be NaN if present-day grid does not have full global coverage.
        """
        
        # Search backward until we sample a non-NaN grid value at requested location.
        for index in range(len(self.grid_ages_and_filenames) - 1, -1, -1):
            grid_age, grid_filename = self.grid_ages_and_filenames[index]
            
            grid_value = sample_grid(longitude, latitude, grid_filename)
            if not math.isnan(grid_value):
                return grid_value, grid_age
            
        # Unable to sample a non-NaN grid value, so just return NaN.
        first_grid_age = self.grid_ages_and_filenames[0][0]
        return float('nan'), first_grid_age


class DynamicTopography(object):
    """
    Class to reconstruct point location and sample the time-dependent dynamic topography *mantle* frame grid files.
    """
    
    def __init__(self, grid_list_filename, static_polygon_filename, rotation_filenames, longitude, latitude, age=None):
        """
        Load dynamic topography grid filenames and associated ages from grid list file 'grid_list_filename'.
        
        The present day location ('longitude' / 'latitude' in degrees) is also assigned a plate ID using the static polygons.
        """
        
        self.location = pygplates.PointOnSphere((latitude, longitude))
        self.age = age
        
        self.grids = TimeDependentGrid(grid_list_filename)
        self.rotation_model = pygplates.RotationModel(rotation_filenames)
        
        # Find the plate ID of the static polygon containing the location (or zero if not in any plates).
        plate_partitioner = pygplates.PlatePartitioner(static_polygon_filename, self.rotation_model)
        partitioning_plate = plate_partitioner.partition_point(self.location)
        if partitioning_plate:
            self.reconstruction_plate_id = partitioning_plate.get_feature().get_reconstruction_plate_id()
        else:
            self.reconstruction_plate_id = 0
        
        # Use the age of the containing static polygon if location is None (ie, outside age grid).
        if self.age is None:
            if partitioning_plate:
                self.age, _ = partitioning_plate.get_feature().get_valid_time()
            else:
                self.age = 0.0
    
    def sample(self, time):
        """
        Samples the time-dependent grid files at 'time' at the internal location.
        
        The location is first reconstructed to the two grid ages bounding 'time' before sampling
        the two grids (and interpolating between them).
        
        Returns NaN if:
        - 'time' is outside age range of grids, or
        - the age of either (of two) interpolated grids is older than age of the internal location.
        """
        
        # Search for the two grids bounding 'time'.
        grids_bounding_time = self.grids.get_grids_bounding_time(time)
        # Return NaN if 'time' outside age range of grids.
        if grids_bounding_time is None:
            return float('nan')
        
        (grid_age_0, grid_filename_0), (grid_age_1, grid_filename_1) = grids_bounding_time
        
        # If the age of the older grid is prior to appearance of location then return NaN.
        if grid_age_1 > self.age + 1e-6:
            return float('nan')
        
        # If 'time' matches either grid age then sample associated grid.
        if math.fabs(time - grid_age_0) < 1e-6:
            return self._sample_grid(grid_age_0, grid_filename_0)
        if math.fabs(time - grid_age_1) < 1e-6:
            return self._sample_grid(grid_age_1, grid_filename_1)
        
        # Sample both grids (we'll interpolate between them).
        grid_value_0 = self._sample_grid(grid_age_0, grid_filename_0)
        grid_value_1 = self._sample_grid(grid_age_1, grid_filename_1)
        
        # If either value is NaN then return NaN.
        # This shouldn't happen since mantle-frame grids have global coverage.
        if math.isnan(grid_value_0) or math.isnan(grid_value_1):
            return float('nan')
        
        # Linearly interpolate.
        # We already know that no two ages are the same (from TimeDependentGrid constructor).
        # So divide-by-zero is not possible.
        return ((grid_age_1 - time) * grid_value_0 + (time - grid_age_0) * grid_value_1) / (grid_age_1 - grid_age_0)
    
    def sample_oldest(self):
        """
        Samples the oldest grid file that is younger than the age-of-appearance of the internal location.
        
        This function is useful when 'sample()' has already been called but returns NaN due to the specific time having
        bounding grid times older than the ocean floor at that location.
        
        Returns 2-tuple (grid_value, grid_age).
        """
        
        # Search backward until we find a grid age younger than the age of the internal location.
        for index in range(len(self.grids.grid_ages_and_filenames) - 1, -1, -1):
            grid_age, grid_filename = self.grids.grid_ages_and_filenames[index]
            if grid_age < self.age + 1e-6:
                grid_value = self._sample_grid(grid_age, grid_filename)
                return grid_value, grid_age
        
        # Unable to sample a non-NaN grid value, so just return NaN.
        first_grid_age, _ = self.grid_ages_and_filenames[0]
        return float('nan'), first_grid_age
    
    def _sample_grid(self, grid_age, grid_filename):
        
        # Get rotation from present day to 'grid_age' using the reconstruction plate ID of the location.
        rotation = self.rotation_model.get_rotation(grid_age, self.reconstruction_plate_id)
        
        # Reconstruct location to 'grid_age'.
        reconstructed_location = rotation * self.location
        reconstructed_latitude, reconstructed_longitude = reconstructed_location.to_lat_lon()
        
        # Sample mantle frame grid (using global/module function).
        return sample_grid(reconstructed_longitude, reconstructed_latitude, grid_filename)


def calc_ocean_total_sediment_thickness_isostatic_correction(total_sediment_thickness):
    """
    Calculate isostatic correction for total (compacted) sediment thickness (in metres) for oceanic crust.
    
    This is using Sykes et al. (1996):
    'A correction for sediment load upon the ocean floor: Uniform versus varying sediment density estimations-implications for isostatic correction'
    """
    
    total_sediment_thickness_kms = total_sediment_thickness / 1000
    total_sediment_thickness_isostatic_correction_kms = (
        0.43422 * total_sediment_thickness_kms -
        0.010395 * total_sediment_thickness_kms * total_sediment_thickness_kms)
    total_sediment_thickness_isostatic_correction = 1000 * total_sediment_thickness_isostatic_correction_kms
    
    return total_sediment_thickness_isostatic_correction


# Enumerations for the 'decompacted_columns' argument in 'write_decompacted_wells()'.
COLUMN_AGE = 0
COLUMN_DECOMPACTED_THICKNESS = 1
COLUMN_DECOMPACTED_DENSITY = 2
COLUMN_TECTONIC_SUBSIDENCE = 3
COLUMN_WATER_DEPTH = 4
COLUMN_COMPACTED_THICKNESS = 5
COLUMN_LITHOLOGY = 6
COLUMN_COMPACTED_DEPTH = 7

decompacted_columns_dict = {
    'age': COLUMN_AGE,
    'decompacted_thickness': COLUMN_DECOMPACTED_THICKNESS,
    'decompacted_density': COLUMN_DECOMPACTED_DENSITY,
    'tectonic_subsidence': COLUMN_TECTONIC_SUBSIDENCE,
    'water_depth': COLUMN_WATER_DEPTH,
    'compacted_thickness': COLUMN_COMPACTED_THICKNESS,
    'lithology': COLUMN_LITHOLOGY,
    'compacted_depth': COLUMN_COMPACTED_DEPTH}
decompacted_column_names_dict = dict([(v, k) for k, v in decompacted_columns_dict.iteritems()])
decompacted_column_names = sorted(decompacted_columns_dict.keys())

default_decompacted_column_names = ['age', 'decompacted_thickness']
default_decompacted_columns = [decompacted_columns_dict[column_name] for column_name in default_decompacted_column_names]


def write_decompacted_wells(
        decompacted_wells,
        decompacted_wells_filename,
        well,
        well_attributes,
        decompacted_columns=default_decompacted_columns):
    """
    Write decompacted parameters as columns in a text file.
    
    decompacted_wells: a sequence of well.DecompactedWell.
    
    decompacted_wells_filename: name of output text file.
    
    well: The well to extract metadata from.
    
    well_attributes: Optional attributes in Well object to write to well file metadata.
                     If specified then must be a dictionary mapping each attribute name to a metadata name.
                     For example, {'longitude' : 'SiteLongitude', 'latitude' : 'SiteLatitude'}.
                     will write well.longitude (if not None) to metadata 'SiteLongitude', etc.
                     Not that the attributes must exist in 'well' (but can be set to None).
    
    decompacted_columns: Sequence of enumerations specifying which decompacted parameters to write.
                         The sequence is ordered by output column.
    
    Raises ValueError if an unrecognised value is encountered in 'decompacted_columns'.
    Raises ValueError if 'COLUMN_LITHOLOGY' is specified in 'decompacted_columns' but is not the last column.
    """
    
    # If 'COLUMN_LITHOLOGY' is specified then it must be the last column.
    if (COLUMN_LITHOLOGY in decompacted_columns and
        decompacted_columns.index(COLUMN_LITHOLOGY) != len(decompacted_columns) - 1):
        raise ValueError('Lithology columns must be the last column in the decompacted well file.')
    
    with open(decompacted_wells_filename, 'w') as file:
        
        # Write the same metadata that comes from the original well file.
        write_well_metadata(file, well, well_attributes)
        file.write('#\n')
        
        field_width = 9
        str_format_string = '{0:<{width}}'
        float_format_string = '{0:<{width}.3f}'
        
        # Write a header showing each column name.
        column_widths = []
        for column_index, decompacted_column in enumerate(decompacted_columns):
            decompacted_column_name = decompacted_column_names_dict[decompacted_column]
            
            if column_index == 0:
                column_name_format_string = '# ' + str_format_string
            else:
                column_name_format_string = ' ' + str_format_string
            
            column_width = max(field_width, len(decompacted_column_name))
            column_widths.append(column_width)
            
            file.write(column_name_format_string.format(decompacted_column_name, width=column_width))
        
        file.write('\n')
        
        # Each decompacted well (ie, at the top age of a stratigraphic unit) is written as a separate row.
        for decompacted_well in decompacted_wells:
            
            for column_index, decompacted_column in enumerate(decompacted_columns):
                if column_index == 0:
                    # Extra space to account for '#' in header.
                    column_float_format_string = '  ' + float_format_string
                    column_str_format_string = '  ' + str_format_string
                else:
                    column_float_format_string = ' ' + float_format_string
                    column_str_format_string = ' ' + str_format_string
                column_width = column_widths[column_index]
                
                if decompacted_column == COLUMN_AGE:
                    column_str = column_float_format_string.format(decompacted_well.get_age(), width=column_width)
                elif decompacted_column == COLUMN_DECOMPACTED_THICKNESS:
                    column_str = column_float_format_string.format(decompacted_well.total_decompacted_thickness, width=column_width)
                elif decompacted_column == COLUMN_DECOMPACTED_DENSITY:
                    average_decompacted_density = decompacted_well.get_average_decompacted_density()
                    column_str = column_float_format_string.format(average_decompacted_density, width=column_width)
                elif decompacted_column == COLUMN_TECTONIC_SUBSIDENCE:
                    column_str = column_float_format_string.format(decompacted_well.tectonic_subsidence, width=column_width)
                elif decompacted_column == COLUMN_WATER_DEPTH:
                    water_depth = decompacted_well.get_water_depth_from_tectonic_subsidence(
                        decompacted_well.tectonic_subsidence,
                        getattr(decompacted_well, 'sea_level', None))  # decompacted_well.sea_level may not exist
                    column_str = column_float_format_string.format(water_depth, width=column_width)
                elif decompacted_column == COLUMN_COMPACTED_THICKNESS:
                    column_str = column_float_format_string.format(decompacted_well.total_compacted_thickness, width=column_width)
                elif decompacted_column == COLUMN_LITHOLOGY:
                    # Write the original lithology components of the surface stratigraphic unit.
                    lithology_string = ''.join('{0:<15} {1:<10.2f} '.format(lithology_name, fraction)
                                               for lithology_name, fraction in decompacted_well.surface_unit.lithology_components)
                    column_str = column_str_format_string.format(lithology_string, width=column_width)
                elif decompacted_column == COLUMN_COMPACTED_DEPTH:
                    # Depth of the top of the first/surface stratigraphic unit.
                    # This matches the age (which is also the top of the first/surface stratigraphic unit).
                    column_str = column_float_format_string.format(decompacted_well.surface_unit.top_depth, width=column_width)
                else:
                    raise ValueError('Unrecognised value for "decompacted_columns".')
            
                file.write(column_str)
            
            file.write('\n')


def backtrack_and_write_decompacted(
        decompacted_output_filename,
        well_filename,
        lithologies_filename,
        age_grid_filename,
        topography_filename,
        total_sediment_thickness_filename,
        crustal_thickness_filename,
        dynamic_topography_model_info=None,
        sea_level_filename=None,
        base_lithology_name=DEFAULT_BASE_LITHOLOGY_NAME,
        ocean_age_to_depth_model=age_to_depth.DEFAULT_MODEL,
        rifting_period=None,
        decompacted_columns=default_decompacted_columns,
        well_location=None,
        well_bottom_age_column=0,
        well_bottom_depth_column=1,
        well_lithology_column=2,
        ammended_well_output_filename=None):
    """
    Backtrack well in 'well_filename' and write decompacted data to 'decompacted_output_filename'.
    
    Also optionally write ammended well data (ie, including extra stratigraphic base unit) to
    'ammended_well_output_filename' if specified.
    
    See 'backtrack()' and 'write_decompacted_wells()' for more details.
    """
    
    # Decompact the well.
    well, decompacted_wells = backtrack(
        well_filename,
        lithologies_filename,
        age_grid_filename,
        topography_filename,
        total_sediment_thickness_filename,
        crustal_thickness_filename,
        dynamic_topography_model_info,
        sea_level_filename,
        base_lithology_name,
        ocean_age_to_depth_model,
        rifting_period,
        well_location,
        well_bottom_age_column,
        well_bottom_depth_column,
        well_lithology_column)
    
    # Attributes of well object to write to file as metadata.
    well_attributes = {
        'longitude': 'SiteLongitude',
        'latitude': 'SiteLatitude',
        'rift_start_age': 'RiftStartAge',
        'rift_end_age': 'RiftEndAge',
        'water_depth': 'WaterDepth'}
    
    # Write out amended well data (ie, extra stratigraphic base unit) if requested.
    if ammended_well_output_filename:
        write_well_file(
            well,
            ammended_well_output_filename,
            # Attributes of well object to write to file as metadata...
            well_attributes=well_attributes)
    
    # Write the decompactions of the well at the ages of its stratigraphic units.
    write_decompacted_wells(
        decompacted_wells,
        decompacted_output_filename,
        well,
        # Attributes of well object to write to file as metadata...
        well_attributes,
        decompacted_columns)


########################
# Command-line parsing #
########################


def argparse_unicode(value_string):
    try:
        # Filename uses the system encoding - decode from 'str' to 'unicode'.
        filename = value_string.decode(sys.getfilesystemencoding())
    except UnicodeDecodeError:
        raise argparse.ArgumentTypeError("Unable to convert filename %s to unicode" % value_string)
    
    return filename


def argparse_non_negative_integer(value_string):
    try:
        value = int(value_string)
    except ValueError:
        raise argparse.ArgumentTypeError("%s is not an integer" % value_string)
    
    if value < 0:
        raise argparse.ArgumentTypeError("%g is a negative number" % value)
    
    return value


def argparse_non_negative_float(value_string):
    try:
        value = float(value_string)
    except ValueError:
        raise argparse.ArgumentTypeError("%s is not a number" % value_string)
    
    if value < 0:
        raise argparse.ArgumentTypeError("%g is a negative number" % value)
    
    return value


# Action to parse a longitude/latitude location.
class ArgParseLocationAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        # Need two numbers (lon and lat).
        if len(values) != 2:
            parser.error('location must be specified as two numbers (longitude and latitude)')
        
        try:
            # Convert strings to float.
            longitude = float(values[0])
            latitude = float(values[1])
        except ValueError:
            raise argparse.ArgumentTypeError("encountered a longitude or latitude that is not a number")
        
        if longitude < -360 or longitude > 360:
            parser.error('longitude must be in the range [-360, 360]')
        if latitude < -90 or latitude > 90:
            parser.error('latitude must be in the range [-90, 90]')
        
        setattr(namespace, self.dest, (longitude, latitude))


# Action to parse dynamic topography model information.
class ArgParseDynamicTopographyAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if len(values) != 3:
            parser.error('Dynamic topography model info must have three parameters '
                         '(grid list filename, static polygons filename, rotation filename).')
        
        grid_list_filename = values[0]
        static_polygons_filename = values[1]
        rotation_filenames = values[2:]  # Needs to be a list.
        
        setattr(namespace, self.dest, (grid_list_filename, static_polygons_filename, rotation_filenames))


ocean_age_to_depth_model_dict = dict((model_name, model) for model, model_name, _ in age_to_depth.ALL_MODELS)
ocean_age_to_depth_model_name_dict = dict((model, model_name) for model, model_name, _ in age_to_depth.ALL_MODELS)
default_ocean_age_to_depth_model_name = ocean_age_to_depth_model_name_dict[age_to_depth.DEFAULT_MODEL]


__description__ = \
    """Find decompacted total sediment thickness and water depth through time.
    
    This backtracking script can be used to find paleo water depths.
    Paleo water depths are obtained from tectonic subsidence by subtracting the isostatic correction of
    decompacted sediment columns through time (optionally including sea level changes relative to present day).
    Tectonic subsidence is modelled separately for ocean basins and continental passive margins.
    Oceanic subsidence is modelled using age-to-depth curves specified using the '-m' option, and a constant offset
    is applied to ensure the modelled present day water depth matches the value sampled from topography grid.
    Continental subsidence is modelled using passive margin rifting (initial and subsequent thermal subsidence).
    The age grid is used to differentiate oceanic and continental regions.
    Dynamic topography is optional for both oceanic and continental where the difference between past
    and present-day dynamic topography is added to subsidence (additionally, for continental crust,
    the difference between dynamic topography at rift start and present-day is also subtracted from
    present-day subsidence before estimating rifting subsidence).
    
    The age, topography, total sediment thickness, crustal thickness and dynamic topography grids
    are sampled at the well location.
    The well location should either be provided inside the well file
    (as '# SiteLongitude = <longitude>' and '# SiteLatitude = <latitude>')
    or specified with the '-x' option (which also overrides well file if both specified).
    If the well depth/thickness is less than the total sediment thickness then an extra base sediment layer is added to
    to fill in the remaining sediment. The lithology of the base layer is specified with the '-b' option.
    
    Reads a lithology text file with each row representing parameters for a single lithology.
    The parameter columns are: name density surface_porosity porosity_decay
    Units of density are kg/m3 and units of porosity decay are m.
    
    Also reads a well text file with each row representing a stratigraphic unit of a single well.
    The required columns are:
        bottom age
        bottom depth
        lithology(s)
    These can be arranged in any order (and even have columns containing unused parameters), however the
    lithology(s) must be the last columns since there can be multiple lithologies (each lithology has
    a name and a fraction, where the fractions add up to 1.0).
    Use the '-c' option to specify the columns for each parameter. For example, to skip unused columns 2 and 3
    (perhaps containing present day water depth and whether column is under water) specify "-c 0 1 4"
    to assign column 0 to bottom age, 1 to bottom depth and 4 to lithology(s).
    
    The decompaction-related outputs are written to a text file with each row representing the top age of a
    stratigraphic unit in the well.
    The following output parameters are available:
{0}
    ...where age has units Ma, and thickness/subsidence/depth have units metres, and density has units kg/m3.
    You can use the '-d' option to specify these choices. For example, "-d age decompacted_thickness"
    will write age to the first column and decompacted thickness to the second column.
    If lithology is specified then it must be the last column.
    
    NOTE: Separate the positional and optional arguments with '--' (workaround for bug in argparse module).
    For example...

    python %(prog)s ... -w well.xy -c 0 1 4 -d age decompacted_thickness -- decompacted_well.xy
    """.format(''.join('        {0}\n'.format(column_name) for column_name in decompacted_column_names))


def get_command_line_parser(
        add_arguments_for_input_data=True):
    """
    Get command-line parser (argparse.ArgumentParser) and add command-line arguments.
    
    If 'add_arguments_for_input_data' is True then add command-line arguments for input data other than
    the well input and output filenames.
    """
    
    # The command-line parser.
    parser = argparse.ArgumentParser(description=__description__, formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument('--version', action='version', version=pybacktrack.version.__version__)
    
    parser.add_argument(
        '-w', '--well_filename', type=argparse_unicode, required=True,
        metavar='well_filename',
        help='The well filename containing age, present day thickness, paleo water depth and lithology(s) '
             'for each stratigraphic unit in a single well.')
    
    if add_arguments_for_input_data:
        parser.add_argument(
            '-l', '--lithologies_filename', type=argparse_unicode, required=True,
            metavar='lithologies_filename',
            help='The lithologies filename used to lookup density, surface porosity and porosity decay.')
    
    parser.add_argument(
        '-x', '--well_location', nargs=2, action=ArgParseLocationAction,
        metavar=('well_longitude', 'well_latitude'),
        help='Optional location of the well. '
             'Must be specified if the well location is not provided inside the well file '
             '(as "# SiteLongitude = <longitude>" and "# SiteLatitude = <latitude>"). '
             'Overrides well file if both specified. '
             'Longitude and latitude are in degrees.')
    
    parser.add_argument(
        '-c', '--well_columns', type=argparse_non_negative_integer, nargs=3, default=[0, 1, 2],
        metavar=('bottom_age_column', 'bottom_depth_column', 'lithology_column'),
        help='The well file column indices (zero-based) for bottom age, bottom depth and lithology(s) respectively. '
             'This enables unused columns to reside in the well text file. '
             'For example, to skip unused columns 2 and 3 '
             '(perhaps containing present day water depth and whether column is under water) '
             'use column indices 0 1 4. Note that lithologies should be the last column since '
             'there can be multiple weighted lithologies (eg, "Grainstone 0.5 Sandstone 0.5"). '
             'Defaults to 0 1 2.')
    
    parser.add_argument(
        '-d', '--decompacted_columns', type=str, nargs='+', default=default_decompacted_column_names,
        metavar='decompacted_column_name',
        help='The columns to output in the decompacted file. '
             'Choices include {0}. '
             'Age has units Ma. Density has units kg/m3. Thickness/subsidence/depth have units metres. '
             'Defaults to "{1}".'.format(
                ', '.join(decompacted_column_names),
                ' '.join(default_decompacted_column_names)))
    
    parser.add_argument(
        '-b', '--base_lithology_name', type=str, default=DEFAULT_BASE_LITHOLOGY_NAME,
        metavar='base_lithology_name',
        help='Lithology name of the stratigraphic unit at the base of the well (must be present in lithologies file). '
             'The well might not record the full depth of sedimentation. '
             'The base unit covers the remaining depth from bottom of well to the total sediment thickness. '
             'Defaults to "{0}".'.format(DEFAULT_BASE_LITHOLOGY_NAME))
    
    parser.add_argument(
        '-m', '--ocean_age_to_depth_model', type=str, default=default_ocean_age_to_depth_model_name,
        metavar='ocean_age_to_depth_model',
        dest='ocean_age_to_depth_model_name',
        help='The oceanic model used to convert age to depth. '
             'Choices include {0}. '
             'Defaults to {1}.'.format(
                ', '.join(model_name for _, model_name, _ in age_to_depth.ALL_MODELS),
                default_ocean_age_to_depth_model_name))
    
    parser.add_argument(
        '-rs', '--rift_start_time', type=argparse_non_negative_float,
        metavar='rift_start_time',
        help='Optional start time of rifting (in My). '
             'Only used if well is located on continental passive margin (outside age grid), '
             'in which case it is not required (even if also not provided inside the well file as '
             '"# RiftStartTime = <rift_start_time>") because it will essentially default to '
             'the rift "end" time. However providing a start time will result in more accurate '
             'subsidence values generated during rifting.')
    parser.add_argument(
        '-re', '--rift_end_time', type=argparse_non_negative_float,
        metavar='rift_end_time',
        help='Optional end time of rifting (in My). '
             'Only used if well is located on continental passive margin (outside age grid), '
             'in which case it must be specified if it is not provided inside the well file '
             '(as "# RiftEndTime = <rift_end_time>"). Overrides well file if both specified.')
    
    parser.add_argument(
        '-o', '--output_well_filename', type=argparse_unicode,
        metavar='output_well_filename',
        help='Optional output well filename to write amended well data to. '
             'This is useful to see the extra stratigraphic base unit added from bottom of well to basement.')
    
    if add_arguments_for_input_data:
        parser.add_argument(
            '-a', '--age_grid_filename', type=argparse_unicode, required=True,
            metavar='age_grid_filename',
            help='Used to obtain age of seafloor at well location.')
        
        parser.add_argument(
            '-s', '--total_sediment_thickness_filename', type=argparse_unicode, required=True,
            metavar='total_sediment_thickness_filename',
            help='Used to obtain total sediment thickness at well location.')
        
        parser.add_argument(
            '-k', '--crustal_thickness_filename', type=argparse_unicode, required=True,
            metavar='crustal_thickness_filename',
            help='Used to obtain crustal thickness at well location.')
        
        parser.add_argument(
            '-t', '--topography_filename', type=argparse_unicode, required=True,
            metavar='topography_filename',
            help='Used to obtain water depth at well location.')
        
        parser.add_argument(
            '-y', '--dynamic_topography_model_info', nargs=3, action=ArgParseDynamicTopographyAction,
            metavar=('dynamic_topography_grid_list_filename', 'static_polygon_filename', 'rotation_filename'),
            help='Optional dynamic topography through time (sampled at reconstructed well locations). '
                 'Can be used both for oceanic floor and continental passive margin '
                 '(ie, well location inside or outside age grid). '
                 'First filename contains a list of dynamic topography grids (and associated times). '
                 'Second filename contains static polygons associated with dynamic topography model '
                 '(used to assign plate ID to well location so it can be reconstructed). '
                 'Third filename is the rotation file associated with model '
                 '(only the rotation file for static continents/oceans is needed - ie, deformation rotations not needed). '
                 'Each row in the grid list file should contain two columns. First column containing '
                 'filename (relative to list file) of a dynamic topography grid at a particular time. '
                 'Second column containing associated time (in Ma).')
        
        parser.add_argument(
            '-sl', '--sea_level_filename', type=str,
            metavar='sea_level_filename',
            help='Optional file used to obtain sea level (relative to present-day) over time. '
                 'If no file is specified then sea level is ignored. '
                 'If specified then each row should contain an age column followed by a column for sea level (in metres).')
    
    parser.add_argument(
        'output_filename', type=argparse_unicode,
        metavar='output_filename',
        help='The output filename used to store the decompacted total sediment thickness and '
             'water depth through time.')
    
    return parser


def post_process_command_line(args):
    
    # Convert output column names to enumerations.
    try:
        decompacted_columns = [decompacted_columns_dict[column_name] for column_name in args.decompacted_columns]
    except KeyError:
        raise argparse.ArgumentTypeError("%s is not a valid decompacted column name" % column_name)
    
    # Convert age-to-depth model name to enumeration.
    try:
        ocean_age_to_depth_model = ocean_age_to_depth_model_dict[args.ocean_age_to_depth_model_name]
    except KeyError:
        raise argparse.ArgumentTypeError("%s is not a valid ocean age-to-depth model" % args.ocean_age_to_depth_model_name)
    
    return decompacted_columns, ocean_age_to_depth_model


if __name__ == '__main__':
    
    import traceback
    
    try:
        # Gather command-line options.
        parser = get_command_line_parser()
        
        # Parse command-line options.
        args = parser.parse_args()
        
        # Do any necessary post-processing/validation of parsed options.
        decompacted_columns, ocean_age_to_depth_model = post_process_command_line(args)
        
        # Backtrack and write output data.
        backtrack_and_write_decompacted(
            args.output_filename,
            args.well_filename,
            args.lithologies_filename,
            args.age_grid_filename,
            args.topography_filename,
            args.total_sediment_thickness_filename,
            args.crustal_thickness_filename,
            args.dynamic_topography_model_info,
            args.sea_level_filename,
            args.base_lithology_name,
            ocean_age_to_depth_model,
            (args.rift_start_time, args.rift_end_time),
            decompacted_columns,
            args.well_location,
            args.well_columns[0],  # well_bottom_age_column
            args.well_columns[1],  # well_bottom_depth_column
            args.well_columns[2],  # well_lithology_column
            args.output_well_filename)
        
        sys.exit(0)
        
    except Exception as exc:
        print('ERROR: {0}'.format(exc), file=sys.stderr)
        # Uncomment this to print traceback to location of raised exception.
        # traceback.print_exc()
        
        sys.exit(1)

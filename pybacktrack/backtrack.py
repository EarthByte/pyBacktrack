
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

:func:`pybacktrack.backtrack_well` finds decompacted total sediment thickness and water depth for each age in a well.

:func:`pybacktrack.write_backtrack_well` writes decompacted parameters as columns in a text file.

:func:`pybacktrack.backtrack_and_write_well` both backtracks well and writes decompacted data.
"""


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import math
import pybacktrack.age_to_depth as age_to_depth
import pybacktrack.bundle_data
from pybacktrack.dynamic_topography import DynamicTopography
from pybacktrack.lithology import read_lithologies_file, DEFAULT_BASE_LITHOLOGY_NAME
import pybacktrack.rifting as rifting
from pybacktrack.sea_level import SeaLevel
from pybacktrack.util.call_system_command import call_system_command
import pybacktrack.version
from pybacktrack.well import read_well_file, write_well_file, write_well_metadata
import sys


# Density in kg/m3.
_DENSITY_WATER = 1030.0
_DENSITY_CRUST = 2800.0
_DENSITY_MANTLE = 3330.0

# Warn the user if the rifting stretching factor (beta) estimate results in a
# tectonic subsidence inaccuracy (at present day) exceeding this amount (in metres)...
_MAX_TECTONIC_SUBSIDENCE_RIFTING_RESIDUAL_ERROR = 100


def backtrack_well(
        well_filename,
        lithology_filenames=[pybacktrack.bundle_data.DEFAULT_BUNDLE_LITHOLOGY_FILENAME],
        age_grid_filename=pybacktrack.bundle_data.BUNDLE_AGE_GRID_FILENAME,
        topography_filename=pybacktrack.bundle_data.BUNDLE_TOPOGRAPHY_FILENAME,
        total_sediment_thickness_filename=pybacktrack.bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,
        crustal_thickness_filename=pybacktrack.bundle_data.BUNDLE_CRUSTAL_THICKNESS_FILENAME,
        dynamic_topography_model=None,
        sea_level_model=None,
        base_lithology_name=DEFAULT_BASE_LITHOLOGY_NAME,
        ocean_age_to_depth_model=age_to_depth.DEFAULT_MODEL,
        rifting_period=None,
        well_location=None,
        well_bottom_age_column=0,
        well_bottom_depth_column=1,
        well_lithology_column=2):
    # Adding function signature on first line of docstring otherwise Sphinx autodoc will print out
    # the expanded values of the bundle filenames.
    """backtrack_well(\
        well_filename,\
        lithology_filenames=[pybacktrack.bundle_data.DEFAULT_BUNDLE_LITHOLOGY_FILENAME],\
        age_grid_filename=pybacktrack.BUNDLE_AGE_GRID_FILENAME,\
        topography_filename=pybacktrack.BUNDLE_TOPOGRAPHY_FILENAME,\
        total_sediment_thickness_filename=pybacktrack.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,\
        crustal_thickness_filename=pybacktrack.BUNDLE_CRUSTAL_THICKNESS_FILENAME,\
        dynamic_topography_model=None,\
        sea_level_model=None,\
        base_lithology_name=pybacktrack.DEFAULT_BASE_LITHOLOGY_NAME,\
        ocean_age_to_depth_model=pybacktrack.AGE_TO_DEPTH_DEFAULT_MODEL,\
        rifting_period=None,\
        well_location=None,\
        well_bottom_age_column=0,\
        well_bottom_depth_column=1,\
        well_lithology_column=2)
    Finds decompacted total sediment thickness and water depth for each age in a well.
    
    Parameters
    ----------
    well_filename : string
        Name of well text file.
    lithology_filenames: list of string, optional
        One or more text files containing lithologies.
    age_grid_filename : string, optional
        Age grid filename.
        Used to obtain age of seafloor at well location.
    topography_filename : string, optional
        Topography filename.
        Used to obtain water depth at well location.
    total_sediment_thickness_filename : string, optional
        Total sediment thickness filename.
        Used to obtain total sediment thickness at well location.
    crustal_thickness_filename : string, optional
        Crustal thickness filename.
        Used to obtain crustal thickness at well location.
    dynamic_topography_model : string or tuple, optional
        Represents a time-dependent dynamic topography raster grid.
        Currently only used for oceanic floor (ie, well location inside age grid)
        it is not used if well is on continental crust (passive margin).
        
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
        Lithology name of the stratigraphic unit at the base of the well (must be present in lithologies file).
        The stratigraphic units in the well might not record the full depth of sedimentation.
        The base unit covers the remaining depth from bottom of well to the total sediment thickness.
        Defaults to ``Shale``.
    ocean_age_to_depth_model : {pybacktrack.AGE_TO_DEPTH_MODEL_GDH1, pybacktrack.AGE_TO_DEPTH_MODEL_CROSBY_2007} or function, optional
        The model to use when converting ocean age to depth at well location
        (if on ocean floor - not used for continental passive margin).
        It can be one of the enumerated values, or a callable function accepting a single non-negative age parameter and returning depth (in metres).
    rifting_period : tuple, optional
        Optional time period of rifting (if on continental passive margin - not used for oceanic floor).
        If specified then should be a 2-tuple (rift_start_age, rift_end_age) where rift_start_age can be None
        (in which case rifting is considered instantaneous from a stretching point-of-view, not thermal).
        If specified then overrides value in well file.
        If well is on continental passive margin then at least rift end age should be specified
        either here or in well file.
    well_location : tuple, optional
        Optional location of well.
        If not provided then is extracted from the ``well_filename`` file.
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
    :class:`pybacktrack.Well`
        The well read from ``well_filename``.
        It may also be amended with a base stratigraphic unit from the bottom of the well to basement.
    list of :class:`pybacktrack.DecompactedWell`
        The decompacted wells associated with the well.
    
    Raises
    ------
    ValueError
        If ``lithology_column`` is not the largest column number (must be last column).
    ValueError
        If ``well_location`` is not specified *and* the well location was not extracted from the well file.
    
    Notes
    -----
    Each attribute to read from well file (eg, bottom_age, bottom_depth, etc) has a column index to direct
    which column it should be read from.
    
    The tectonic subsidence at each age (of decompacted wells) is added as a *tectonic_subsidence* attribute
    to each decompacted well returned.
    """
    
    # If a dynamic topography *model name* was specified then convert it to a bundled dynamic topography info tuple.
    if (dynamic_topography_model is not None and
        dynamic_topography_model in pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_NAMES):
        dynamic_topography_model = pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS[dynamic_topography_model]
    
    # If a sea level *model name* was specified then convert it to a bundled sea level filename.
    if (sea_level_model is not None and
        sea_level_model in pybacktrack.bundle_data.BUNDLE_SEA_LEVEL_MODEL_NAMES):
        sea_level_model = pybacktrack.bundle_data.BUNDLE_SEA_LEVEL_MODELS[sea_level_model]
    
    # Read the lithologies from one or more text files.
    #
    # It used to be a single filename (instead of a list) so handle that case to be backward compatible.
    if isinstance(lithology_filenames, str if sys.version_info[0] >= 3 else basestring): # Python 2 vs 3.
        lithology_filename = lithology_filenames
        lithologies = read_lithologies_file(lithology_filename)
    else:
        # Read all the lithology files and merge their dicts.
        # Subsequently specified files override previous files in the list.
        # So if the first and second files have the same lithology then the second lithology is used.
        lithologies = {}
        for lithology_filename in lithology_filenames:
            lithologies.update(read_lithologies_file(lithology_filename))
    
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
    age = _sample_grid(well.longitude, well.latitude, age_grid_filename)
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
    present_day_topography = _sample_grid(well.longitude, well.latitude, topography_filename)
    # If sampled outside topography grid then set topography to zero.
    # Shouldn't happen since topography grid is not masked anywhere.
    if math.isnan(present_day_topography):
        present_day_topography = 0.0
    
    # Topography is negative in ocean but water depth is positive.
    present_day_water_depth = -present_day_topography
    # Clamp water depth so it's below sea level (ie, must be >= 0).
    present_day_water_depth = max(0, present_day_water_depth)
    
    # Sample total sediment thickness grid at well location.
    present_day_total_sediment_thickness = _sample_grid(well.longitude, well.latitude, total_sediment_thickness_filename)
    # If sampled outside total sediment thickness grid then set total sediment thickness to zero.
    # This will result in a base stratigraphic layer not getting added underneath the well to fill
    # in the total sediment thickness (but the well is probably close to the coastlines where it's shallow
    # and hence probably includes all layers in the total sediment thickness anyway).
    if math.isnan(present_day_total_sediment_thickness):
        present_day_total_sediment_thickness = 0.0
    
    # Sample crustal thickness grid at well location.
    present_day_crustal_thickness = _sample_grid(well.longitude, well.latitude, crustal_thickness_filename)
    # If sampled outside crustal thickness then set crustal thickness to zero.
    # Shouldn't happen since crustal thickness grid is not masked anywhere.
    if math.isnan(present_day_crustal_thickness):
        present_day_crustal_thickness = 0.0
    
    # Add a base stratigraphic unit from the bottom of the well to basement if the stratigraphic units
    # in the well do not record the total sediment thickness.
    _add_stratigraphic_unit_to_basement(
        well,
        present_day_total_sediment_thickness,
        lithologies,
        base_lithology_name,
        age)
    
    # Each decompacted well (in returned list) represents decompaction at the age of a stratigraphic unit in the well.
    decompacted_wells = well.decompact()
    
    # Calculate sea level (relative to present day) for each decompaction age (unpacking of stratigraphic units)
    # that is an average over the decompacted surface layer's period of deposition.
    if sea_level_model:
        _add_sea_level(
            well,
            decompacted_wells,
            # Create sea level object for integrating sea level over time periods...
            SeaLevel(sea_level_model))
    
    # Isostatic correction for total sediment thickness.
    #
    # For ocean floor we could use a simple formula using only total sediment thickness based on Sykes et al. 1996
    # (although we'd still need something for continental crust).
    # However the first decompaction age of the well contains an isostatic correction based on its lithology units which
    # is more accurate so we'll use that instead. It also means the decompacted water depth at age zero (ie, top of well)
    # will match the water depth we obtained from topography above.
    #
    # present_day_total_sediment_isostatic_correction = _calc_ocean_total_sediment_thickness_isostatic_correction(present_day_total_sediment_thickness)
    present_day_total_sediment_isostatic_correction = decompacted_wells[0].get_sediment_isostatic_correction()
    
    # Unload the sediment to get unloaded water depth.
    # Note that sea level variations don't apply here because they are zero at present day.
    present_day_tectonic_subsidence = present_day_water_depth + present_day_total_sediment_isostatic_correction
    
    # Create time-dependent grid object for sampling dynamic topography (if requested).
    if dynamic_topography_model:
        dynamic_topography_list_filename, dynamic_topography_static_polygon_filename, dynamic_topography_rotation_filenames = dynamic_topography_model
        dynamic_topography = DynamicTopography(
            dynamic_topography_list_filename, dynamic_topography_static_polygon_filename, dynamic_topography_rotation_filenames,
            well.longitude, well.latitude, age)
    else:
        dynamic_topography = None
    
    # Calculate tectonic subsidence (unloaded water depth) at each decompaction age (unpacking of stratigraphic units).
    # The tectonic subsidence curve can later be used to calculate paleo (loaded) water depths.
    if age is not None:
        # Oceanic crust.
        _add_oceanic_tectonic_subsidence(
            well,
            decompacted_wells,
            present_day_tectonic_subsidence,
            ocean_age_to_depth_model,
            age,
            dynamic_topography)
    else:
        # Continental crust.
        _add_continental_tectonic_subsidence(
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
            'RiftEndAge': ('rift_end_age', read_age)})
    
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


def _add_stratigraphic_unit_to_basement(
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


def _add_sea_level(
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


def _add_oceanic_tectonic_subsidence(
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
    present_day_tectonic_subsidence_from_model = age_to_depth.convert_age_to_depth(age, ocean_age_to_depth_model)
    
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
    #             (_DENSITY_MANTLE - _DENSITY_CRUST) / (_DENSITY_MANTLE - _DENSITY_WATER))
    
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
        tectonic_subsidence_from_model = age_to_depth.convert_age_to_depth(paleo_age_of_crust_at_decompaction_time, ocean_age_to_depth_model)
        
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


def _add_continental_tectonic_subsidence(
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
    
    # Get dynamic topography (if requested) at rift start and remove contribution of dynamic topography
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
    if math.fabs(subsidence_residual) > _MAX_TECTONIC_SUBSIDENCE_RIFTING_RESIDUAL_ERROR:
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


def _sample_grid(longitude, latitude, grid_filename):
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


def _calc_ocean_total_sediment_thickness_isostatic_correction(total_sediment_thickness):
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


# Enumerations for the 'decompacted_columns' argument in 'write_well()'.
COLUMN_AGE = 0
COLUMN_DECOMPACTED_THICKNESS = 1
COLUMN_DECOMPACTED_DENSITY = 2
COLUMN_TECTONIC_SUBSIDENCE = 3
COLUMN_WATER_DEPTH = 4
COLUMN_COMPACTED_THICKNESS = 5
COLUMN_LITHOLOGY = 6
COLUMN_COMPACTED_DEPTH = 7

_DECOMPACTED_COLUMNS_DICT = {
    'age': COLUMN_AGE,
    'decompacted_thickness': COLUMN_DECOMPACTED_THICKNESS,
    'decompacted_density': COLUMN_DECOMPACTED_DENSITY,
    'tectonic_subsidence': COLUMN_TECTONIC_SUBSIDENCE,
    'water_depth': COLUMN_WATER_DEPTH,
    'compacted_thickness': COLUMN_COMPACTED_THICKNESS,
    'lithology': COLUMN_LITHOLOGY,
    'compacted_depth': COLUMN_COMPACTED_DEPTH}
_DECOMPACTED_COLUMN_NAMES_DICT = dict([(v, k) for k, v in _DECOMPACTED_COLUMNS_DICT.iteritems()])
_DECOMPACTED_COLUMN_NAMES = sorted(_DECOMPACTED_COLUMNS_DICT.keys())

_DEFAULT_DECOMPACTED_COLUMN_NAMES = ['age', 'decompacted_thickness']
DEFAULT_DECOMPACTED_COLUMNS = [_DECOMPACTED_COLUMNS_DICT[column_name] for column_name in _DEFAULT_DECOMPACTED_COLUMN_NAMES]


def write_well(
        decompacted_wells,
        decompacted_wells_filename,
        well,
        well_attributes=None,
        decompacted_columns=DEFAULT_DECOMPACTED_COLUMNS):
    """write_backtrack_well(\
        decompacted_wells,\
        decompacted_wells_filename,\
        well,\
        well_attributes=None,\
        decompacted_columns=pybacktrack.BACKTRACK_DEFAULT_DECOMPACTED_COLUMNS):
    Write decompacted parameters as columns in a text file.
    
    Parameters
    ----------
    decompacted_wells : sequence of :class:`pybacktrack.DecompactedWell`
        The decompacted wells returned by :func:`pybacktrack.backtrack_well`.
    decompacted_wells_filename : string
        Name of output text file.
    well : :class:`pybacktrack.Well`
        The well to extract metadata from.
    well_attributes : dict, optional
        Optional attributes in :class:`pybacktrack.Well` object to write to well file metadata.
        If specified then must be a dictionary mapping each attribute name to a metadata name.
        For example, ``{'longitude' : 'SiteLongitude', 'latitude' : 'SiteLatitude'}``.
        will write ``well.longitude`` (if not None) to metadata 'SiteLongitude', etc.
        Not that the attributes must exist in ``well`` (but can be set to None).
    decompacted_columns : list of {pybacktrack.BACKTRACK_COLUMN_AGE, \
                                   pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_THICKNESS, \
                                   pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_DENSITY, \
                                   pybacktrack.BACKTRACK_COLUMN_TECTONIC_SUBSIDENCE, \
                                   pybacktrack.BACKTRACK_COLUMN_WATER_DEPTH, \
                                   pybacktrack.BACKTRACK_COLUMN_COMPACTED_THICKNESS, \
                                   pybacktrack.BACKTRACK_COLUMN_LITHOLOGY, \
                                   pybacktrack.BACKTRACK_COLUMN_COMPACTED_DEPTH}, optional
        The decompacted columns (and their order) to output to ``decompacted_wells_filename``.
    
    Raises
    ------
    ValueError
        If an unrecognised value is encountered in ``decompacted_columns``.
    ValueError
        If ``COLUMN_LITHOLOGY`` is specified in ``decompacted_columns`` but is not the last column.
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
            decompacted_column_name = _DECOMPACTED_COLUMN_NAMES_DICT[decompacted_column]
            
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


def backtrack_and_write_well(
        decompacted_output_filename,
        well_filename,
        lithology_filenames=[pybacktrack.bundle_data.DEFAULT_BUNDLE_LITHOLOGY_FILENAME],
        age_grid_filename=pybacktrack.bundle_data.BUNDLE_AGE_GRID_FILENAME,
        topography_filename=pybacktrack.bundle_data.BUNDLE_TOPOGRAPHY_FILENAME,
        total_sediment_thickness_filename=pybacktrack.bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,
        crustal_thickness_filename=pybacktrack.bundle_data.BUNDLE_CRUSTAL_THICKNESS_FILENAME,
        dynamic_topography_model=None,
        sea_level_model=None,
        base_lithology_name=DEFAULT_BASE_LITHOLOGY_NAME,
        ocean_age_to_depth_model=age_to_depth.DEFAULT_MODEL,
        rifting_period=None,
        decompacted_columns=DEFAULT_DECOMPACTED_COLUMNS,
        well_location=None,
        well_bottom_age_column=0,
        well_bottom_depth_column=1,
        well_lithology_column=2,
        ammended_well_output_filename=None):
    # Adding function signature on first line of docstring otherwise Sphinx autodoc will print out
    # the expanded values of the bundle filenames.
    """backtrack_and_write_well(\
        decompacted_output_filename,\
        well_filename,\
        lithology_filenames=[pybacktrack.bundle_data.DEFAULT_BUNDLE_LITHOLOGY_FILENAME],\
        age_grid_filename=pybacktrack.BUNDLE_AGE_GRID_FILENAME,\
        topography_filename=pybacktrack.BUNDLE_TOPOGRAPHY_FILENAME,\
        total_sediment_thickness_filename=pybacktrack.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,\
        crustal_thickness_filename=pybacktrack.BUNDLE_CRUSTAL_THICKNESS_FILENAME,\
        dynamic_topography_model=None,\
        sea_level_model=None,\
        base_lithology_name=pybacktrack.DEFAULT_BASE_LITHOLOGY_NAME,\
        ocean_age_to_depth_model=pybacktrack.AGE_TO_DEPTH_DEFAULT_MODEL,\
        rifting_period=None,\
        decompacted_columns=pybacktrack.BACKTRACK_DEFAULT_DECOMPACTED_COLUMNS,\
        well_location=None,\
        well_bottom_age_column=0,\
        well_bottom_depth_column=1,\
        well_lithology_column=2,\
        ammended_well_output_filename=None)
    Same as :func:`pybacktrack.backtrack_well` but also writes decompacted results to a text file.
    
    Also optionally write amended well data (ie, including extra stratigraphic base unit from well bottom to ocean basement)
    to ``ammended_well_output_filename`` if specified.
    
    Parameters
    ----------
    decompacted_output_filename : string
        Name of text file to write decompacted results to.
    well_filename : string
        Name of well text file.
    lithology_filenames: list of string, optional
        One or more text files containing lithologies.
    age_grid_filename : string, optional
        Age grid filename.
        Used to obtain age of seafloor at well location.
    topography_filename : string, optional
        Topography filename.
        Used to obtain water depth at well location.
    total_sediment_thickness_filename : string, optional
        Total sediment thickness filename.
        Used to obtain total sediment thickness at well location.
    crustal_thickness_filename : string, optional
        Crustal thickness filename.
        Used to obtain crustal thickness at well location.
    dynamic_topography_model : string or tuple, optional
        Represents a time-dependent dynamic topography raster grid.
        Currently only used for oceanic floor (ie, well location inside age grid)
        it is not used if well is on continental crust (passive margin).
        
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
        Lithology name of the stratigraphic unit at the base of the well (must be present in lithologies file).
        The stratigraphic units in the well might not record the full depth of sedimentation.
        The base unit covers the remaining depth from bottom of well to the total sediment thickness.
        Defaults to ``Shale``.
    ocean_age_to_depth_model : {pybacktrack.AGE_TO_DEPTH_MODEL_GDH1, pybacktrack.AGE_TO_DEPTH_MODEL_CROSBY_2007} or function, optional
        The model to use when converting ocean age to depth at well location
        (if on ocean floor - not used for continental passive margin).
        It can be one of the enumerated values, or a callable function accepting a single non-negative age parameter and returning depth (in metres).
    rifting_period : tuple, optional
        Optional time period of rifting (if on continental passive margin - not used for oceanic floor).
        If specified then should be a 2-tuple (rift_start_age, rift_end_age) where rift_start_age can be None
        (in which case rifting is considered instantaneous from a stretching point-of-view, not thermal).
        If specified then overrides value in well file.
        If well is on continental passive margin then at least rift end age should be specified
        either here or in well file.
    decompacted_columns : list of {pybacktrack.BACKTRACK_COLUMN_AGE, \
                                   pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_THICKNESS, \
                                   pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_DENSITY, \
                                   pybacktrack.BACKTRACK_COLUMN_TECTONIC_SUBSIDENCE, \
                                   pybacktrack.BACKTRACK_COLUMN_WATER_DEPTH, \
                                   pybacktrack.BACKTRACK_COLUMN_COMPACTED_THICKNESS, \
                                   pybacktrack.BACKTRACK_COLUMN_LITHOLOGY, \
                                   pybacktrack.BACKTRACK_COLUMN_COMPACTED_DEPTH}, optional
        The decompacted columns (and their order) to output to ``decompacted_output_filename``.
    well_location : tuple, optional
        Optional location of well.
        If not provided then is extracted from the ``well_filename`` file.
        If specified then overrides value in well file.
        If specified then must be a 2-tuple (longitude, latitude) in degrees.
    well_bottom_age_column : int, optional
        The column of well file containing bottom age. Defaults to 0.
    well_bottom_depth_column : int, optional
        The column of well file containing bottom depth. Defaults to 1.
    well_lithology_column : int, optional
        The column of well file containing lithology(s). Defaults to 2.
    ammended_well_output_filename: string, optional
        Amended well data filename. Useful if an extra stratigraphic base unit is added from well bottom to ocean basement.
    
    Raises
    ------
    ValueError
        If ``lithology_column`` is not the largest column number (must be last column).
    ValueError
        If ``well_location`` is not specified *and* the well location was not extracted from the well file.
    
    Notes
    -----
    Each attribute to read from well file (eg, bottom_age, bottom_depth, etc) has a column index to direct
    which column it should be read from.
    """
    """
    Backtrack well in ``well_filename`` and write decompacted data to ``decompacted_output_filename``.
    
    Also optionally write ammended well data (ie, including extra stratigraphic base unit) to
    ``ammended_well_output_filename`` if specified.
    """
    
    # Decompact the well.
    well, decompacted_wells = backtrack_well(
        well_filename,
        lithology_filenames,
        age_grid_filename,
        topography_filename,
        total_sediment_thickness_filename,
        crustal_thickness_filename,
        dynamic_topography_model,
        sea_level_model,
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
        'rift_end_age': 'RiftEndAge'}
    
    # Write out amended well data (ie, extra stratigraphic base unit) if requested.
    if ammended_well_output_filename:
        write_well_file(
            well,
            ammended_well_output_filename,
            # Attributes of well object to write to file as metadata...
            well_attributes=well_attributes)
    
    # Write the decompactions of the well at the ages of its stratigraphic units.
    write_well(
        decompacted_wells,
        decompacted_output_filename,
        well,
        # Attributes of well object to write to file as metadata...
        well_attributes,
        decompacted_columns)


#
# For backward compatibility after renaming functions.
#
backtrack = backtrack_well
write_decompacted_wells = write_well
backtrack_and_write_decompacted = backtrack_and_write_well


if __name__ == '__main__':
    
    ########################
    # Command-line parsing #
    ########################
    
    import argparse
    
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

    def main():
        
        __description__ = """Find decompacted total sediment thickness and water depth through time.
    
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
    """.format(''.join('        {0}\n'.format(column_name) for column_name in _DECOMPACTED_COLUMN_NAMES))
    
        #
        # Gather command-line options.
        #
        
        # The command-line parser.
        parser = argparse.ArgumentParser(description=__description__, formatter_class=argparse.RawDescriptionHelpFormatter)
        
        parser.add_argument('--version', action='version', version=pybacktrack.version.__version__)
        
        parser.add_argument(
            '-w', '--well_filename', type=argparse_unicode, required=True,
            metavar='well_filename',
            help='The well filename containing age, present day thickness, paleo water depth and lithology(s) '
                 'for each stratigraphic unit in a single well.')
        
        # Allow user to override the default lithology filename.
        parser.add_argument(
            '-l', '--lithology_filenames', type=argparse_unicode, nargs='+',
            default=[pybacktrack.bundle_data.DEFAULT_BUNDLE_LITHOLOGY_FILENAME],
            metavar='lithology_filename',
            help='Optional lithology filenames used to lookup density, surface porosity and porosity decay. '
                 'If more than one file provided then conflicting lithologies in latter files override those in former files. '
                 'Defaults to the bundled data file "{0}".'.format(pybacktrack.bundle_data.DEFAULT_BUNDLE_LITHOLOGY_FILENAME))
        
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
            '-d', '--decompacted_columns', type=str, nargs='+', default=_DEFAULT_DECOMPACTED_COLUMN_NAMES,
            metavar='decompacted_column_name',
            help='The columns to output in the decompacted file. '
                 'Choices include {0}. '
                 'Age has units Ma. Density has units kg/m3. Thickness/subsidence/depth have units metres. '
                 'Defaults to "{1}".'.format(
                    ', '.join(_DECOMPACTED_COLUMN_NAMES),
                    ' '.join(_DEFAULT_DECOMPACTED_COLUMN_NAMES)))
        
        parser.add_argument(
            '-b', '--base_lithology_name', type=str, default=DEFAULT_BASE_LITHOLOGY_NAME,
            metavar='base_lithology_name',
            help='Lithology name of the stratigraphic unit at the base of the well (must be present in lithologies file). '
                 'The well might not record the full depth of sedimentation. '
                 'The base unit covers the remaining depth from bottom of well to the total sediment thickness. '
                 'Defaults to "{0}".'.format(DEFAULT_BASE_LITHOLOGY_NAME))
        
        parser.add_argument(
            '-m', '--ocean_age_to_depth_model', nargs='*', action=age_to_depth.ArgParseAgeModelAction,
            metavar='model_parameter',
            default=age_to_depth.DEFAULT_MODEL,
            help='The oceanic model used to convert age to depth. '
                 'It can be the name of an in-built oceanic age model: {0} (defaults to {1}). '
                 'Or it can be an age model filename followed by two integers representing the age and depth column indices, '
                 'where the file should contain at least two columns (one containing the age and the other the depth).'.format(
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
        
        # Allow user to override default age grid filename (if they don't want the one in the bundled data).
        parser.add_argument(
            '-a', '--age_grid_filename', type=argparse_unicode,
            default=pybacktrack.bundle_data.BUNDLE_AGE_GRID_FILENAME,
            metavar='age_grid_filename',
            help='Optional age grid filename used to obtain age of seafloor at well location. '
                 'Defaults to the bundled data file "{0}".'.format(pybacktrack.bundle_data.BUNDLE_AGE_GRID_FILENAME))
        
        # Allow user to override default total sediment thickness filename (if they don't want the one in the bundled data).
        parser.add_argument(
            '-s', '--total_sediment_thickness_filename', type=argparse_unicode,
            default=pybacktrack.bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,
            metavar='total_sediment_thickness_filename',
            help='Optional filename used to obtain total sediment thickness at well location. '
                 'Defaults to the bundled data file "{0}".'.format(pybacktrack.bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME))
        
        # Allow user to override default crustal thickness filename (if they don't want the one in the bundled data).
        parser.add_argument(
            '-k', '--crustal_thickness_filename', type=argparse_unicode,
            default=pybacktrack.bundle_data.BUNDLE_CRUSTAL_THICKNESS_FILENAME,
            metavar='crustal_thickness_filename',
            help='Optional filename used to obtain crustal thickness at well location. '
                 'Defaults to the bundled data file "{0}".'.format(pybacktrack.bundle_data.BUNDLE_CRUSTAL_THICKNESS_FILENAME))
        
        # Allow user to override default topography filename (if they don't want the one in the bundled data).
        parser.add_argument(
            '-t', '--topography_filename', type=argparse_unicode,
            default=pybacktrack.bundle_data.BUNDLE_TOPOGRAPHY_FILENAME,
            metavar='topography_filename',
            help='Optional topography filename used to obtain water depth at well location. '
                 'Defaults to the bundled data file "{0}".'.format(pybacktrack.bundle_data.BUNDLE_TOPOGRAPHY_FILENAME))
        
        # Can optionally specify dynamic topography as a triplet of filenames or a model name (if using bundled data) but not both.
        dynamic_topography_argument_group = parser.add_mutually_exclusive_group()
        dynamic_topography_argument_group.add_argument(
            '-ym', '--bundle_dynamic_topography_model', type=str,
            metavar='bundle_dynamic_topography_model',
            help='Optional dynamic topography through time at well location. '
                 'If no model (or filenames) specified then dynamic topography is ignored. '
                 'Can be used both for oceanic floor and continental passive margin '
                 '(ie, well location inside or outside age grid). '
                 'Choices include {0}.'.format(', '.join(pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_NAMES)))
        dynamic_topography_argument_group.add_argument(
            '-y', '--dynamic_topography_model', nargs=3, action=ArgParseDynamicTopographyAction,
            metavar=('dynamic_topography_grid_list_filename', 'static_polygon_filename', 'rotation_filename'),
            help='Optional dynamic topography through time (sampled at reconstructed well locations). '
                 'If no filenames (or model) specified then dynamic topography is ignored. '
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
        
        # Can optionally specify sea level as a filename or  model name (if using bundled data) but not both.
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
            'output_filename', type=argparse_unicode,
            metavar='output_filename',
            help='The output filename used to store the decompacted total sediment thickness and '
                 'water depth through time.')
        
        #
        # Parse command-line options.
        #
        args = parser.parse_args()
        
        #
        # Do any necessary post-processing/validation of parsed options.
        #
        
        # Convert output column names to enumerations.
        try:
            decompacted_columns = [_DECOMPACTED_COLUMNS_DICT[column_name] for column_name in args.decompacted_columns]
        except KeyError:
            raise argparse.ArgumentTypeError("%s is not a valid decompacted column name" % column_name)
        
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
        
        # Backtrack and write output data.
        backtrack_and_write_well(
            args.output_filename,
            args.well_filename,
            args.lithology_filenames,
            args.age_grid_filename,
            args.topography_filename,
            args.total_sediment_thickness_filename,
            args.crustal_thickness_filename,
            dynamic_topography_model,
            sea_level_model,
            args.base_lithology_name,
            args.ocean_age_to_depth_model,
            (args.rift_start_time, args.rift_end_time),
            decompacted_columns,
            args.well_location,
            args.well_columns[0],  # well_bottom_age_column
            args.well_columns[1],  # well_bottom_depth_column
            args.well_columns[2],  # well_lithology_column
            args.output_well_filename)
        
        sys.exit(0)
    
    import traceback
    
    try:
        main()
        sys.exit(0)
    except Exception as exc:
        print('ERROR: {0}'.format(exc), file=sys.stderr)
        # Uncomment this to print traceback to location of raised exception.
        # traceback.print_exc()
        sys.exit(1)

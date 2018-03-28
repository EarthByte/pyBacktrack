
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

"""An easier-to-use version of the :mod:`backtrack<pybacktrack.backtrack>` module that references included :mod:`bundled data<pybacktrack.bundle_data>`.

:func:`backtrack` same as :func:`pybacktrack.backtrack.backtrack` but uses :mod:`bundled data<pybacktrack.bundle_data>`.

:func:`backtrack_and_write_decompacted` same as :func:`pybacktrack.backtrack.backtrack_and_write_decompacted` but uses :mod:`bundled data<pybacktrack.bundle_data>`.
"""

from __future__ import print_function
import argparse
import pybacktrack.age_to_depth
import pybacktrack.backtrack
import pybacktrack.bundle_data
import os.path
import sys
import traceback


def backtrack(
        well_filename,
        lithologies_filename=pybacktrack.bundle_data.BUNDLE_LITHOLOGIES_FILENAME,
        age_grid_filename=pybacktrack.bundle_data.BUNDLE_AGE_GRID_FILENAME,
        topography_filename=pybacktrack.bundle_data.BUNDLE_TOPOGRAPHY_FILENAME,
        total_sediment_thickness_filename=pybacktrack.bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,
        crustal_thickness_filename=pybacktrack.bundle_data.BUNDLE_CRUSTAL_THICKNESS_FILENAME,
        dynamic_topography_model_name=None,
        sea_level_model_name=None,
        base_lithology_name=pybacktrack.backtrack.DEFAULT_BASE_LITHOLOGY_NAME,
        ocean_age_to_depth_model=pybacktrack.age_to_depth.DEFAULT_MODEL,
        rifting_period=None,
        well_location=None,
        well_bottom_age_column=0,
        well_bottom_depth_column=1,
        well_lithology_column=2):
    # Adding function signature on first line of docstring otherwise Sphinx autodoc will print out
    # the expanded values of the bundle filenames.
    """backtrack(\
        well_filename,\
        lithologies_filename=pybacktrack.bundle_data.BUNDLE_LITHOLOGIES_FILENAME,\
        age_grid_filename=pybacktrack.bundle_data.BUNDLE_AGE_GRID_FILENAME,\
        topography_filename=pybacktrack.bundle_data.BUNDLE_TOPOGRAPHY_FILENAME,\
        total_sediment_thickness_filename=pybacktrack.bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,\
        crustal_thickness_filename=pybacktrack.bundle_data.BUNDLE_CRUSTAL_THICKNESS_FILENAME,\
        dynamic_topography_model_name=None,\
        sea_level_model_name=None,\
        base_lithology_name=pybacktrack.backtrack.DEFAULT_BASE_LITHOLOGY_NAME,\
        ocean_age_to_depth_model=pybacktrack.age_to_depth.DEFAULT_MODEL,\
        rifting_period=None,\
        well_location=None,\
        well_bottom_age_column=0,\
        well_bottom_depth_column=1,\
        well_lithology_column=2)
    Finds decompacted total sediment thickness and water depth for each age in a well.
    
    This function is very similar to :func:`pybacktrack.backtrack.backtrack` except it has
    default values that reference the :mod:`bundled data<pybacktrack.bundle_data>` included in the ``pybacktrack`` package.
    It also uses a model name (instead of filenames) for dynamic topography and sea-level curve to
    make specifying them even easier (especially dynamic topography).
    
    Parameters
    ----------
    well_filename : string
        Name of well text file.
    lithologies_filename : string, optional
        Name of lithologies text file.
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
    dynamic_topography_model_name : string, optional
        Represents a time-dependent dynamic topography raster grid.
        Currently only used for oceanic floor (ie, well location inside age grid)
        it is not used if well is on continental crust (passive margin).
        This is the name of a bundled dynamic topography model.
        Choices include 'terra', 'M1', 'M2', 'M3', 'M4', 'M5', 'M6' and 'M7'.
    sea_level_model_name : string, optional
        Name of the bundled sea level model.
        Choices include 'Haq87_SealevelCurve' and 'Haq87_SealevelCurve_Longterm'.
        Used to obtain sea levels relative to present day.
    base_lithology_name : string, optional
        Lithology name of the stratigraphic unit at the base of the well (must be present in lithologies file).
        The stratigraphic units in the well might not record the full depth of sedimentation.
        The base unit covers the remaining depth from bottom of well to the total sediment thickness.
        Defaults to 'Shale'.
    ocean_age_to_depth_model : {pybacktrack.age_to_depth.MODEL_GDH1, pybacktrack.age_to_depth.MODEL_CROSBY_2007}, optional
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
    :class:`Well`
        The well read from ``well_filename``.
        It may also be amended with a base stratigraphic unit from the bottom of the well to basement.
    list of :class:`Well.DecompactedWell`
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
    
    # Convert dynamic topography model name to list filename (if specified).
    if dynamic_topography_model_name is None:
        dynamic_topography_model_info = None
    else:
        try:
            dynamic_topography_model_info = pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_INFOS[dynamic_topography_model_name]
        except KeyError:
            raise ValueError("%s is not a valid dynamic topography model name" % dynamic_topography_model_name)
    
    # Convert sea level model name to filename (if specified).
    if sea_level_model_name is None:
        sea_level_filename = None
    else:
        try:
            sea_level_filename = pybacktrack.bundle_data.BUNDLE_SEA_LEVEL_MODEL_FILES[sea_level_model_name]
        except KeyError:
            raise ValueError("%s is not a valid sea level model name" % sea_level_model_name)
    
    # Delegate to the 'backtrack' module.
    return pybacktrack.backtrack.backtrack(
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


def backtrack_and_write_decompacted(
        decompacted_output_filename,
        well_filename,
        lithologies_filename=pybacktrack.bundle_data.BUNDLE_LITHOLOGIES_FILENAME,
        age_grid_filename=pybacktrack.bundle_data.BUNDLE_AGE_GRID_FILENAME,
        topography_filename=pybacktrack.bundle_data.BUNDLE_TOPOGRAPHY_FILENAME,
        total_sediment_thickness_filename=pybacktrack.bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,
        crustal_thickness_filename=pybacktrack.bundle_data.BUNDLE_CRUSTAL_THICKNESS_FILENAME,
        dynamic_topography_model_name=None,
        sea_level_model_name=None,
        base_lithology_name=pybacktrack.backtrack.DEFAULT_BASE_LITHOLOGY_NAME,
        ocean_age_to_depth_model=pybacktrack.age_to_depth.DEFAULT_MODEL,
        rifting_period=None,
        decompacted_columns=pybacktrack.backtrack.default_decompacted_columns,
        well_location=None,
        well_bottom_age_column=0,
        well_bottom_depth_column=1,
        well_lithology_column=2,
        ammended_well_output_filename=None):
    # Adding function signature on first line of docstring otherwise Sphinx autodoc will print out
    # the expanded values of the bundle filenames.
    """backtrack_and_write_decompacted(\
        decompacted_output_filename,\
        well_filename,\
        lithologies_filename=pybacktrack.bundle_data.BUNDLE_LITHOLOGIES_FILENAME,\
        age_grid_filename=pybacktrack.bundle_data.BUNDLE_AGE_GRID_FILENAME,\
        topography_filename=pybacktrack.bundle_data.BUNDLE_TOPOGRAPHY_FILENAME,\
        total_sediment_thickness_filename=pybacktrack.bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,\
        crustal_thickness_filename=pybacktrack.bundle_data.BUNDLE_CRUSTAL_THICKNESS_FILENAME,\
        dynamic_topography_model_name=None,\
        sea_level_model_name=None,\
        base_lithology_name=pybacktrack.backtrack.DEFAULT_BASE_LITHOLOGY_NAME,\
        ocean_age_to_depth_model=pybacktrack.age_to_depth.DEFAULT_MODEL,\
        rifting_period=None,\
        decompacted_columns=pybacktrack.backtrack.default_decompacted_columns,\
        well_location=None,\
        well_bottom_age_column=0,\
        well_bottom_depth_column=1,\
        well_lithology_column=2,\
        ammended_well_output_filename=None)
    Same as :func:`pybacktrack.backtrack_bundle.backtrack` but also writes decompacted results to a text file.
    
    Also optionally write amended well data (ie, including extra stratigraphic base unit from well bottom to ocean basement)
    to ``ammended_well_output_filename`` if specified.
    
    This function is very similar to :func:`pybacktrack.backtrack.backtrack_and_write_decompacted` except it has
    default values that reference the :mod:`bundled data<pybacktrack.bundle_data>` included in the `pybacktrack` package.
    It also uses a model name (instead of filenames) for dynamic topography and sea-level curve to
    make specifying them even easier (especially dynamic topography).
    
    Parameters
    ----------
    decompacted_output_filename : string
        Name of text file to write decompacted results to.
    well_filename : string
        Name of well text file.
    lithologies_filename : string, optional
        Name of lithologies text file.
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
    dynamic_topography_model_name : string, optional
        Represents a time-dependent dynamic topography raster grid.
        Currently only used for oceanic floor (ie, well location inside age grid)
        it is not used if well is on continental crust (passive margin).
        This is the name of a bundled dynamic topography model.
        Choices include 'terra', 'M1', 'M2', 'M3', 'M4', 'M5', 'M6' and 'M7'.
    sea_level_model_name : string, optional
        Name of the bundled sea level model.
        Choices include 'Haq87_SealevelCurve' and 'Haq87_SealevelCurve_Longterm'.
        Used to obtain sea levels relative to present day.
    base_lithology_name : string, optional
        Lithology name of the stratigraphic unit at the base of the well (must be present in lithologies file).
        The stratigraphic units in the well might not record the full depth of sedimentation.
        The base unit covers the remaining depth from bottom of well to the total sediment thickness.
        Defaults to 'Shale'.
    ocean_age_to_depth_model : {pybacktrack.age_to_depth.MODEL_GDH1, pybacktrack.age_to_depth.MODEL_CROSBY_2007}, optional
        The model to use when converting ocean age to depth at well location
        (if on ocean floor - not used for continental passive margin).
    rifting_period : tuple, optional
        Optional time period of rifting (if on continental passive margin - not used for oceanic floor).
        If specified then should be a 2-tuple (rift_start_age, rift_end_age) where rift_start_age can be None
        (in which case rifting is considered instantaneous from a stretching point-of-view, not thermal).
        If specified then overrides value in well file.
        If well is on continental passive margin then at least rift end age should be specified
        either here or in well file.
    decompacted_columns : list of {pybacktrack.backtrack.COLUMN_AGE, \
                                   pybacktrack.backtrack.COLUMN_DECOMPACTED_THICKNESS, \
                                   pybacktrack.backtrack.COLUMN_DECOMPACTED_DENSITY, \
                                   pybacktrack.backtrack.COLUMN_TECTONIC_SUBSIDENCE, \
                                   pybacktrack.backtrack.COLUMN_WATER_DEPTH, \
                                   pybacktrack.backtrack.COLUMN_COMPACTED_THICKNESS, \
                                   pybacktrack.backtrack.COLUMN_LITHOLOGY, \
                                   pybacktrack.backtrack.COLUMN_COMPACTED_DEPTH}, optional
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
    
    # Convert dynamic topography model name to list filename (if specified).
    if dynamic_topography_model_name is None:
        dynamic_topography_model_info = None
    else:
        try:
            dynamic_topography_model_info = pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_INFOS[dynamic_topography_model_name]
        except KeyError:
            raise ValueError("%s is not a valid dynamic topography model name" % dynamic_topography_model_name)
    
    # Convert sea level model name to filename (if specified).
    if sea_level_model_name is None:
        sea_level_filename = None
    else:
        try:
            sea_level_filename = pybacktrack.bundle_data.BUNDLE_SEA_LEVEL_MODEL_FILES[sea_level_model_name]
        except KeyError:
            raise ValueError("%s is not a valid sea level model name" % sea_level_model_name)
    
    # Delegate to the 'backtrack' module.
    pybacktrack.backtrack.backtrack_and_write_decompacted(
        decompacted_output_filename,
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
        decompacted_columns,
        well_location,
        well_bottom_age_column,
        well_bottom_depth_column,
        well_lithology_column,
        ammended_well_output_filename)


if __name__ == '__main__':
    
    try:
        # Gather command-line options.
        # But don't add options for data that we've bundled.
        parser = pybacktrack.backtrack.get_command_line_parser(False)
        
        # Allow user to override default lithologies filename (if they don't want the one in the bundled data).
        parser.add_argument(
            '-l', '--lithologies_filename', type=pybacktrack.backtrack.argparse_unicode,
            default=pybacktrack.bundle_data.BUNDLE_LITHOLOGIES_FILENAME,
            metavar='lithologies_filename',
            help='Optional lithologies filename used to lookup density, surface porosity and porosity decay. '
                 'Defaults to "{0}".'.format(pybacktrack.bundle_data.BUNDLE_LITHOLOGIES_FILENAME))
        
        # Optional dynamic topography model name.
        parser.add_argument(
            '-y', '--dynamic_topography_model', type=str,
            metavar='dynamic_topography_model',
            help='Optional dynamic topography through time at well location. '
                 'Can be used both for oceanic floor and continental passive margin '
                 '(ie, well location inside or outside age grid). '
                 'Choices include {0}.'.format(', '.join(pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_NAMES)))
        
        parser.add_argument(
            '-sl', '--sea_level_model', type=str,
            metavar='sea_level_model',
            help='Optional sea level model used to obtain sea level (relative to present-day) over time. '
                 'Choices include {0}.'.format(', '.join(pybacktrack.bundle_data.BUNDLE_SEA_LEVEL_MODEL_NAMES)))
        
        # Parse command-line options.
        args = parser.parse_args()
        
        # Do any necessary post-processing/validation of parsed options.
        decompacted_columns, ocean_age_to_depth_model = pybacktrack.backtrack.post_process_command_line(args)
        
        # Backtrack and write output data.
        backtrack_and_write_decompacted(
            args.output_filename,
            args.well_filename,
            args.lithologies_filename,
            dynamic_topography_model_name=args.dynamic_topography_model,
            sea_level_model_name=args.sea_level_model,
            base_lithology_name=args.base_lithology_name,
            ocean_age_to_depth_model=ocean_age_to_depth_model,
            rifting_period=(args.rift_start_time, args.rift_end_time),
            decompacted_columns=decompacted_columns,
            well_location=args.well_location,
            well_bottom_age_column=args.well_columns[0],
            well_bottom_depth_column=args.well_columns[1],
            well_lithology_column=args.well_columns[2],
            ammended_well_output_filename=args.output_well_filename)
        
        sys.exit(0)
        
    except Exception as exc:
        print('ERROR: {0}'.format(exc), file=sys.stderr)
        # Uncomment this to print traceback to location of raised exception.
        # traceback.print_exc()
        
        sys.exit(1)

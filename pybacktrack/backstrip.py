
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

"""Find decompacted total sediment thickness and tectonic subsidence through time.

:func:`backstrip_well` finds decompacted total sediment thickness and tectonic subsidence for each age in a well.

:func:`write_well` writes decompacted parameters as columns in a text file.
"""


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pybacktrack.bundle_data
from pybacktrack.lithology import read_lithologies_file, DEFAULT_BASE_LITHOLOGY_NAME
from pybacktrack.sea_level import SeaLevel
from pybacktrack.util.call_system_command import call_system_command
import pybacktrack.version
from pybacktrack.well import read_well_file, write_well_file, write_well_metadata
import math
import sys


def backstrip_well(
        well_filename,
        lithologies_filename=pybacktrack.bundle_data.BUNDLE_LITHOLOGIES_FILENAME,
        total_sediment_thickness_filename=pybacktrack.bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,
        sea_level_model=None,
        base_lithology_name=DEFAULT_BASE_LITHOLOGY_NAME,
        well_location=None,
        well_bottom_age_column=0,
        well_bottom_depth_column=1,
        well_min_water_depth_column=2,
        well_max_water_depth_column=3,
        well_lithology_column=4):
    """
    Finds decompacted total sediment thickness and tectonic subsidence for each age in 'well'.
    
    well_filename: name of well text file.
    
    lithologies_filename: name of lithologies text file.
    
    total_sediment_thickness_filename: Total sediment thickness filename.
                                       Used to obtain total sediment thickness at well location.
    
    sea_level_model : string, optional
        Used to obtain sea levels relative to present day.
        Can be either the name of a bundled sea level model, or a sea level filename.
        Bundled sea level models include ``Haq87_SealevelCurve`` and ``Haq87_SealevelCurve_Longterm``.
    
    base_lithology_name: Lithology name of the stratigraphic unit at the base of the well (must be present in lithologies file).
                         The stratigraphic units in the well might not record the full depth of sedimentation.
                         The base unit covers the remaining depth from bottom of well to the total sediment thickness.
    
    well_location: Optional location of well. If not provided then is extracted from 'well_filename' file.
                   If specified then overrides value in well file.
                   If specified then must be a 2-tuple (longitude, latitude) in degrees.
    
    <well columns>: Each column attribute to read from well file (bottom_age, bottom_depth,
                    min_water_depth, max_water_depth and lithology(s))
                    has a column index to direct which column it should be read from.
    
    Returns: 2-tuple (Well, list of well.DecompactedWell)
    
    The min/max paleo water depths at each age (of decompacted wells) is added as
    'min_water_depth' and 'max_water_depth' attributes to each decompacted well returned.
    
    Each attribute to read from well file (eg, bottom_age, bottom_depth, etc) has a column index to direct
    which column it should be read from.
    
    Raises ValueError if 'lithology_column' is not the largest column number (must be last column).
    Raises ValueError if 'well_location' is not specified *and* the well location was not extracted from the well file.
    """
    
    # If a sea level *model name* was specified then convert it to a bundled sea level filename.
    if (sea_level_model is not None and
        sea_level_model in pybacktrack.bundle_data.BUNDLE_SEA_LEVEL_MODEL_NAMES):
        sea_level_model = pybacktrack.bundle_data.BUNDLE_SEA_LEVEL_MODELS[sea_level_model]
    
    # Read the lithologies from a text file.
    lithologies = read_lithologies_file(lithologies_filename)
    
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
    
    # Read the well from a text file.
    well = read_well_file(
        well_filename,
        lithologies,
        well_bottom_age_column,
        well_bottom_depth_column,
        well_lithology_column,
        # Extra columns to read into attributes 'well.StratigraphicUnit.min_water_depth' and
        # 'well.StratigraphicUnit.max_water_depth' for each row (returned in well.Well)...
        other_columns={
            'min_water_depth': well_min_water_depth_column,
            'max_water_depth': well_max_water_depth_column},
        # Attributes to read from file into returned well object...
        well_attributes={
            'SiteLongitude': ('longitude', read_longitude),
            'SiteLatitude': ('latitude', read_latitude)})
    # There should be at least one stratigraphic unit - if not then return empty decompaction list.
    if not well.stratigraphic_units:
        return []
    
    # If the well location was specified then override the location read from the well file (if a location was read).
    if well_location is not None:
        well.longitude, well.latitude = well_location
    # Needs to be specified by user or obtained from well file.
    if well.longitude is None or well.latitude is None:
        raise ValueError('Well location was not extracted from well file and was not specified by user.')
    
    # Sample total sediment thickness grid at well location.
    total_sediment_thickness = _sample_grid(well.longitude, well.latitude, total_sediment_thickness_filename)
    # If sampled outside total sediment thickness grid then set total sediment thickness to zero.
    # This will result in a base stratigraphic layer not getting added underneath the well to fill
    # in the total sediment thickness (but the well is probably close to the coastlines where it's shallow
    # and hence probably includes all layers in the total sediment thickness anyway).
    if math.isnan(total_sediment_thickness):
        total_sediment_thickness = 0.0
    
    # The stratigraphic units in the well might not record the total sediment thickness.
    # The well depth/thickness is the bottom depth of the deepest stratigraphic unit (they are sorted from youngest to oldest).
    deepest_well_unit = well.stratigraphic_units[-1]
    well_sediment_thickness = deepest_well_unit.bottom_depth
    if well_sediment_thickness < total_sediment_thickness:
        base_unit_thickness = total_sediment_thickness - well_sediment_thickness
        base_unit_top_depth = well_sediment_thickness
        base_unit_bottom_depth = base_unit_top_depth + base_unit_thickness
        
        # Age at the top of the base unit (age at which deposition ended for base unit) is
        # the bottom age of the unit above it (deepest unit of well).
        base_unit_top_age = deepest_well_unit.bottom_age
        # We don't know the age at the bottom of the base unit so just set it to the top age.
        base_unit_bottom_age = base_unit_top_age
        
        # One lithology component comprising the full fraction.
        base_unit_lithogy_components = [(base_lithology_name, 1.0)]
        
        # We don't know the min/max water depth of the base unit so
        # just use the min/max water depth of the deepest unit of well.
        base_unit_other_attributes = {
            'min_water_depth': deepest_well_unit.min_water_depth,
            'max_water_depth': deepest_well_unit.max_water_depth}
        
        well.add_compacted_unit(
            base_unit_top_age, base_unit_bottom_age,
            base_unit_top_depth, base_unit_bottom_depth,
            base_unit_lithogy_components, lithologies,
            base_unit_other_attributes)
        
    elif well_sediment_thickness - total_sediment_thickness > 0.01 * well_sediment_thickness:
        # Warn the user that the well thickness exceeds the total sediment thickness - requested by Dietmar.
        # This can happen as a result of the large uncertainties in the sediment thickness grid.
        print('WARNING: Well thickness {0} is larger than the total sediment thickness grid {1} at well location ({2}, {3}).'.format(
              well_sediment_thickness, total_sediment_thickness, well.longitude, well.latitude), file=sys.stderr)
    
    # Each decompacted well (in returned list) represents decompaction at the age of a stratigraphic unit in the well.
    decompacted_wells = well.decompact()
    
    # Calculate sea level (relative to present day) for each decompaction age (unpacking of stratigraphic units)
    # that is an average over the decompacted surface layer's period of deposition.
    if sea_level_model:
        # Create sea level object for integrating sea level over time periods.
        sea_level = SeaLevel(sea_level_model)
        
        # The sea level (relative to present day) is integrated over the period of deposition of each
        # stratigraphic layer (in decompacted wells) and added as a 'sea_level' attribute to each decompacted well.
        for decompacted_well in decompacted_wells:
            decompacted_well.sea_level = sea_level.get_average_level(
                decompacted_well.surface_unit.bottom_age,
                decompacted_well.surface_unit.top_age)
    
    return well, decompacted_wells


def _sample_grid(longitude, latitude, grid_filename):
    """
    Samples the grid file 'grid_filename' at the longitude/latitude location (in degrees).
    
    Returns sampled float value (which can be NaN if location is in a masked region of grid).
    """
    
    location_data = '{0} {1}\n'.format(longitude, latitude)

    # The command-line strings to execute GMT 'grdtrack'.
    grdtrack_command_line = ["gmt", "grdtrack", "-G{0}".format(grid_filename)]
    
    # Call the system command.
    stdout_data = call_system_command(grdtrack_command_line, stdin=location_data, return_stdout=True)
    
    # GMT grdtrack returns a single line containing "longitude latitude sampled_value".
    # Note that if GMT returns "NaN" then we'll return float('nan').
    return float(stdout_data.split()[2])


# Enumerations for the 'decompacted_columns' argument in 'write_well()'.
COLUMN_AGE = 0
COLUMN_DECOMPACTED_THICKNESS = 1
COLUMN_DECOMPACTED_DENSITY = 2
COLUMN_AVERAGE_TECTONIC_SUBSIDENCE = 3
COLUMN_MIN_TECTONIC_SUBSIDENCE = 4
COLUMN_MAX_TECTONIC_SUBSIDENCE = 5
COLUMN_AVERAGE_WATER_DEPTH = 6
COLUMN_MIN_WATER_DEPTH = 7
COLUMN_MAX_WATER_DEPTH = 8
COLUMN_COMPACTED_THICKNESS = 9
COLUMN_LITHOLOGY = 10
COLUMN_COMPACTED_DEPTH = 11

_DECOMPACTED_COLUMNS_DICT = {
    'age': COLUMN_AGE,
    'decompacted_thickness': COLUMN_DECOMPACTED_THICKNESS,
    'decompacted_density': COLUMN_DECOMPACTED_DENSITY,
    'average_tectonic_subsidence': COLUMN_AVERAGE_TECTONIC_SUBSIDENCE,
    'min_tectonic_subsidence': COLUMN_MIN_TECTONIC_SUBSIDENCE,
    'max_tectonic_subsidence': COLUMN_MAX_TECTONIC_SUBSIDENCE,
    'average_water_depth': COLUMN_AVERAGE_WATER_DEPTH,
    'min_water_depth': COLUMN_MIN_WATER_DEPTH,
    'max_water_depth': COLUMN_MAX_WATER_DEPTH,
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
                elif decompacted_column == COLUMN_AVERAGE_TECTONIC_SUBSIDENCE:
                    min_tectonic_subsidence, max_tectonic_subsidence = decompacted_well.get_min_max_tectonic_subsidence_from_water_depth(
                        # Use extra attributes (min/max water depth) loaded into original well...
                        decompacted_well.surface_unit.min_water_depth,
                        decompacted_well.surface_unit.max_water_depth,
                        getattr(decompacted_well, 'sea_level', None))  # decompacted_well.sea_level may not exist
                    average_tectonic_subsidence = (min_tectonic_subsidence + max_tectonic_subsidence) / 2.0
                    column_str = column_float_format_string.format(average_tectonic_subsidence, width=column_width)
                elif decompacted_column == COLUMN_MIN_TECTONIC_SUBSIDENCE:
                    min_tectonic_subsidence, max_tectonic_subsidence = decompacted_well.get_min_max_tectonic_subsidence_from_water_depth(
                        # Use extra attributes (min/max water depth) loaded into original well...
                        decompacted_well.surface_unit.min_water_depth,
                        decompacted_well.surface_unit.max_water_depth,
                        getattr(decompacted_well, 'sea_level', None))  # decompacted_well.sea_level may not exist
                    column_str = column_float_format_string.format(min_tectonic_subsidence, width=column_width)
                elif decompacted_column == COLUMN_MAX_TECTONIC_SUBSIDENCE:
                    min_tectonic_subsidence, max_tectonic_subsidence = decompacted_well.get_min_max_tectonic_subsidence_from_water_depth(
                        # Use extra attributes (min/max water depth) loaded into original well...
                        decompacted_well.surface_unit.min_water_depth,
                        decompacted_well.surface_unit.max_water_depth,
                        getattr(decompacted_well, 'sea_level', None))  # decompacted_well.sea_level may not exist
                    column_str = column_float_format_string.format(max_tectonic_subsidence, width=column_width)
                elif decompacted_column == COLUMN_AVERAGE_WATER_DEPTH:
                    # Use extra attributes (min/max water depth) loaded into original well...
                    average_water_depth = (decompacted_well.surface_unit.min_water_depth + decompacted_well.surface_unit.max_water_depth) / 2.0
                    column_str = column_float_format_string.format(average_water_depth, width=column_width)
                elif decompacted_column == COLUMN_MIN_WATER_DEPTH:
                    # Use extra attributes (min/max water depth) loaded into original well...
                    column_str = column_float_format_string.format(decompacted_well.surface_unit.min_water_depth, width=column_width)
                elif decompacted_column == COLUMN_MAX_WATER_DEPTH:
                    # Use extra attributes (min/max water depth) loaded into original well...
                    column_str = column_float_format_string.format(decompacted_well.surface_unit.max_water_depth, width=column_width)
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


def backstrip_and_write_well(
        decompacted_output_filename,
        well_filename,
        lithologies_filename=pybacktrack.bundle_data.BUNDLE_LITHOLOGIES_FILENAME,
        total_sediment_thickness_filename=pybacktrack.bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,
        sea_level_model=None,
        base_lithology_name=DEFAULT_BASE_LITHOLOGY_NAME,
        decompacted_columns=DEFAULT_DECOMPACTED_COLUMNS,
        well_location=None,
        well_bottom_age_column=0,
        well_bottom_depth_column=1,
        well_min_water_depth_column=2,
        well_max_water_depth_column=3,
        well_lithology_column=4,
        ammended_well_output_filename=None):
    
    # Decompact the well.
    well, decompacted_wells = backstrip_well(
        well_filename,
        lithologies_filename,
        total_sediment_thickness_filename,
        sea_level_model,
        base_lithology_name,
        well_location,
        well_bottom_age_column,
        well_bottom_depth_column,
        well_min_water_depth_column,
        well_max_water_depth_column,
        well_lithology_column)
    
    # Attributes of well object to write to file as metadata.
    well_attributes = {'longitude': 'SiteLongitude', 'latitude': 'SiteLatitude'}
    
    # Write out amended well data (ie, extra stratigraphic base unit) if requested.
    if ammended_well_output_filename:
        write_well_file(
            well,
            ammended_well_output_filename,
            ['min_water_depth', 'max_water_depth'],
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
backstrip = backstrip_well
write_decompacted_wells = write_well
backstrip_and_write_decompacted = backstrip_and_write_well


if __name__ == '__main__':
    
    import argparse
    
    def main():
        
        __description__ = """Find decompacted total sediment thickness and tectonic subsidence through time.
    
    This backstripping script can be used to find tectonic subsidence (due to lithospheric stretching) from
    paleo water depths of the stratigraphic columns and their decompaction through time.
    
    For (deeper) ocean basin regions the backtracking script is more suitable since oceanic subsidence is
    somewhat simpler (due to no lithospheric stretching) which can be modelled using an age-to-depth curve
    and used to find the unknown paleo water depths.
    
    So backstripping is suited to finding tectonic subsidence and backtracking is suited to finding paleo water depths.
    
    The total sediment thickness ('-s') grid is sampled at the well location.
    The well location should either be provided inside the well file (as '# SiteLongitude = <longitude>' and '# SiteLatitude = <latitude>')
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
        min water depth
        max water depth
        lithology(s)
    These can be arranged in any order (and even have columns containing unused parameters), however the
    lithology(s) must be the last columns since there can be multiple lithologies (each lithology has
    a name and a fraction, where the fractions add up to 1.0).
    Use the '-c' option to specify the columns for each parameter. For example, to skip unused columns 4 and 5
    (perhaps containing present day water depth and whether column is under water) specify "-c 0 1 2 3 6"
    to assign column 0 to bottom age, 1 to bottom depth, 2 to min water depth, 3 to max water depth and
    6 to lithology(s).
    
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

    python %(prog)s -w well.xy -l lithologies.txt -s tot_sed_thickness.nc -c 0 1 2 3 6 -d age decompacted_thickness -- decompacted_well.xy
    """.format(''.join('        {0}\n'.format(column_name) for column_name in _DECOMPACTED_COLUMN_NAMES))
        
        # The command-line parser.
        parser = argparse.ArgumentParser(description=__description__, formatter_class=argparse.RawDescriptionHelpFormatter)
        
        parser.add_argument('--version', action='version', version=pybacktrack.version.__version__)
        
        def parse_unicode(value_string):
            try:
                # Filename uses the system encoding - decode from 'str' to 'unicode'.
                filename = value_string.decode(sys.getfilesystemencoding())
            except UnicodeDecodeError:
                raise argparse.ArgumentTypeError("Unable to convert filename %s to unicode" % value_string)
            
            return filename
        
        parser.add_argument(
            '-w', '--well_filename', type=parse_unicode, required=True,
            metavar='well_filename',
            help='The well filename containing age, present day thickness, paleo water depth and lithology(s) '
                 'for each stratigraphic unit in a single well.')
         
        # Allow user to override default lithologies filename (if they don't want the one in the bundled data).
        parser.add_argument(
            '-l', '--lithologies_filename', type=parse_unicode,
            default=pybacktrack.bundle_data.BUNDLE_LITHOLOGIES_FILENAME,
            metavar='lithologies_filename',
            help='Optional lithologies filename used to lookup density, surface porosity and porosity decay. '
                 'Defaults to the bundled data file "{0}".'.format(pybacktrack.bundle_data.BUNDLE_LITHOLOGIES_FILENAME))
        
        # Action to parse a longitude/latitude location.
        class LocationAction(argparse.Action):
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
        
        parser.add_argument(
            '-x', '--well_location', nargs=2, action=LocationAction,
            metavar=('well_longitude', 'well_latitude'),
            help='Optional location of the well. '
                 'Must be specified if the well location is not provided inside the well file '
                 '(as "# SiteLongitude = <longitude>" and "# SiteLatitude = <latitude>"). '
                 'Overrides well file if both specified. '
                 'Longitude and latitude are in degrees.')
        
        def parse_non_negative_integer(value_string):
            try:
                value = int(value_string)
            except ValueError:
                raise argparse.ArgumentTypeError("%s is not an integer" % value_string)
            
            if value < 0:
                raise argparse.ArgumentTypeError("%g is a negative number" % value)
            
            return value
        
        parser.add_argument(
            '-c', '--well_columns', type=parse_non_negative_integer, nargs=5, default=[0, 1, 2, 3, 4],
            metavar=('bottom_age_column', 'bottom_depth_column', 'min_water_depth_column', 'max_water_depth_column', 'lithology_column'),
            help='The well file column indices (zero-based) for bottom age, bottom depth, '
                 'min water depth, max water depth and lithology(s) respectively. '
                 'This enables unused columns to reside in the well text file. '
                 'For example, to skip unused columns 4 and 5 '
                 '(perhaps containing present day water depth and whether column is under water) '
                 'use column indices 0 1 2 3 6. Note that lithologies should be the last column since '
                 'there can be multiple weighted lithologies (eg, "Grainstone 0.5 Sandstone 0.5"). '
                 'Defaults to 0 1 2 3 4.')
        
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
            '-o', '--output_well_filename', type=parse_unicode,
            metavar='output_well_filename',
            help='Optional output well filename to write amended well data to. '
                 'This is useful to see the extra stratigraphic base unit added from bottom of well to basement.')
        
        # Allow user to override default total sediment thickness filename (if they don't want the one in the bundled data).
        parser.add_argument(
            '-s', '--total_sediment_thickness_filename', type=parse_unicode,
            default=pybacktrack.bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,
            metavar='total_sediment_thickness_filename',
            help='Optional filename used to obtain total sediment thickness at well location. '
                 'Defaults to the bundled data file "{0}".'.format(pybacktrack.bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME))
        
        # Can optionally specify sea level as a filename or  model name (if using bundled data) but not both.
        sea_level_argument_group = parser.add_mutually_exclusive_group()
        sea_level_argument_group.add_argument(
            '-slm', '--bundle_sea_level_model', type=str,
            metavar='bundle_sea_level_model',
            help='Optional sea level model used to obtain sea level (relative to present-day) over time. '
                 'If no model (or filename) is specified then sea level is ignored. '
                 'Choices include {0}.'.format(', '.join(pybacktrack.bundle_data.BUNDLE_SEA_LEVEL_MODEL_NAMES)))
        sea_level_argument_group.add_argument(
            '-sl', '--sea_level_model', type=parse_unicode,
            metavar='sea_level_model',
            help='Optional file used to obtain sea level (relative to present-day) over time. '
                 'If no filename (or model) is specified then sea level is ignored. '
                 'If specified then each row should contain an age column followed by a column for sea level (in metres).')
        
        parser.add_argument(
            'output_filename', type=parse_unicode,
            metavar='output_filename',
            help='The output filename used to store the decompacted total sediment thickness and '
                 'tectonic subsidence through time.')
        
        # Parse command-line options.
        args = parser.parse_args()
        
        # Convert output column names to enumerations.
        try:
            decompacted_columns = [_DECOMPACTED_COLUMNS_DICT[column_name] for column_name in args.decompacted_columns]
        except KeyError:
            raise argparse.ArgumentTypeError("%s is not a valid decompacted column name" % column_name)
        
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
        
        # Decompact the well.
        well, decompacted_wells = backstrip_well(
            args.well_filename,
            args.lithologies_filename,
            args.total_sediment_thickness_filename,
            sea_level_model,
            args.base_lithology_name,
            args.well_location,
            well_bottom_age_column=args.well_columns[0],
            well_bottom_depth_column=args.well_columns[1],
            well_min_water_depth_column=args.well_columns[2],
            well_max_water_depth_column=args.well_columns[3],
            well_lithology_column=args.well_columns[4])
        
        # Attributes of well object to write to file as metadata.
        well_attributes = {'longitude': 'SiteLongitude', 'latitude': 'SiteLatitude'}
        
        # Write out amended well data (ie, extra stratigraphic base unit) if requested.
        if args.output_well_filename:
            write_well_file(
                well,
                args.output_well_filename,
                ['min_water_depth', 'max_water_depth'],
                # Attributes of well object to write to file as metadata...
                well_attributes=well_attributes)
        
        # Write the decompactions of the well at the ages of its stratigraphic units.
        write_well(
            decompacted_wells,
            args.output_filename,
            well,
            # Attributes of well object to write to file as metadata...
            well_attributes,
            decompacted_columns)
    
    import traceback
    
    try:
        main()
        sys.exit(0)
    except Exception as exc:
        print('ERROR: {0}'.format(exc), file=sys.stderr)
        # Uncomment this to print traceback to location of raised exception.
        # traceback.print_exc()
        sys.exit(1)

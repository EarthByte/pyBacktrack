
"""
    Copyright (C) 2017 The University of Sydney, Australia
    
    This program is free software; you can redistribute it and/or modify it under
    the terms of the GNU General Public License, version 2, as published by
    the Free Software Foundation.
    
    This program is distributed in the hope that it will be useful, but WITHOUT
    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
    FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
    for more details.
    
    You should have received a copy of the GNU General Public License along
    with this program; if not, write to Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""


#########################################################################
# Classes and utilities to read and decompact a sediment column (well). #
#                                                                       #
# This is used by the backstrip and backtrack modules.                  #
#########################################################################


from __future__ import print_function
import math
from lithology import create_lithology_from_components
import sys


# Density in kg/m3.
DENSITY_WATER = 1030.0
DENSITY_MANTLE = 3330.0


class StratigraphicUnit(object):
    """
    Class to hold data for a stratigraphic unit.
    """
    
    def __init__(self, top_age, bottom_age, top_depth, bottom_depth, lithology_components, lithologies, other_attributes=None):
        """
        
        lithology_components: Sequence of tuples (name, fraction) containing a lithology name and its fraction of contribution.
        
        lithologies: A dict mapping lithology names to lithology.Lithology objects.
        
        other_attributes: Optional dict of attribute name/value pairs to set on stratigraphic unit object (using 'setattr').
        
        The type of 'lithology' is lithology.Lithology.
        """
        
        self.top_age = top_age
        self.bottom_age = bottom_age
        self.top_depth = top_depth
        self.bottom_depth = bottom_depth
        
        # Create a combined lithology (if necessary) from multiple weighted lithologies.
        self.lithology = create_lithology_from_components(lithology_components, lithologies)
        self.lithology_components = lithology_components
        
        # Add any extra attributes requested.
        if other_attributes is not None:
            for name, value in other_attributes.iteritems():
                setattr(self, name, value)
    
    def calc_decompacted_thickness(self, decompacted_depth_to_top):
        """
        Calculate decompacted thickness when top of this stratigraphic unit is at depth 'decompacted_depth_to_top'.
        """
        
        present_day_thickness = self.bottom_depth - self.top_depth
        
        surface_porosity = self.lithology.surface_porosity
        porosity_decay = self.lithology.porosity_decay
        
        #
        # Assuming the porosity decays exponentially and that the volume of grains within a unit never changes we get:
        #
        #    Integral(1 - porosity(z), z = D -> D + T) = Integral(1 - porosity(z), z = d -> d + t)
        #
        # ...where D is 'decompacted_depth_to_top' and T is 'decompacted_thickness', and
        # 'd' is present day depth to top of unit and 't' is present day thickness of unit.
        #
        #    Integral(1 - porosity(z), z = D -> D + T) = T - Integral(porosity(0) * exp(-z / decay), z = D -> D + T)
        #                                              = T - (-decay * porosity(0) * (exp(-(D+T)/decay) - exp(-D/decay)))
        #                                              = T - (-decay * porosity(0) * exp(-D/decay) * (exp(-T/decay) - 1))
        #                                              = T + decay * porosity(0) * exp(-D/decay) * (exp(-T/decay) - 1)
        #
        #    Integral(1 - porosity(z), z = d -> d + t) = t + decay * porosity(0) * exp(-d/decay) * (exp(-t/decay) - 1)
        #
        #    Integral(1 - porosity(z), z = D -> D + T) = Integral(1 - porosity(z), z = d -> d + t)
        #    T + decay * porosity(0) * exp(-D/decay) * (exp(-T/decay) - 1) = t + decay * porosity(0) * exp(-d/decay) * (exp(-t/decay) - 1)
        #    T = -decay * porosity(0) * exp(-D/decay) * (exp(-T/decay) - 1) + t + decay * porosity(0) * exp(-d/decay) * (exp(-t/decay) - 1)
        #    T = a * exp(-T/decay) + b
        #
        # ...where a and b are:
        #
        #    a = -decay * porosity(0) * exp(-D/decay)
        #
        #    b = decay * porosity(0) * exp(-D/decay) + t + decay * porosity(0) * exp(-d/decay) * (exp(-t/decay) - 1)
        #      = -a + t + decay * porosity(0) * exp(-d/decay) * (exp(-t/decay) - 1)
        #
        # So the decompacted thickness T:
        #
        #    T = a * exp(-T/decay) + b
        #
        # ...can be solved iteratively by repeatedly substituting the left hand side back into the right hand side
        # until T converges on a solution. The initial T is chosen to be 't' (the present day thickness).
        #
        
        # Constants 'a' and 'b' are calculated outside the iteration loop for efficiency.
        a = -porosity_decay * surface_porosity * math.exp(-decompacted_depth_to_top / porosity_decay)
        b = (-a + present_day_thickness +
             porosity_decay * surface_porosity * math.exp(-self.top_depth / porosity_decay) *
             (math.exp(-present_day_thickness / porosity_decay) - 1))
        
        # Start out with initial estimate - choose the present day thickness.
        decompacted_thickness = present_day_thickness
        
        # Limit the number of iterations in case we never converge.
        # Although should converge within around 20 iterations (for 1e-6 accuracy).
        for iteration in xrange(1000):
            new_decompacted_thickness = a * math.exp(-decompacted_thickness / porosity_decay) + b
            
            # If we've converged within a tolerance then we're done.
            if math.fabs(new_decompacted_thickness - decompacted_thickness) < 1e-6:
                decompacted_thickness = new_decompacted_thickness
                break
            
            # The new thickness becomes the old thickness for the next loop iteration.
            decompacted_thickness = new_decompacted_thickness
        
        return decompacted_thickness
    
    def calc_decompacted_density(self, decompacted_thickness, decompacted_depth_to_top):
        """
        Calculate average decompacted density when top of this stratigraphic unit is at depth 'decompacted_depth_to_top'
        and decompacted thickness is 'decompacted_thickness' (see 'calc_decompacted_thickness()').
        """
        
        density = self.lithology.density
        surface_porosity = self.lithology.surface_porosity
        porosity_decay = self.lithology.porosity_decay
        
        #
        # Decompacted density at depth z is:
        #
        #    decompacted_density(z) = density_water * porosity(z) + density * (1 - porosity(z))
        #
        # The average density over the decompacted stratigraphic unit is:
        #
        #    average_decompacted_density = (1 / T) * Integral(decompacted_density(z), z = D -> D + T)
        #
        # ...where D is 'decompacted_depth_to_top' and T is 'decompacted_thickness'.
        #
        #    average_decompacted_density = (1 / T) * Integral(density_water * porosity(z) + density * (1 - porosity(z)), z = D -> D + T)
        #                                = (1 / T) * (T * density + (density_water - density) * Integral(porosity(z), z = D -> D + T))
        #                                = density + (1 / T) * (density_water - density) * Integral(porosity(z), z = D -> D + T))
        #
        #    Integral(porosity(z), z = D -> D + T) = Integral(porosity(0) * exp(-z / decay), z = D -> D + T)
        #                                          = -decay * porosity(0) * (exp(-(D+T)/decay) - exp(-D/decay))
        #                                          = decay * porosity(0) * exp(-D/decay) * (1 - exp(-T/decay))
        #
        #    average_decompacted_density = density + (1 / T) * (density_water - density) * decay * porosity(0) * exp(-D/decay) * (1 - exp(-T/decay))
        #
        return (density +
                (DENSITY_WATER - density) * porosity_decay * surface_porosity *
                math.exp(-decompacted_depth_to_top / porosity_decay) *
                (1 - math.exp(-decompacted_thickness / porosity_decay)) / decompacted_thickness)


class Well(object):
    """
    Class containing all the stratigraphic units in a well sorted by age (from youngest to oldest).
    """
    
    def __init__(self, attributes=None, stratigraphic_units=None):
        """
        attributes: Optional well attributes to store on well object.
                    If specified then must be a dictionary mapping attribute names to values.
    
        stratigraphic_units: Optional sequence of StratigraphicUnit objects.
                             They can be unsorted (by age) but will be added in sorted order.
        
        Raises ValueError if:
        (1) youngest unit does not have zero depth, or
        (2) adjacent units do not have matching top and bottom ages and depths.
        
        ...this ensures the units are contiguous in depth from the surface (ie, no gaps).
        """
        
        # Add any well attributes requested.
        if attributes is not None:
            for name, value in attributes.iteritems():
                setattr(self, name, value)
        
        self.stratigraphic_units = []
        
        if stratigraphic_units is None:
            return
        
        # Sort by age.
        stratigraphic_units = sorted(stratigraphic_units, key=lambda unit: unit.top_age)
        
        # Add the units in order of age.
        for stratigraphic_unit in stratigraphic_units:
            self._add_compacted_unit(stratigraphic_unit)
    
    def add_compacted_unit(self, top_age, bottom_age, top_depth, bottom_depth, lithology_components, lithologies, other_attributes=None):
        """
        Add the next deeper stratigraphic unit.
        
        Units must be added in order of age.
        
        lithology_components: Sequence of tuples (name, fraction) containing a lithology name and its fraction of contribution.
        
        lithologies: A dict mapping lithology names to lithology.Lithology objects.
        
        other_attributes: Optional dict of attribute name/value pairs to set on stratigraphic unit object (using 'setattr').
    
        Raises ValueError if:
        (1) youngest unit does not have zero depth, or
        (2) adjacent units do not have matching top and bottom ages and depths.
        
        ...this ensures the units are contiguous in depth from the surface (ie, no gaps).
        """
        
        self._add_compacted_unit(
            StratigraphicUnit(top_age, bottom_age, top_depth, bottom_depth, lithology_components, lithologies, other_attributes))
    
    def _add_compacted_unit(self, stratigraphic_unit):
        # If adding first unit then check that it has zero top depth.
        #
        # Note that the top age of the first unit might not be present day (0Ma) though because
        # sedimentation may have ended prior to present day.
        if not self.stratigraphic_units:
            if stratigraphic_unit.top_depth != 0.0:
                raise ValueError('Top stratigraphic unit in well must have zero top depth.')
        
        # Check that adjacent units have matching top and bottom ages and depths.
        if self.stratigraphic_units:
            # Check bottom of last unit add with top of current unit.
            if abs(self.stratigraphic_units[-1].bottom_age - stratigraphic_unit.top_age) > 1e-6:
                raise ValueError('Adjacent stratigraphic units in well must have matching top and bottom ages.')
            if abs(self.stratigraphic_units[-1].bottom_depth - stratigraphic_unit.top_depth) > 1e-6:
                raise ValueError('Adjacent stratigraphic units in well must have matching top and bottom depths.')
        
        self.stratigraphic_units.append(stratigraphic_unit)
    
    def decompact(self):
        """
        Finds decompacted total sediment thickness and tectonic subsidence for each age in stratigraphic units.
        
        Returns: List of DecompactedWell (one per age) in same order (and ages) as the well units (youngest to oldest).
        """
        
        # Each decompacted well represents decompaction at the age of a stratigraphic unit in the well.
        decompacted_wells = []
        
        # Iterate over the stratigraphic units - they are sorted by age (youngest to oldest).
        #
        # Note that the first stratigraphic unit doesn't really need decompaction but we do it anyway
        # (it's quick since it only requires one iteration in the decompacted thickness convergence loop).
        num_stratigraphic_units = len(self.stratigraphic_units)
        for surface_unit_index in xrange(0, num_stratigraphic_units):
            surface_unit = self.stratigraphic_units[surface_unit_index]
            
            decompacted_well = DecompactedWell(surface_unit)
            
            # The total decompacted thickness at the age of the current surface unit -
            # this is age at which deposition ended for the current surface unit.
            total_decompacted_thickness = 0.0
            
            # Starting at the current surface unit, iterate over all units beneath it.
            for unit_index in xrange(surface_unit_index, num_stratigraphic_units):
                unit = self.stratigraphic_units[unit_index]
                
                # Decompact the current unit assuming there is 'total_decompacted_thickness' depth
                # of sediment (from other units) above it.
                unit_decompacted_thickness = unit.calc_decompacted_thickness(total_decompacted_thickness)
                
                # Calculate decompacted density of unit (average density over thickness).
                unit_decompacted_density = unit.calc_decompacted_density(unit_decompacted_thickness, total_decompacted_thickness)
                
                # Record the decompacted thickness and decompacted depth to top in the decompacted well.
                # These are used to incrementally calculate average density of the entire decompacted stratigraphic column
                # (used for isostatic correction).
                decompacted_well.add_decompacted_unit(
                    unit,
                    unit_decompacted_thickness,
                    unit_decompacted_density)
                
                total_decompacted_thickness += unit_decompacted_thickness
            
            decompacted_wells.append(decompacted_well)
        
        return decompacted_wells


class DecompactedStratigraphicUnit(object):
    """
    Class to hold data for a *decompacted* stratigraphic unit (decompacted at a specific age).
    """
    
    def __init__(self, stratigraphic_unit, decompacted_thickness, decompacted_density):
        self.stratigraphic_unit = stratigraphic_unit
        self.decompacted_thickness = decompacted_thickness
        self.decompacted_density = decompacted_density


class DecompactedWell(object):
    """
    Class containing the decompacted well data at a specific age.
    """
    
    def __init__(self, surface_unit):
        """
        surface_unit: The top stratigraphic unit in this decompacted well.
        """
        
        self.surface_unit = surface_unit
        
        self.total_compacted_thickness = 0.0
        self.total_decompacted_thickness = 0.0
        self.decompacted_stratigraphic_units = []
        
        # Private.
        self._total_decompacted_thickness_times_density = 0.0
    
    def add_decompacted_unit(
            self,
            stratigraphic_unit,
            decompacted_thickness,
            decompacted_density):
        """
        Stratigraphic units are decompacted from top of well column to bottom.
        """
        
        self.decompacted_stratigraphic_units.append(
            DecompactedStratigraphicUnit(stratigraphic_unit, decompacted_thickness, decompacted_density))
        
        # Keep track of total compacted thickness (sum of present day thicknesses).
        self.total_compacted_thickness += stratigraphic_unit.bottom_depth - stratigraphic_unit.top_depth
        
        # Cumulative decompacted quantities.
        self.total_decompacted_thickness += decompacted_thickness
        self._total_decompacted_thickness_times_density += decompacted_density * decompacted_thickness
    
    def get_age(self):
        """
        Returns the age of the surface of the decompacted column of the well.
        """
        
        # Return the age of the top of the first stratigraphic unit.
        return self.surface_unit.top_age
    
    def get_average_decompacted_density(self):
        """
        Returns the average density of the entire decompacted column of the well.
        """
        
        if self.total_decompacted_thickness == 0.0:
            raise ValueError('Decompacted well has no decampacted units.')
        
        return self._total_decompacted_thickness_times_density / self.total_decompacted_thickness
    
    def get_sediment_isostatic_correction(self):
        """
        Returns the isostatic correction of this decompacted well.
        
        The returned correction can be added to a known water depth to obtain the deeper isostatically compensated,
        sediment-free water depth (tectonic subsidence). Or the correction could be subtracted from a
        known tectonic subsidence (unloaded water depth) to get the depth at sediment/water interface.
        """
        
        return (self.total_decompacted_thickness *
                (DENSITY_MANTLE - self.get_average_decompacted_density()) /
                (DENSITY_MANTLE - DENSITY_WATER))
    
    def get_min_max_tectonic_subsidence_from_water_depth(self, min_water_depth, max_water_depth, sea_level=None):
        """
        Returns the min/max tectonic subsidence (unloaded water depth) of this decompacted well from its min/max water depth.
        
        The min/max are a result of the min/max paleo water depths.
        
        Optional sea level fluctuation is included if specified.
        """
        
        isostatic_correction = self.get_sediment_isostatic_correction()
        
        if sea_level is not None:
            isostatic_correction -= sea_level * (DENSITY_MANTLE / (DENSITY_MANTLE - DENSITY_WATER))
        
        # Add the isostatic correction to the known (loaded) water depth to obtain the deeper
        # isostatically compensated, sediment-free water depth (tectonic subsidence).
        return min_water_depth + isostatic_correction, max_water_depth + isostatic_correction
    
    def get_water_depth_from_tectonic_subsidence(self, tectonic_subsidence, sea_level=None):
        """
        Returns the water depth of this decompacted well from its tectonic subsidence (unloaded water depth).
        
        The min/max are a result of the min/max paleo water depths.
        
        Optional sea level fluctuation is included if specified.
        """
        
        isostatic_correction = self.get_sediment_isostatic_correction()
        
        if sea_level is not None:
            isostatic_correction -= sea_level * (DENSITY_MANTLE / (DENSITY_MANTLE - DENSITY_WATER))
        
        # Subtract the isostatic correction from the known tectonic subsidence (unloaded water depth)
        # to get the (loaded) water depth at the decompacted sediment/water interface.
        return tectonic_subsidence - isostatic_correction


def read_well_file(
        well_filename,
        lithologies,
        bottom_age_column=0,
        bottom_depth_column=1,
        lithology_column=2,
        other_columns=None,
        well_attributes=None):
    """
    Reads a text file with each row representing a stratigraphic unit.
    
    well_filename: name of well text file.
    
    lithologies: a dict mapping lithology names to lithology.Lithology objects.
    
    other_columns: Optional dict of extra columns (besides age, depth and lithology(s)).
                   Each dict value should be a column index (to read from file) and associated dict key
                   should be a string that will be the name of an attribute (added to each StratigraphicUnit
                   object in the returned Well) containing the value read.
    
    well_attributes: Optional attributes to read from well file metadata and store in returned Well object.
                     If specified then must be a dictionary mapping each metadata name to a 2-tuple containing
                     attribute name and a function to convert attribute string to attribute value.
                     For example, {'SiteLongitude' : ('longitude', float), 'SiteLatitude' : ('latitude', float)}
                     will look for metadata name 'SiteLongitude' and store a float value in Well.longitude
                     (or None if not found), etc.
                     Each metadata not found in well file will store None in the associated attribute of Well object.
    
    Returns: Well
    
    Each attribute to read (eg, bottom_age, bottom_depth, etc) has a column index to direct which column it should be read from.
    
    If file contains 'SurfaceAge = <age>'in commented ('#') lines then the top age of the
    youngest stratigraphic unit will have that age, otherwise it defaults to 0Ma (present day).
    
    Raises ValueError if 'lithology_column' is not the largest column number (must be last column).
    """
    
    if (max(bottom_age_column, bottom_depth_column) >= lithology_column or
        (other_columns is not None and max(other_columns.values()) >= lithology_column)):
        raise ValueError('Lithology columns must be the last column in well text file.')
    
    # All requested well attributes default to None if not found in well file.
    attributes = {}
    for _, (well_attribute_name, _) in well_attributes.iteritems():
        attributes[well_attribute_name] = None
    
    # Attempt to parse the file for the surface age (becomes top age of top stratigraphic unit).
    # If it's not found then it defaults to zero (present day).
    surface_age = 0.0
    
    stratigraphic_units = []
    with open(well_filename, 'rU') as well_file:
        for line_number, line in enumerate(well_file):
        
            # Make line number 1-based instead of 0-based.
            line_number = line_number + 1
            
            # Split the line into strings (separated by whitespace).
            line_string_list = line.split()
            
            num_strings = len(line_string_list)
            
            # If just a line containing white-space then skip to next line.
            if num_strings == 0:
                continue
            
            # If line starts with '#' then search for well metadata and then skip to next line.
            if line_string_list[0].startswith('#'):
                comment = line[1:]
                # See if comment contains "name=value".
                comment_data = comment.split('=')
                # See if it's a metadata line (has a single '=' char).
                if len(comment_data) == 2:
                    name = comment_data[0].strip()  # Note: Case-insensitive comparison.
                    value = comment_data[1].strip()
                    
                    # See if current line contains a well attribute requested by caller.
                    if name in well_attributes:
                        attribute_name, attribute_conversion = well_attributes[name]
                        try:
                            attributes[attribute_name] = attribute_conversion(value)
                        except Exception as exc:
                            print('WARNING: Line {0} of "{1}": Ignoring {2}: {3}.' .format(
                                  line_number, well_filename, name, exc), file=sys.stderr)
                    
                    # else read 'SurfaceAge'...
                    elif name == 'SurfaceAge':
                        try:
                            age = float(value)
                            if age < 0:
                                raise ValueError
                            surface_age = age
                        except ValueError:
                            print('WARNING: Line {0} of "{1}": Ignoring SurfaceAge: '
                                  '{2} is not a number >= 0.' .format(line_number, well_filename, value),
                                  file=sys.stderr)
                
                continue
            
            # The number of columns must include the lithology name and fraction
            # (starting with lithology column - extra strings if more than one lithology component).
            if num_strings < lithology_column + 2:
                print('WARNING: Line {0} of "{1}": Ignoring lithology: line does not have at least '
                      '{2} white-space separated strings.'.format(line_number, well_filename, lithology_column + 2),
                      file=sys.stderr)
                continue
            
            # Need an odd number of strings per line (each lithology component is 2 strings).
            if ((num_strings - lithology_column) % 2) == 1:
                print('WARNING: Line {0} of "{1}": Ignoring lithology: each extra lithology must have two '
                      'strings (name and fraction).'.format(line_number, well_filename),
                      file=sys.stderr)
                continue
            
            # Attempt to read/convert the column strings.
            try:
                bottom_age = float(line_string_list[bottom_age_column])
                bottom_depth = float(line_string_list[bottom_depth_column])
                
                # Read the lithology components (name, fraction) pairs.
                lithology_components = []
                num_lithology_components = (num_strings - lithology_column) / 2
                for index in range(num_lithology_components):
                    name = line_string_list[lithology_column + 2 * index]
                    fraction = float(line_string_list[lithology_column + 2 * index + 1])
                    lithology_components.append((name, fraction))
            except ValueError:
                print('WARNING: Line {0} of "{1}": Ignoring stratigraphic unit: cannot '
                      'read age/depth/lithology values.' .format(line_number, well_filename),
                      file=sys.stderr)
                continue
            
            # Read any extra columns if requested.
            other_attributes = None
            if other_columns is not None:
                other_attributes = {}
                try:
                    for column_name, column in other_columns.iteritems():
                        column_value = float(line_string_list[column])
                        other_attributes[column_name] = column_value
                except ValueError:
                    print('WARNING: Line {0} of "{1}": Ignoring stratigraphic unit: cannot read {2} '
                          'value at column index {3}.' .format(line_number, well_filename, column_name, column),
                          file=sys.stderr)
                    continue
            
            stratigraphic_units.append((bottom_age, bottom_depth, lithology_components, other_attributes))
    
    well = Well(attributes)
    
    if stratigraphic_units:
        # Sort the units in order of age (the first entry in each tuple in list of units).
        stratigraphic_units = sorted(stratigraphic_units, key=lambda unit: unit[0])
        
        # Add youngest stratigraphic unit (the unit on the surface).
        surface_unit_bottom_age, surface_unit_bottom_depth, surface_unit_lithology_components, surface_unit_other_attributes = stratigraphic_units[0]
        surface_unit_top_age = surface_age
        surface_unit_top_depth = 0.0
        well.add_compacted_unit(
            surface_unit_top_age, surface_unit_bottom_age,
            surface_unit_top_depth, surface_unit_bottom_depth,
            surface_unit_lithology_components, lithologies,
            surface_unit_other_attributes)
        
        # Add the remaining units in order of age (starting with second youngest).
        for unit_index in range(1, len(stratigraphic_units)):
            # Bottom age and depth recorded for stratigraphic unit.
            bottom_age, bottom_depth, lithology_components, other_attributes = stratigraphic_units[unit_index]
            # Top age and depth is same as bottom age and depth of next younger stratigraphic unit.
            top_age, top_depth, _, _ = stratigraphic_units[unit_index - 1]
            
            well.add_compacted_unit(
                top_age, bottom_age,
                top_depth, bottom_depth,
                lithology_components, lithologies,
                other_attributes)
    
    return well


def write_well_file(well, well_filename, other_column_attribute_names=None, well_attributes=None):
    """
    Write a text file with each row representing a stratigraphic unit.
    
    well: The well to write.
    
    well_filename: Name of well text file.
    
    other_column_attribute_names: Names of any extra column attributes to write as column before the lithology(s) column.
    
    well_attributes: Optional attributes in Well object to write to well file metadata.
                     If specified then must be a dictionary mapping each attribute name to a metadata name.
                     For example, {'longitude' : 'SiteLongitude', 'latitude' : 'SiteLatitude'}.
                     will write well.longitude (if not None) to metadata 'SiteLongitude', etc.
                     Not that the attributes must exist in 'well' (but can be set to None).
    """
    
    if not well.stratigraphic_units:
        return
    
    with open(well_filename, 'w') as well_file:
        
        # Write the well metadata.
        write_well_metadata(well_file, well, well_attributes)
        
        # All column names.
        column_names = ['bottom_age', 'bottom_depth']
        if other_column_attribute_names:
            column_names.extend(other_column_attribute_names)
        column_names.append('lithology')
        
        field_width = 9
        
        # Write the column names.
        column_widths = []
        well_file.write('#\n')
        for column_index, column_name in enumerate(column_names):
            if column_index == 0:
                column_name_format_string = '## {0:<{width}}'
            else:
                column_name_format_string = ' {0:<{width}}'
            
            column_width = max(field_width, len(column_name))
            column_widths.append(column_width)
            
            well_file.write(column_name_format_string.format(column_name, width=column_width))
        
        well_file.write('\n')
        
        # Write each stratigraphic unit as a single line.
        for stratigraphic_unit in well.stratigraphic_units:
            # Write bottom age and depth.
            well_file.write('   {0:<{width}.3f}'.format(stratigraphic_unit.bottom_age, width=column_widths[0]))
            well_file.write(' {0:<{width}.3f}'.format(stratigraphic_unit.bottom_depth, width=column_widths[1]))
            
            # Write any other column attributes.
            if other_column_attribute_names:
                for other_column_attribute_index, other_column_attribute_name in enumerate(other_column_attribute_names):
                    column_attribute_value = getattr(stratigraphic_unit, other_column_attribute_name)
                    well_file.write(' {0:<{width}.3f}'.format(column_attribute_value, width=column_widths[2 + other_column_attribute_index]))
            
            # Write the lithology components.
            for lithology_name, fraction in stratigraphic_unit.lithology_components:
                well_file.write(' {0:<15} {1:<10.2f}'.format(lithology_name, fraction))
            
            well_file.write('\n')


def write_well_metadata(well_file, well, well_attributes=None):
    """
    Write well metadata to file object 'well_file'.
    
    well: The well to extract metadata from.
    
    well_attributes: Optional attributes in Well object to write to well file metadata.
                     If specified then must be a dictionary mapping each attribute name to a metadata name.
                     For example, {'longitude' : 'SiteLongitude', 'latitude' : 'SiteLatitude'}.
                     will write well.longitude (if not None) to metadata 'SiteLongitude', etc.
                     Not that the attributes must exist in 'well' (but can be set to None).
    """
    
    # List of 2-tuples of metadata to write to file.
    metadata = []
    
    if well_attributes:
        # Add any requested well attributes (if they are not None).
        for well_attribute_name, well_metadata_name in well_attributes.iteritems():
            well_attribute_value = getattr(well, well_attribute_name)
            if well_attribute_value is not None:
                metadata.append((well_metadata_name, well_attribute_value))
    
    # Add the age of total sediment surface.
    # This is a well metadata that is not stored in a well attribute.
    surface_age = well.stratigraphic_units[0].top_age
    metadata.append(('SurfaceAge', surface_age))
    
    # Write the metadata (sorted by name).
    for well_metadata_name, well_metadata_value in sorted(metadata):
        well_file.write('# {0} = {1:.4f}\n'.format(well_metadata_name, well_metadata_value))

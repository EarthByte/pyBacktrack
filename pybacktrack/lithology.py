
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


####################################################################
# Read lithologies from a text file with the following format:
#
# # Columns:
# # name                            density   porosity      decay
# #                                   kg/m3                     m
# #
# Anhydrite                            2960        0.4        500
# Basalt                               2700        0.2       2500
#
####################################################################


from __future__ import print_function
import sys


class Lithology(object):
    """
    Class to specify lithology data.
    """
    
    def __init__(self, density, surface_porosity, porosity_decay):
        self.density = density
        self.surface_porosity = surface_porosity
        self.porosity_decay = porosity_decay


def read_lithologies_file(lithologies_filename):
    """
    Reads a text file with each row representing lithology parameters.
    
    The parameter columns are: name density surface_porosity porosity_decay
    
    Units of density are kg/m3 and units of porosity decay are m.
    
    lithologies_filename: name of lithologies text file.
    
    Returns: Dictionary mapping lithology names to Lithology objects.
    """
    
    lithologies = {}
    with open(lithologies_filename, 'rU') as lithologies_file:
        for line_number, line in enumerate(lithologies_file):

            # Make line number 1-based instead of 0-based.
            line_number = line_number + 1

            # Split the line into strings (separated by whitespace).
            line_string_list = line.split()

            # If just a line containing white-space, or starts with '#' or '>', then skip to next line.
            if (not line_string_list or
                line_string_list[0].startswith('#') or
                line_string_list[0].startswith('>')):
                continue
            
            # Need 4 strings per line (for name, density, porosity and decay).
            # If have more than 4 strings then 5th string should be a comment (ie, start with '#').
            if (len(line_string_list) < 4 or
                (len(line_string_list) > 4 and not line_string_list[4].startswith('#'))):
                print('Line {0} of "{1}": Ignoring lithology: line does not have 4 white-space '
                      'separated strings.'.format(line_number, lithologies_filename),
                      file=sys.stderr)
                continue
                
            # Attempt to read/convert the strings.
            try:
                name = line_string_list[0]
                density = float(line_string_list[1])
                surface_porosity = float(line_string_list[2])
                porosity_decay = float(line_string_list[3])
            except ValueError:
                print('Line {0} of "{1}": Ignoring lithology: cannot read name/density/porosity/decay '
                      'values.'.format(line_number, lithologies_filename),
                      file=sys.stderr)
                continue

            lithologies[name] = Lithology(density, surface_porosity, porosity_decay)
    
    return lithologies


def create_lithology(lithology_name, lithologies):
    """
    Looks up a lithology in 'lithologies' using a lithology name.
    
    lithology_name: Lithology name (string).
    
    lithologies: a dict mapping lithology names to Lithology objects.
    
    Returns: Lithology.
    
    Raises KeyError if 'lithology_name' is not found in 'lithologies'.
    """
    
    return lithologies[lithology_name]


def create_lithology_from_components(components, lithologies):
    """
    Creates a combined lithology (if necessary) from multiple weighted lithologies.
    
    components: Sequence of tuples (name, fraction) containing a lithology name and its fraction of contribution.
    
    lithologies: a dict mapping lithology names to Lithology objects.
    
    Returns: Lithology.
    
    Raises ValueError if all fractions do not add up to 1.0.
    Raises KeyError if a lithology name is not found in 'lithologies'.
    """
    
    density = 0
    surface_porosity = 0
    porosity_decay = 0
    total_fraction = 0
    for name, fraction in components:
        lithology = lithologies.get(name)
        if not lithology:
            raise KeyError('Lithology name "{0}" does not exist in lithology dictionary.'.format(name))
        
        density += fraction * lithology.density
        surface_porosity += fraction * lithology.surface_porosity
        porosity_decay += fraction * lithology.porosity_decay
        total_fraction += fraction
    
    # Make sure total fraction adds up to one.
    if total_fraction < 1 - 1e-6 or total_fraction > 1 + 1e-6:
        raise ValueError('Lithology fractions do not add up to one for {0}.'.format(components))
    
    return Lithology(density, surface_porosity, porosity_decay)

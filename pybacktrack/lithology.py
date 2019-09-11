
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


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import pybacktrack.bundle_data
import os.path
import warnings


DEFAULT_BASE_LITHOLOGY_NAME = 'Shale'
"""Default name of the lithology of the stratigraphic unit at the base of the well."""


class Lithology(object):
    """
    Class containing lithology data.
    """
    
    def __init__(self, density, surface_porosity, porosity_decay):
        """
        Create a lithology from density, surface porosity and porosity decay.
        
        Parameters
        ----------
        density : float
            Density (in kg/m3).
        surface_porosity : float
            Surface porosity (unit-less).
        porosity_decay : float
            Porosity decay (in metres).
        """
        
        self.density = density
        self.surface_porosity = surface_porosity
        self.porosity_decay = porosity_decay


def read_lithologies_file(lithologies_filename):
    """
    Reads a text file with each row representing lithology parameters.
    
    Parameters
    ----------
    lithologies_filename : str
        Filename of the lithologies text file.
    
    Returns
    -------
    dict
        Dictionary mapping lithology names to :class:`pybacktrack.Lithology` objects.
    
    Notes
    -----
    The four parameter columns in the lithologies text file should contain:
    
    #. name
    #. density
    #. surface_porosity
    #. porosity_decay
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
                warnings.warn('Line {0} of "{1}": Ignoring lithology: line does not have 4 white-space '
                              'separated strings.'.format(line_number, lithologies_filename))
                continue
                
            # Attempt to read/convert the strings.
            try:
                name = line_string_list[0]
                density = float(line_string_list[1])
                surface_porosity = float(line_string_list[2])
                porosity_decay = float(line_string_list[3])
            except ValueError:
                warnings.warn('Line {0} of "{1}": Ignoring lithology: cannot read name/density/porosity/decay '
                              'values.'.format(line_number, lithologies_filename))
                continue

            lithologies[name] = Lithology(density, surface_porosity, porosity_decay)
    
    return lithologies


def read_lithologies_files(lithologies_filenames):
    """
    Reads each lithologies text file in the sequence and merges their lithologies.
    
    Parameters
    ----------
    lithologies_filenames : sequence of str
        Filenames of the lithologies text files.
    
    Returns
    -------
    dict
        Dictionary mapping lithology names to :class:`pybacktrack.Lithology` objects.
    
    Notes
    -----
    The four parameter columns in each lithologies text file should contain:
    
    #. name
    #. density
    #. surface_porosity
    #. porosity_decay
    
    The order of filenames is important. If a lithology name exists in multiple files
    but has different definitions (values for density, surface porosity and porosity decay) then
    the definition in the last file containing the lithology name is used.
    
    .. versionadded:: 1.2
    """
    
    lithologies = {}
    
    # Read all the lithology files and merge their dicts.
    # Subsequently specified files override previous files in the list.
    # So if the first and second files have the same lithology then the second lithology is used.
    for lithologies_filename in lithologies_filenames:
        lithologies.update(read_lithologies_file(lithologies_filename))
    
    return lithologies


def create_lithology(lithology_name, lithologies):
    """
    Looks up a lithology using a name.
    
    Parameters
    ----------
    lithology_name : str
        The name of the lithology to look up.
    lithologies : dict
        A dictionary mapping lithology names to :class:`pybacktrack.Lithology` objects.
    
    Returns
    -------
    :class:`pybacktrack.Lithology`
        The lithology matching ``lithology_name``.
    
    Raises
    ------
    KeyError
        If ``lithology_name`` is not found in ``lithologies``.
    """
    
    return lithologies[lithology_name]


def create_lithology_from_components(components, lithologies):
    """
    Creates a combined lithology (if necessary) from multiple weighted lithologies.
    
    Parameters
    ----------
    components : sequence of tuples
        A sequence (eg, ``list``) of tuples (str, float) containing a lithology name and its fraction of contribution.
    lithologies : dict
        A dictionary mapping lithology names to :class:`pybacktrack.Lithology` objects.
    
    Returns
    -------
    :class:`pybacktrack.Lithology`
        The combined lithology.
    
    Raises
    ------
    ValueError
        If all fractions do not add up to 1.0.
    KeyError
        If a lithology name is not found in ``lithologies``.
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


#################################################################
# For command-line parsing in "backtrack.py" and "backstrip.py" #
#################################################################

# Bundled short lithology names are the bundled filenames with directory and extension removed, and lower case.
def _convert_bundled_lithology_to_short_name(bundled_lithology_filename):
    return os.path.basename(os.path.splitext(bundled_lithology_filename)[0]).lower()


DEFAULT_BUNDLED_LITHOLOGY_SHORT_NAME = _convert_bundled_lithology_to_short_name(pybacktrack.bundle_data.DEFAULT_BUNDLE_LITHOLOGY_FILENAME)
BUNDLED_LITHOLOGY_SHORT_NAMES = [
    _convert_bundled_lithology_to_short_name(filename) for filename in pybacktrack.bundle_data.BUNDLE_LITHOLOGY_FILENAMES]

# Create a dict mapping these short names to the actual filenames in the bundle.
bundled_lithology_filenames_dict = dict(
    (_convert_bundled_lithology_to_short_name(filename), filename) for filename in pybacktrack.bundle_data.BUNDLE_LITHOLOGY_FILENAMES)


# Action to parse lithology files (bundled and user-specified).
class ArgParseLithologyAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        
        lithology_filenames = []
        
        for value in values:
            # First see if lithology filename matches the short name of a bundled lithology file, otherwise interpret as a filename.
            if value.lower() in bundled_lithology_filenames_dict:
                lithology_filenames.append(bundled_lithology_filenames_dict[value.lower()])
            else:
                lithology_filenames.append(value)
        
        setattr(namespace, self.dest, lithology_filenames)


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


#######################################################################################
# Convert a Python source code file containing a lithology dictionary to a text file. #
#######################################################################################

# The lithology dictionary is a Python source file containing lines like:
#
#
# lithology_prop = {}
# lithology_prop["Anhydrite"] = {"porosity":0.40,"density":2960,"decay":500}
# lithology_prop["Basalt"] = {"porosity":0.20,"density":2700,"decay":2500}
#
from lithology_dictionary import lithology_prop

# Write the 'name density porosity decay' for each lithology to a text file that can then be read by Python source code.
with open('lithologies.txt', 'w') as output_file:
    data_line_format = '{0:<30} {1:>10} {2:>10} {3:>10}\n'
    
    # Write header.
    output_file.write('# Lithologies.\n')
    output_file.write('#\n')
    output_file.write('# Columns:\n')
    output_file.write(data_line_format.format('# name', 'density', 'porosity', 'decay'))
    output_file.write(data_line_format.format('#', 'kg/m3', '', 'm'))
    output_file.write('#\n')
    
    # Write data.
    for name, lith in sorted(lithology_prop.items()):
        output_file.write(data_line_format.format(name, lith['density'], lith['porosity'], lith['decay']))

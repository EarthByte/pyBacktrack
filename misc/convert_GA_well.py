
#
# Copyright (C) 2019 The University of Sydney, Australia
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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import sys


def convert(
        input_filename):
    """Convert a Geoscience Australia (GA) well file to a pyBacktrack well file.
    
    The output filename is determined from the name of the well inside the input GA filename."""
    
    # Regular expression for extracting the min/max water depths from the WATER_DEPTHS column string.
    #
    # Eg, "-50 (-200 to 0) metres above sea-level" should produce min/max water depths of -200 and 0.
    re_water_depths = re.compile('.*\((.*) to (.*)\).*')
    
    # Read the input GA file.
    well_name = None
    well_data = []
    with open(input_filename, 'rU') as input_file:
        found_well_header = False
        for line_number, line in enumerate(input_file):
            
            # Make line number 1-based instead of 0-based.
            line_number = line_number + 1
            
            # Split the line into strings (separated by commas).
            line_string_list = [column.strip() for column in line.split(',')]
            
            num_strings = len(line_string_list)
            
            # If just a line containing white-space then skip to next line.
            if num_strings == 0:
                continue
            
            if (line_string_list[0] == 'WELL NAME'):
                found_well_header = True
                try:
                    # Get the column indices for the columns we're interested in.
                    top_depth_column_index = line_string_list.index('TOP DEPTH(m)')
                    base_depth_column_index = line_string_list.index('BASE DEPTH(m)')
                    top_age_column_index = line_string_list.index('TOP AGE(Ma)')
                    base_age_column_index = line_string_list.index('BASE AGE(Ma)')
                    water_depths_column_index = line_string_list.index('WATER_DEPTHS')
                    environment_column_index = line_string_list.index('ENVIRONMENT')
                except ValueError:
                    # Raise a more informative error message.
                    raise ValueError('Cannot find expected column header names at line {0} of input file {1}.'.format(
                                     line_number, input_filename))
                
                continue
            
            # If haven't reached well data yet so continue.
            if not found_well_header:
                continue
            
            # Read the current row data.
            try:
                if well_name is None:
                    # This is first row after header, so get the well name.
                    well_name = line_string_list[0]
                elif line_string_list[0] != well_name:
                    # Each row should start with the well name, if not then we've reached the end of the well data.
                    break
                
                # Read the well row data.
                top_depth = float(line_string_list[top_depth_column_index] if line_string_list[top_depth_column_index] else 'nan')
                base_depth = float(line_string_list[base_depth_column_index] if line_string_list[base_depth_column_index] else 'nan')
                top_age = float(line_string_list[top_age_column_index] if line_string_list[top_age_column_index] else 'nan')
                base_age = float(line_string_list[base_age_column_index] if line_string_list[base_age_column_index] else 'nan')
                
                # Extract min/max water depths from WATER_DEPTHS column string.
                water_depths = line_string_list[water_depths_column_index]
                match_water_depths = re_water_depths.match(water_depths)
                min_water_depth = float(match_water_depths.group(1))
                max_water_depth = float(match_water_depths.group(2))
                
                environment = line_string_list[environment_column_index]
                # Replace whitespaces with '_'.
                environment = '_'.join(environment.split())
                
                well_data.append((top_depth, base_depth, top_age, base_age, min_water_depth, max_water_depth, environment))
            except (ValueError, IndexError):
                # Raise a more informative error message.
                raise ValueError('Cannot read well values at line {0} of input file {1}.'.format(line_number, input_filename))
    
    # Sort the well layers by their base depth.
    well_data.sort(key = lambda well_row: well_row[1])
    
    if not well_name:
        raise ValueError('Cannot find well data in input file {0}.'.format(input_filename))
    
    # The output pyBacktrack well filename is obtained from the well name (with whitespaces replaced by '-').
    output_filename = '-'.join(well_name.split()) + '.txt'
    
    # Write the output pyBacktrack file.
    with open(output_filename, 'w') as output_file:
        output_file.write('## bottom_age bottom_depth min_water_depth max_water_depth lithology\n')
        for top_depth, base_depth, top_age, base_age, min_water_depth, max_water_depth, environment in well_data:
            output_file.write('   {0:<10.3f} {1:<12.3f} {2:<15.3f} {3:<15.3f} {4:<15} {5:<10.2f}\n'.format(base_age, base_depth, min_water_depth, max_water_depth, environment, 1.0))


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
    
    
    def main():
        
        __description__ = """Convert one or more Geoscience Australia (GA) well files to pyBacktrack well files.
    
    Each output filename is determined from the name of the well inside each input GA filename.
    
    NOTE: Separate the positional and optional arguments with '--' (workaround for bug in argparse module).
    For example...

    python %(prog)s ... -- GA_well_1.csv GA_well_2.csv
    """
    
        #
        # Gather command-line options.
        #
        
        # The command-line parser.
        parser = argparse.ArgumentParser(description=__description__, formatter_class=argparse.RawDescriptionHelpFormatter)
        
        parser.add_argument(
            'GA_well_filenames', type=argparse_unicode, nargs='+',
            help='Filenames of one or more GA wells to convert.')
        
        # Parse command-line options.
        args = parser.parse_args()
        
        # Convert each GA well file.
        for GA_well_filename in args.GA_well_filenames:
            convert(GA_well_filename)
        
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

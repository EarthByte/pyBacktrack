
#
# Copyright (C) 2023 The University of Sydney, Australia
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

"""Convert stratigraphic depths (metres) to age (Ma) using an depth-to-age model.

:func:`pybacktrack.convert_stratigraphic_depth_to_age` converts a single stratigraphic depth to an age.

:func:`pybacktrack.convert_stratigraphic_depth_to_age_files` converts a sequence of stratigraphic depths (read from an input file) to ages
(and writes both ages and depths, and any lithologies in the input file, to an output file).
"""


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import math
import pybacktrack.bundle_data
import pybacktrack.version
from pybacktrack.util.interpolate import read_curve_function
import sys
import warnings


def convert_stratigraphic_depth_to_age(
        depth,
        depth_to_age_model):
    """convert_stratigraphic_depth_to_age(age, depth_to_age_model)
    Convert stratigraphic depth to age using a specified depth-to-age model.
    
    Parameters
    ----------
    depth : float
        The stratigraphic depth in metres.
    depth_to_age_model : function
        The model to use when converting stratigraphic depth to age.
        A callable function accepting a single non-negative depth parameter (in metres) and returning age (in Ma).
    
    Returns
    -------
    float
        Age (in Ma) as a positive number.
    
    Raises
    ------
    ValueError
        If `depth` is negative.
    TypeError
        If `model` is not a function accepting a single parameter.
        
    Notes
    -----
    .. versionadded:: 1.5
    """
    
    if depth < 0:
        raise ValueError('Stratigraphic depth must be non-negative')
    
    return depth_to_age_model(depth)


def convert_stratigraphic_depth_to_age_files(
        input_filename,
        output_filename,
        depth_to_age_model,
        reverse_output_columns=False):
    """convert_stratigraphic_depth_to_age_files(input_filename, output_filename, depth_to_age_model, reverse_output_columns=False)
    Converts stratigraphic depth to age by reading `depth` rows (in first column) from input file and writing rows containing both `age` and `depth` to output file.
    
    Parameters
    ----------
    input_filename : string
        Name of input text file containing the `depth` values.
        A single `depth` value is obtained from each row by indexing the first column.
    output_filename : string
        Name of output text file containing `age` and `depth` values.
        Each row of output file contains an `age` value and its associated `depth` value (with order depending on `reverse_output_columns`).
    model : function
        The model to use when converting stratigraphic depth to age.
        A callable function accepting a single non-negative depth parameter (in metres) and returning age (in Ma).
    reverse_output_columns : bool, optional
        Determines order of `age` and `depth` columns in output file.
        If `True` then output `depth age`, otherwise output `age depth`.
    
    Raises
    ------
    ValueError
        If cannot read `depth` value, as a floating-point number, from input file in the first column.
    ValueError
        If stratigraphic depths are not monotonically increasing.
        
    Notes
    -----
    .. versionadded:: 1.5
    """
    
    with open(input_filename, 'r') as input_file, open(output_filename, 'w') as output_file:

        metadata_lines = []

        encountered_data = False
        last_depth = None  # used to ensure depths are monotonically increasing
        data_lines = []

        for line_number, line in enumerate(input_file):
            
            # Make line number 1-based instead of 0-based.
            line_number = line_number + 1
            
            # Split the line into strings (separated by whitespace).
            line_string_list = line.split()
            
            num_strings = len(line_string_list)
            
            # If line only contains white-space or is a comment then ignore and then skip to next line.
            if (num_strings == 0 or
                line_string_list[0].startswith('#') or
                line_string_list[0].startswith('>')):

                # If still in the top metadata part of the file then record the metadata.
                if not encountered_data:
                    metadata_lines.append(line)
                
                continue

            encountered_data = True
            
            # Read depth.
            try:
                depth = float(line_string_list[0])
            except ValueError:
                # Raise a more informative error message.
                raise ValueError('Cannot read depth value at line {0} of input file {1}.'.format(
                                 line_number, input_filename))

            # Make sure depths are monotonically increasing.
            if last_depth is not None and last_depth > depth:
                raise ValueError('Stratigraphic depths should be monotonically increasing. '
                                    'The depth value {} at line {} of input file {} is less than the previous depth {}.'.format(
                                    depth, line_number, input_filename, last_depth))
            last_depth = depth
            
            # Convert depth to age.
            age = convert_stratigraphic_depth_to_age(depth, depth_to_age_model)
            
            if reverse_output_columns:
                output_row = depth, age
            else:
                output_row = age, depth
            
            # Extract the rest of the line starting at the second column (first column is depth).
            # This will also get written to the output file.
            extra_columns_text = line.split(maxsplit=1)[1].rstrip()

            # The formatted output data line.
            data_lines.append('  {}\n'.format(
                    '{1:<20.3f}{2:<20.3f}{0}'.format(extra_columns_text, *output_row).rstrip(' ')))
        
        # Write the metadata lines.
        output_file.write(''.join(metadata_lines))

        # Write the column header.
        if reverse_output_columns:
            column_header = 'depth', 'age'
        else:
            column_header = 'age', 'depth'
        output_file.write('\n{}\n'.format(
                '# {0:<20}{1:<20}'.format(*column_header).rstrip(' ')))

        # Write the data lines.
        output_file.write(''.join(data_lines))


# Action to parse a depth-to-age model.
class ArgParseAgeModelAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        model = None
        
        if not (len(values) == 1 or len(values) == 3):
            parser.error('depth-to-age model must be a depth-to-age model filename, and optional age and depth column indices')
        
        # Read 2-column text file to get a function of age(depth).
        depth_to_age_model_filename = values[0]
        
        if len(values) == 3:
            # User-specified age and depth column indices.
            try:
                age_column_index = int(values[1])
                depth_column_index = int(values[2])
                if age_column_index < 0 or depth_column_index < 0:
                    parser.error('age and depth column indices must be non-negative')
            except ValueError:
                raise argparse.ArgumentTypeError("encountered an age or depth column index that is not an integer")
        else:
            # Default age and depth column indices.
            age_column_index = 0
            depth_column_index = 1
        
        # Read the model age(depth) where 'x' is depth and 'y' is age (in the returned function y=f(x)).
        model, _, _ = read_curve_function(depth_to_age_model_filename, depth_column_index, age_column_index)
        
        setattr(namespace, self.dest, model)


########################
# Command-line parsing #
########################

def main():
    
    __description__ = \
        """Converts rows containing stratigraphic depth (in first column) in input file to rows containing age and depth in output file.

        It also retains any extra column data from the input file (into the output file) such as lithologies,
        as well as retaining any metadata at the top of the input file.
        
        The depth-to-age model can be chosen using the '-m' option.
        It is a depth-to-age model filename optionally followed by two integers representing the age and depth column indices
        (defaulting to 0 and 1 respectively), where the file should contain at least two columns (one containing the age and the other the depth).
        
        
        NOTE: Separate the positional and optional arguments with '--' (workaround for bug in argparse module).
        For example...

        python -m pybacktrack.stratigraphic_depth_to_age_cli -m age_depth_model.xy -- depth_points.xy age_depth_points.xy
        """

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
    
    #
    # Gather command-line options.
    #
    
    # The command-line parser.
    parser = argparse.ArgumentParser(description=__description__, formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument('--version', action='version', version=pybacktrack.version.__version__)
    
    parser.add_argument(
        '-m', '--model', nargs='+', action=ArgParseAgeModelAction,
        metavar='model_parameter',
        help='The model used to convert depth to age. '
             'The first parameter is a depth-to-age model filename containing at least two columns (one containing the age and the other the depth). '
             'The filename can optionally be followed by two integers representing the age and depth column indices '
             '(if not specified then they default to 0 and 1 respectively).')
    
    parser.add_argument(
        '-r', '--reverse_output_columns', action='store_true',
        help='Reverse the order of output columns to output as "depth age". Defaults to "age depth".')
    
    parser.add_argument(
        'input_filename', type=argparse_unicode,
        metavar='input_filename',
        help='The input filename containing the "depth" values.')
    
    parser.add_argument(
        'output_filename', type=argparse_unicode,
        metavar='output_filename',
        help='The output filename containing the converted "age" values (and associated depth values).')
    
    # Parse command-line options.
    args = parser.parse_args()
    
    convert_stratigraphic_depth_to_age_files(
        args.input_filename,
        args.output_filename,
        args.model,
        args.reverse_output_columns)


if __name__ == '__main__':

    import traceback
    
    def warning_format(message, category, filename, lineno, file=None, line=None):
        # return '{0}:{1}: {1}:{1}\n'.format(filename, lineno, category.__name__, message)
        return '{0}: {1}\n'.format(category.__name__, message)

    # Print the warnings without the filename and line number.
    # Users are not going to want to see that.
    warnings.formatwarning = warning_format
    
    #
    # User should use 'stratigraphic_depth_to_age_cli' module (instead of this module 'stratigraphic_depth_to_age'), when executing as a script, to avoid Python 3 warning:
    #
    #   RuntimeWarning: 'pybacktrack.stratigraphic_depth_to_age' found in sys.modules after import of package 'pybacktrack',
    #                   but prior to execution of 'pybacktrack.stratigraphic_depth_to_age'; this may result in unpredictable behaviour
    #
    # For more details see https://stackoverflow.com/questions/43393764/python-3-6-project-structure-leads-to-runtimewarning
    #
    # Importing this module (eg, 'import pybacktrack.stratigraphic_depth_to_age') is fine though.
    #
    warnings.warn("Use 'python -m pybacktrack.stratigraphic_depth_to_age_cli ...', instead of 'python -m pybacktrack.stratigraphic_depth_to_age ...'.", DeprecationWarning)

    try:
        main()
        sys.exit(0)
    except Exception as exc:
        print('ERROR: {0}'.format(exc), file=sys.stderr)
        # Uncomment this to print traceback to location of raised exception.
        # traceback.print_exc()
        sys.exit(1)

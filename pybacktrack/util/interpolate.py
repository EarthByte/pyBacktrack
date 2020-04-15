#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

"""Interpolate a sequence of linear segments read from a 2-column file at values read from a 1-column file.

:func:`read_curve_function` reads x and y columns from a curve file and returns a function y(x) that linearly interpolates.

:func:`interpolate_file` interpolates a `curve_function` at `x` positions, read from input file, and stores both `x` and interpolated `y` values to output file.
"""


from __future__ import print_function
import pybacktrack.version
import math
import scipy.interpolate
import sys


def read_curve_function(
        curve_filename,
        x_column_index=0,
        y_column_index=1):
    """Read x and y columns from a curve file and return a function y(x) that linearly interpolates.
    
    Parameters
    ----------
    curve_filename : string
        Name of input text file containing the `x` and `y` data from which to create the returned curve function.
    x_column_index : int, optional
        Determines which column of input text file to read `x` values from.
    y_column_index : int, optional
        Determines which column of input text file to read `y` values from.
    
    Returns
    -------
    curve_function : function
        A callable function `y=f(x)` accepting a single `x` argument and returning a `y` value.
    x_column : list of float
        The `x` values read from the curve file.
    y_column : list of float
        The `y` values read from the curve file.
    
    Raises
    ------
    ValueError
        If cannot read x and y columns, as floating-point numbers, from the curve file at column indices `x_column_index` and `y_column_index`.
    ValueError
        If curve file contains no data.
    
    Notes
    -----
    The returned `x` and `y` columns are useful if integrating the curve function with ``scipy.integrate.quad``
    (since can pass x column to its `points` argument and `len(x)` to its `limit`).
    """
    
    # Each row in each file should have at least a minimum number of columns.
    min_num_columns = max(x_column_index, y_column_index) + 1
    
    x_column = []
    y_column = []
    xmin, xmax = None, None
    with open(curve_filename, 'r') as curve_file:
        for line_number, line in enumerate(curve_file):
            
            # Make line number 1-based instead of 0-based.
            line_number = line_number + 1
            
            # Split the line into strings (separated by whitespace).
            line_string_list = line.split()
            
            num_strings = len(line_string_list)
            
            # If just a line containing white-space then skip to next line.
            if num_strings == 0:
                continue
            
            # If line is a comment then ignore and then skip to next line.
            if (line_string_list[0].startswith('#') or
                line_string_list[0].startswith('>')):
                continue
            
            if num_strings < min_num_columns:
                raise ValueError('Curve file "{0}" does not have at least {1} columns at line {2}.'.format(
                                 curve_filename, min_num_columns, line_number))

            # Attempt to convert each string into a floating-point number.
            try:
                x = float(line_string_list[x_column_index])
                y = float(line_string_list[y_column_index])
            except ValueError:
                # Raise a more informative error message.
                raise ValueError('Cannot read x/y values at line {0} of curve file {1}.'.format(
                                 line_number, curve_filename))
            
            x_column.append(x)
            y_column.append(y)
            
            # Track the y values of the two endpoints (ie, min/max x).
            if xmin is None or x < xmin:
                xmin = x
                y_xmin = y
            if xmax is None or x > xmax:
                xmax = x
                y_xmax = y
    
    # Raise error if no data.
    if not x_column:
        raise ValueError('Curve file {0} contains no data.'.format(curve_filename))
    
    # Function will return (y_xmin, y_xmax) fill values on bounds error instead of raising ValueError.
    interpolate_func = scipy.interpolate.interp1d(x_column, y_column, bounds_error=False, fill_value=(y_xmin, y_xmax))
    
    # Wrap in 'float()' since scipy.interpolate.interp1d can return np.array(np.nan) which isn't really a float.
    def interpolate_func_wrapper(x):
        return float(interpolate_func(x))
    
    return interpolate_func_wrapper, x_column, y_column


def interpolate_file(
        curve_function,
        input_filename,
        output_filename,
        input_x_column_index=0,
        reverse_output_columns=False):
    """Interpolate `curve_function` at `x` positions, read from input file, and store both `x` and interpolated `y` values to output file.
    
    Parameters
    ----------
    curve_function : function
        A callable function `y=f(x)` accepting a single `x` argument and returning a `y` value.
    input_filename : string
        Name of input text file containing the `x` positions at which to sample `curve_function`.
        A single `x` value is obtained from each row by indexing the `input_x_column_index` column (zero-based index).
    output_filename : string
        Name of output text file containing `x` and `y` values.
        Each row of output file contains an `x` value and its associated `y` value (with order depending on `reverse_output_columns`).
    input_x_column_index : int, optional
        Determines which column of input file to read `x` values from.
    reverse_output_columns : bool, optional
        Determines order of `x` and `y` columns in output file.
        If `True` then output `y x`, otherwise output `x y`.
    
    Raises
    ------
    ValueError
        If cannot read an `x` value, as a floating-point number, from input file at column index `input_x_column_index`.
    """
    
    with open(input_filename, 'r') as input_file, open(output_filename, 'w') as output_file:
        for line_number, line in enumerate(input_file):
            
            # Make line number 1-based instead of 0-based.
            line_number = line_number + 1
            
            # Split the line into strings (separated by whitespace).
            line_string_list = line.split()
            
            num_strings = len(line_string_list)
            
            # If just a line containing white-space then skip to next line.
            if num_strings == 0:
                continue
            
            # If line is a comment then ignore and then skip to next line.
            if (line_string_list[0].startswith('#') or
                line_string_list[0].startswith('>')):
                continue
            
            if num_strings < input_x_column_index + 1:
                raise ValueError('Input file {0} does not have a column {1} at line {2}.'.format(
                                 input_filename, input_x_column_index + 1, line_number))
            
            try:
                x = float(line_string_list[input_x_column_index])
            except ValueError:
                # Raise a more informative error message.
                raise ValueError('Cannot read x value at line {0} of input file {1}.'.format(
                                 line_number, input_filename))
            
            y = curve_function(x)
            
            if reverse_output_columns:
                output_row = y, x
            else:
                output_row = x, y
            
            output_file.write('{0:.2f}\t{1:.2f}\n'.format(*output_row))


if __name__ == '__main__':
    
    import argparse
    import traceback
    
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
    
    try:
        __description__ = \
            """
        Interpolate a sequence of linear segments (read from a 2-column model file) at values read from
        a specific column in input file and write 2-column results to output file.
        
        The linear segments represent a linear function y = f(x) where the input 2-column file contains its (x,y) node points.
        The input 1-column data represents x values (at which to interpolate y) and the output 2-column data contains interpolated columns x and y.

        NOTE: Separate the positional and optional arguments with '--' (workaround for bug in argparse module).
        For example...

        python %(prog)s -c x_y_curve.txt input_x.txt output_x_y.txt
         """

        # The command-line parser.
        parser = argparse.ArgumentParser(description=__description__, formatter_class=argparse.RawDescriptionHelpFormatter)
        
        parser.add_argument('--version', action='version', version=pybacktrack.version.__version__)
        
        parser.add_argument(
            '-c', '--curve_filename', type=str, required=True,
            metavar='curve_filename', help='File containing linear function y=f(x). The first column is x and second column y.')
        
        parser.add_argument(
            '-cx', '--curve_x_column', type=int, default=0,
            metavar='curve_x_column_index', help='The zero-based index of column in "curve" file containing x values. Defaults to first column.')
        parser.add_argument(
            '-cy', '--curve_y_column', type=int, default=1,
            metavar='curve_y_column_index', help='The zero-based index of column in "curve" file containing y values. Defaults to second column.')
        
        parser.add_argument(
            '-ix', '--input_x_column', type=int, default=0,
            metavar='input_x_column_index', help='The zero-based index of column in input file containing x values. Defaults to first column.')
        
        parser.add_argument(
            '-r', '--reverse_output_columns', action='store_true',
            help='Reverse the order of output columns to output as "y x". Defaults to "x y".')
        
        parser.add_argument(
            'input_filename', type=argparse_unicode,
            metavar='input_filename',
            help='The input filename containing the "x" positions to interpolate at.')
        
        parser.add_argument(
            'output_filename', type=argparse_unicode,
            metavar='output_filename',
            help='The output filename that the "x" positions (from input file) and interpolated "y" values (at those "x" positions) will be written to.')
        
        # Parse command-line options.
        args = parser.parse_args()
        
        # Read the curve function y=f(x) from curve file.
        curve_function, _, _ = read_curve_function(args.curve_filename, args.curve_x_column, args.curve_y_column)
        
        # Convert x values in 1-column input file to x and y values in 2-column output file.
        interpolate_file(
            curve_function,
            args.input_filename,
            args.output_filename,
            args.input_x_column,
            args.reverse_output_columns)
        
        sys.exit(0)
        
    except Exception as exc:
        print('ERROR: {0}'.format(exc), file=sys.stderr)
        # Uncomment this to print traceback to location of raised exception.
        # traceback.print_exc()
        
        sys.exit(1)

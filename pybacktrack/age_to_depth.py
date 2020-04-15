
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

"""Convert ocean basin ages (Ma) to basement depth (metres) using different age/depth models.

:func:`convert_age_to_depth` converts ocean basin age to basement depth using a specified age/depth model.

:func:`convert_age_to_depth_files` converts age to depth by reading `age` rows from input file and writing rows containing both `age` and `depth` to output file.
"""


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import math
import pybacktrack.version
from pybacktrack.util.interpolate import read_curve_function
import sys
import warnings


#
# Enumerations for the age-to-depth model.
#
# GDH1;
# Stein and Stein (1992) "Model for the global variation in oceanic depth and heat flow with lithospheric age".
MODEL_GDH1 = 0
# Crosby short PDF on 22 May 2007 uses function which best-fits all the data in
# Crosby et al. (2006) "The relationship between depth, age and gravity in the oceans".
MODEL_CROSBY_2007 = 1

    
# List of 3-tuples (model, model_name, model_desc).
# Only used by command-line script (at bottom of this file).
ALL_MODELS = [
    (MODEL_GDH1, 'GDH1', 'Stein and Stein (1992) "Model for the global variation in oceanic depth and heat flow with lithospheric age"'),
    (MODEL_CROSBY_2007, 'CROSBY_2007', 'Crosby et al. (2006) "The relationship between depth, age and gravity in the oceans"')]


# The model to use by default (if no 'model' parameter passed to function).
DEFAULT_MODEL = MODEL_GDH1


def convert_age_to_depth(
        age,
        model=DEFAULT_MODEL):
    """convert_age_to_depth(age, model=pybacktrack.AGE_TO_DEPTH_DEFAULT_MODEL)
    Convert ocean basin age to basement depth using a specified age/depth model.
    
    Parameters
    ----------
    age : float
        The age in Ma.
    model : {pybacktrack.AGE_TO_DEPTH_MODEL_GDH1, pybacktrack.AGE_TO_DEPTH_MODEL_CROSBY_2007} or function, optional
        The model to use when converting ocean age to basement depth.
        It can be one of the enumerated values, or a callable function accepting a single non-negative age parameter and returning depth (in metres).
    
    Returns
    -------
    float
        Depth (in metres) as a positive number.
    
    Raises
    ------
    ValueError
        If `age` is negative.
    TypeError
        If `model` is not a recognised model, or a function accepting a single parameter.
    """
    
    if age < 0:
        raise ValueError('Age must be non-negative')
    
    if model == MODEL_GDH1:
        return _age_to_depth_GDH1(age)
    elif model == MODEL_CROSBY_2007:
        return _age_to_depth_CROSBY_2007(age)
    else:
        return model(age)


def convert_age_to_depth_files(
        input_filename,
        output_filename,
        model=DEFAULT_MODEL,
        age_column_index=0,
        reverse_output_columns=False):
    """convert_age_to_depth_files(input_filename, output_filename, model=pybacktrack.AGE_TO_DEPTH_DEFAULT_MODEL, age_column_index=0,reverse_output_columns=False)
    Converts age to depth by reading `age` rows from input file and writing rows containing both `age` and `depth` to output file.
    
    Parameters
    ----------
    input_filename : string
        Name of input text file containing the `age` values.
        A single `age` value is obtained from each row by indexing the `age_column_index` column (zero-based index).
    output_filename : string
        Name of output text file containing `age` and `depth` values.
        Each row of output file contains an `age` value and its associated `depth` value (with order depending on `reverse_output_columns`).
    model : {pybacktrack.AGE_TO_DEPTH_MODEL_GDH1, pybacktrack.AGE_TO_DEPTH_MODEL_CROSBY_2007} or function, optional
        The model to use when converting ocean age to basement depth.
        It can be one of the enumerated values, or a callable function accepting a single non-negative age parameter and returning depth (in metres).
    age_column_index : int, optional
        Determines which column of input file to read `age` values from.
    reverse_output_columns : bool, optional
        Determines order of `age` and `depth` columns in output file.
        If `True` then output `depth age`, otherwise output `age depth`.
    
    Raises
    ------
    ValueError
        If cannot read `age` value, as a floating-point number, from input file at column index `age_column_index`.
    """
    
    with open(input_filename, 'rU') as input_file, open(output_filename, 'w') as output_file:
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
            
            if num_strings < age_column_index + 1:
                raise ValueError('Input file {0} does not have a column {1} at line {2}.'.format(
                                 input_filename, age_column_index + 1, line_number))
            
            try:
                age = float(line_string_list[age_column_index])
            except ValueError:
                # Raise a more informative error message.
                raise ValueError('Cannot read age value at line {0} of input file {1}.'.format(
                                 line_number, input_filename))
            
            depth = convert_age_to_depth(age, model)
            
            if reverse_output_columns:
                output_row = depth, age
            else:
                output_row = age, depth
            
            output_file.write('{0:.2f}\t{1:.2f}\n'.format(*output_row))


#########################################################################################
# GDH1 model (Stein and Stein 1992)                                                     #
# "Model for the global variation in oceanic depth and heat flow with lithospheric age" #
#########################################################################################

def _age_to_depth_GDH1(age):
    
    if age < 0:
        raise ValueError('Age must be non-negative')
    elif age < 20:
        return 2600.0 + 365.0 * math.sqrt(age)
    else:
        return 5651.0 - 2473.0 * math.exp(-0.0278 * age)


#########################################################################################
# Crosby short PDF on 22 May 2007 uses function which best-fits all the data in         #
# Crosby et al. (2006) "The relationship between depth, age and gravity in the oceans". #
#                                                                                       #
# Converted to Python from C program "age2depth.c".                                     #
#########################################################################################

def _age_to_depth_CROSBY_2007(age):
    
    return _CROSBY_2007_RD + _CROSBY_2007_subs(age) - _CROSBY_2007_pert(age)


_CROSBY_2007_DENSM = 3300.0  # Mantle density, kgm-3
_CROSBY_2007_DENSW = 1030.0  # Water density, kgm-3
_CROSBY_2007_KAPPA = 7.8e-7  # Thermal diffusivity, m2s-1
_CROSBY_2007_ALPHA = 3.2e-5  # Thermal expansivity
_CROSBY_2007_TM = 1333.0  # Mantle temperature, C
_CROSBY_2007_RD = 2600.0  # Zero-age depth, m
_CROSBY_2007_PTHICK = 1.02e5  # Plate thickness, m

_CROSBY_2007_PERT_A = 300.0
_CROSBY_2007_PERT_B = 15.0
_CROSBY_2007_PERT_C = 0.2
_CROSBY_2007_PERT_D = 94.0
_CROSBY_2007_PERT_E = 30.0

_CROSBY_2007_FTOL = 1.0e-6


def _CROSBY_2007_subs(age):

    # Calculates the expected subsidence for a given age and plate model

    age *= 1.0e6 * 365.25 * 24.0 * 3600.0
        
    i = 1.0
    oldsum = 0.0
    
    while True:

        sum = math.exp(-i * i * math.pi * math.pi * _CROSBY_2007_KAPPA * age / (_CROSBY_2007_PTHICK * _CROSBY_2007_PTHICK))
        sum /= (i * i)
        sum *= -2.0
        sum += oldsum

        fdiff = math.fabs((sum - oldsum) / sum)
 
        oldsum = sum
        
        i += 2.0
    
        if fdiff <= _CROSBY_2007_FTOL:
            break

    w = sum * 2.0 * _CROSBY_2007_TM * _CROSBY_2007_PTHICK / (math.pi * math.pi)
    w += _CROSBY_2007_TM * _CROSBY_2007_PTHICK / 2.0
    w *= _CROSBY_2007_DENSM * _CROSBY_2007_ALPHA / (_CROSBY_2007_DENSM - _CROSBY_2007_DENSW)

    return w


def _CROSBY_2007_pert(age):

    ptb = (age - _CROSBY_2007_PERT_D) / _CROSBY_2007_PERT_E
    ptb *= ptb
    ptb = math.exp(-ptb)
    ptb *= math.sin((age / _CROSBY_2007_PERT_B) - _CROSBY_2007_PERT_C)
    ptb *= _CROSBY_2007_PERT_A

    return ptb


model_dict = dict((model_name, model) for model, model_name, _ in ALL_MODELS)
model_name_dict = dict((model, model_name) for model, model_name, _ in ALL_MODELS)
default_model_name = model_name_dict[DEFAULT_MODEL]


# Action to parse an age model.
class ArgParseAgeModelAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        model = None
        
        if len(values) == 1:
            # Convert model name to enumeration.
            try:
                model = model_dict[values[0]]
            except KeyError:
                raise argparse.ArgumentTypeError("%s is not a valid model" % values[0])
        elif len(values) == 3:
            # Read 2-column text file to get a function of depth(age).
            age_model_filename = values[0]
            
            try:
                # Convert strings to float.
                age_column_index = int(values[1])
                depth_column_index = int(values[2])
                if age_column_index < 0 or depth_column_index < 0:
                    parser.error('age and depth column indices must be non-negative')
            except ValueError:
                raise argparse.ArgumentTypeError("encountered an age or depth column index that is not an integer")
            
            model, _, _ = read_curve_function(age_model_filename, age_column_index, depth_column_index)
        else:
            parser.error('age model must either be one of {0}, or an age model filename and age and depth column indices'.format(
                ' '.join(model_name for _, model_name, _ in ALL_MODELS)))
        
        setattr(namespace, self.dest, model)


if __name__ == '__main__':
    
    def warning_format(message, category, filename, lineno, file=None, line=None):
        # return '{0}:{1}: {1}:{1}\n'.format(filename, lineno, category.__name__, message)
        return '{0}: {1}\n'.format(category.__name__, message)
    
    # Print the warnings without the filename and line number.
    # Users are not going to want to see that.
    warnings.formatwarning = warning_format
    
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
    
    __description__ = \
        """Converts rows containing age in input file to rows containing age and depth in output file.
        
        Reads text data from input file where each line contains age (in Ma).
        Writes text data to output file where each line contains age (in Ma) and depth (in metres), optionally reversed.
        
        The age-to-depth model can be chosen using the '-m' option.
        It can be the name of an in-built age model:{0}
        ...defaults to {1}.
        Or it can be an age model filename followed by two integers representing the age and depth column indices,
        where the file should contain at least two columns (one containing the age and the other the depth).
        
        
        NOTE: Separate the positional and optional arguments with '--' (workaround for bug in argparse module).
        For example...

        python %(prog)s -m {1} age_points.xy depth_points.xy
        """.format(
            ''.join('\n\n        {0}: {1}.\n'.format(model_name, model_desc)
                    for _, model_name, model_desc in ALL_MODELS),
            default_model_name)
    
    # The command-line parser.
    parser = argparse.ArgumentParser(description=__description__, formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument('--version', action='version', version=pybacktrack.version.__version__)
    
    parser.add_argument(
        '-m', '--model', nargs='+', action=ArgParseAgeModelAction,
        metavar='model_parameter',
        default=DEFAULT_MODEL,
        help='The model used to convert age to depth. '
             'It can be the name of an in-built age model: {0} (defaults to {1}). '
             'Or it can be an age model filename followed by two integers representing the age and depth column indices, '
             'where the file should contain at least two columns (one containing the age and the other the depth).'.format(
                ', '.join(model_name for _, model_name, _ in ALL_MODELS),
                default_model_name))
    
    parser.add_argument(
        '-a', '--age_column', type=int, default=0,
        metavar='age_column_index', help='The zero-based index of column in input file containing age values. Defaults to first column.')
    
    parser.add_argument(
        '-r', '--reverse_output_columns', action='store_true',
        help='Reverse the order of output columns to output as "depth age". Defaults to "age depth".')
    
    parser.add_argument(
        'input_filename', type=argparse_unicode,
        metavar='input_filename',
        help='The input filename containing the "age" values.')
    
    parser.add_argument(
        'output_filename', type=argparse_unicode,
        metavar='output_filename',
        help='The output filename containing the converted "depth" values.')
    
    # Parse command-line options.
    args = parser.parse_args()
    
    convert_age_to_depth_files(
        args.input_filename,
        args.output_filename,
        args.model,
        args.age_column,
        args.reverse_output_columns)
    
    sys.exit(0)

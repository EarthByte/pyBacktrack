
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


###############################################################################
# Various age/depth curves to convert ocean basin age (Ma) to depth (metres). #
###############################################################################


from __future__ import print_function
import pybacktrack.version
import math
import sys


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
    (MODEL_CROSBY_2007, 'CROSBY_2007', 'Crosby et al. (2006) "The relationship between depth, age and gravity in the oceans".')]


# The model to use by default (if no 'model' parameter passed to function).
DEFAULT_MODEL = MODEL_GDH1


def age_to_depth(
        age,
        model=DEFAULT_MODEL):
    """
    Converts 'age' (Ma) to basement depth (metres) using the age/depth curve/model 'model'.
    
    Returns depth (in metres) as a positive number.
    
    'model' defaults to GDH1 (Stein and Stein 1992).
    
    'age' must be non-negative.
    """
    
    if age < 0:
        raise ValueError('Age must be non-negative')
    
    if model == MODEL_GDH1:
        return age_to_depth_GDH1(age)
    elif model == MODEL_CROSBY_2007:
        return age_to_depth_CROSBY_2007(age)
    
    raise ValueError('Unexpected model.')


def age_to_depth_from_stdin_to_stdout(
        model=DEFAULT_MODEL):
    """
    Converts (lon, lat, age) lines on stdin to (lon, lat, depth) on stdout.
    
    Reads text data from standard input where each line contains longitude, latitude (in degrees) and age (in Ma).
    Writes text data to standard output where each line contains longitude, latitude (in degrees) and depth (in metres).
    """
    
    for line_number, line in enumerate(sys.stdin):

        # Make line number 1-based instead of 0-based.
        line_number = line_number + 1

        # Split the line into strings (separated by whitespace).
        line_string_list = line.split()

        # Need at least 3 strings per line (longitude, latitude and age).
        if len(line_string_list) < 3:
            print('Line {0}: Ignoring point - line does not have at least three white-space separated strings.'.format(
                  line_number), file=sys.stderr)
            continue

        # Attempt to convert each string into a floating-point number.
        try:
            # Use GMT (lon/lat) order.
            lon = float(line_string_list[0])
            lat = float(line_string_list[1])
            age = float(line_string_list[2])
        except ValueError:
            print('Line {0}: Ignoring point - cannot read lon/lat/age values.'.format(line_number), file=sys.stderr)
            continue
        
        depth = age_to_depth(age, model)
        
        sys.stdout.write('{0}\t{1}\t{2}\n'.format(lon, lat, depth))


#########################################################################################
# GDH1 model (Stein and Stein 1992)                                                     #
# "Model for the global variation in oceanic depth and heat flow with lithospheric age" #
#########################################################################################

def age_to_depth_GDH1(age):
    
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

CROSBY_2007_DENSM = 3300.0  # Mantle density, kgm-3
CROSBY_2007_DENSW = 1030.0  # Water density, kgm-3
CROSBY_2007_KAPPA = 7.8e-7  # Thermal diffusivity, m2s-1
CROSBY_2007_ALPHA = 3.2e-5  # Thermal expansivity
CROSBY_2007_TM = 1333.0  # Mantle temperature, C
CROSBY_2007_RD = 2600.0  # Zero-age depth, m
CROSBY_2007_PTHICK = 1.02e5  # Plate thickness, m

CROSBY_2007_PERT_A = 300.0
CROSBY_2007_PERT_B = 15.0
CROSBY_2007_PERT_C = 0.2
CROSBY_2007_PERT_D = 94.0
CROSBY_2007_PERT_E = 30.0

CROSBY_2007_FTOL = 1.0e-6


def CROSBY_2007_subs(age):

    # Calculates the expected subsidence for a given age and plate model

    age *= 1.0e6 * 365.25 * 24.0 * 3600.0
        
    i = 1.0
    oldsum = 0.0
    
    while True:

        sum = math.exp(-i * i * math.pi * math.pi * CROSBY_2007_KAPPA * age / (CROSBY_2007_PTHICK * CROSBY_2007_PTHICK))
        sum /= (i * i)
        sum *= -2.0
        sum += oldsum

        fdiff = math.fabs((sum - oldsum) / sum)
 
        oldsum = sum
        
        i += 2.0
    
        if fdiff <= CROSBY_2007_FTOL:
            break

    w = sum * 2.0 * CROSBY_2007_TM * CROSBY_2007_PTHICK / (math.pi * math.pi)
    w += CROSBY_2007_TM * CROSBY_2007_PTHICK / 2.0
    w *= CROSBY_2007_DENSM * CROSBY_2007_ALPHA / (CROSBY_2007_DENSM - CROSBY_2007_DENSW)

    return w


def CROSBY_2007_pert(age):

    ptb = (age - CROSBY_2007_PERT_D) / CROSBY_2007_PERT_E
    ptb *= ptb
    ptb = math.exp(-ptb)
    ptb *= math.sin((age / CROSBY_2007_PERT_B) - CROSBY_2007_PERT_C)
    ptb *= CROSBY_2007_PERT_A

    return ptb


def age_to_depth_CROSBY_2007(age):
    
    return CROSBY_2007_RD + CROSBY_2007_subs(age) - CROSBY_2007_pert(age)


if __name__ == '__main__':
    
    import argparse
    
    model_dict = dict((model_name, model) for model, model_name, _ in ALL_MODELS)
    model_name_dict = dict((model, model_name) for model, model_name, _ in ALL_MODELS)
    default_model_name = model_name_dict[DEFAULT_MODEL]
    
    __description__ = \
        """Converts (lon, lat, age) lines on stdin to (lon, lat, depth) on stdout.
        
        Reads text data from standard input where each line contains longitude, latitude (in degrees) and age (in Ma).
        Writes text data to standard output where each line contains longitude, latitude (in degrees) and depth (in metres).
        
        The age-to-depth model can be chosen using the '-m' option.
        Choices include:{0}
        ...defaults to {1}.
        
        
        NOTE: Separate the positional and optional arguments with '--' (workaround for bug in argparse module).
        For example...

        python %(prog)s -m {1} < age_points.xy > depth_points.xy
        """.format(
            ''.join('\n\n        {0}: {1}.\n'.format(model_name, model_desc)
                    for _, model_name, model_desc in ALL_MODELS),
            default_model_name)
    
    # The command-line parser.
    parser = argparse.ArgumentParser(description=__description__, formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument('--version', action='version', version=pybacktrack.version.__version__)
    
    parser.add_argument(
        '-m', '--model', type=str, default=default_model_name,
        metavar='model',
        dest='model_name',
        help='The model used to convert age to depth. '
             'Choices include {0} (see above). '
             'Defaults to {1}.'.format(
                ', '.join(model_name for _, model_name, _ in ALL_MODELS),
                default_model_name))
    
    # Parse command-line options.
    args = parser.parse_args()
    
    # Convert model name to enumeration.
    try:
        model = model_dict[args.model_name]
    except KeyError:
        raise argparse.ArgumentTypeError("%s is not a valid model" % args.model_name)
    
    age_to_depth_from_stdin_to_stdout(model)
    
    sys.exit(0)

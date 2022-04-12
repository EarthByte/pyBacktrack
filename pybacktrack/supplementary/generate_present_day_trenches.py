
#
# Copyright (C) 2022 The University of Sydney, Australia
#
# This program is free software; you can redistribute it and/or modify it under
# the Free Software Foundation.
# the terms of the GNU General Public License, version 2, as published by
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

import os.path
import pygplates
import sys


# Required pygplates version.
# Need version 30 to use pygplates.TopologicalModel and pygplates.TopologicalSnapshot.
PYGPLATES_VERSION_REQUIRED = pygplates.Version(30)

# Default to the 2019 v2 deforming model (in 'deforming_model/2019_v2/' sub-directory).
DEFAULT_TOPOLOGY_FILES = os.path.join('deforming_model', '2019_v2', 'topology_files.txt')
DEFAULT_ROTATION_FILES = os.path.join('deforming_model', '2019_v2', 'rotation_files.txt')

# Default distance to present-day trenches to exclude bathymetry grid points (in kms).
DEFAULT_EXCLUDE_DISTANCE_TO_TRENCHES_KMS = 50


def generate_present_day_trenches(
        topology_filenames=None,
        rotation_filenames=None,
        exclude_distance_to_trenches_kms=DEFAULT_EXCLUDE_DISTANCE_TO_TRENCHES_KMS):
    """Generate the present-day locations of trenches.
    
    Parameters
    ----------
    topology_filenames : list of string, optional
        List of filenames containing topological features (to create a topological model with).
        If not specified then defaults to the 'deforming_model/2019_v2/' topological model.
    rotation_filenames : list of string, optional
        List of filenames containing rotation features (to create a topological model with).
        If not specified then defaults to the 'deforming_model/2019_v2/' topological model.
    exclude_distance_to_trenches_kms : float, optional
        The distance to present-day trenches (in kms) that will be used to exclude grid points during paleobathymetry gridding.
    
    Returns
    -------
    list of pygplates.Feature (with a single geometry per feature)
    """
    
    # Check the imported pygplates version.
    if pygplates.Version.get_imported_version() < PYGPLATES_VERSION_REQUIRED:
        raise RuntimeError('Using pygplates version {0} but version {1} or greater is required'.format(
                pygplates.Version.get_imported_version(), PYGPLATES_VERSION_REQUIRED))
    
    # Must either provide both topology and rotation features or neither.
    if (topology_filenames and not rotation_filenames) or (not topology_filenames and rotation_filenames):
        raise ValueError('Must either provide both topology and rotation features or neither')
    
    # If caller did not provide a topological model.
    if not topology_filenames and not rotation_filenames:
        # Read the list of default topology filenames.
        topology_filenames = _read_list_of_files(DEFAULT_TOPOLOGY_FILES)
        # Read the list of default rotation filenames.
        rotation_filenames = _read_list_of_files(DEFAULT_ROTATION_FILES)

    # Load the topological model.
    topological_model = pygplates.TopologicalModel(topology_filenames, rotation_filenames)

    # Get a snapshot of resolved topologies at present day.
    topological_snapshot = topological_model.topological_snapshot(0.0)

    # Get the topological sections shared by resolved boundaries/networks.
    resolved_topological_sections = topological_snapshot.get_resolved_topological_sections()

    # Extract resolved features for trench sub-segments (each containing a single sub-segment geometry).
    resolved_trench_features = []
    for resolved_topological_section in resolved_topological_sections:
        if resolved_topological_section.get_feature().get_feature_type() == pygplates.FeatureType.gpml_subduction_zone:
            trench_sub_segments = resolved_topological_section.get_shared_sub_segments()
            resolved_trench_features.extend(trench_sub_segment.get_resolved_feature() for trench_sub_segment in trench_sub_segments)

    # Set the default exclude distance to trenches as a shapefile attribute (to be read by paleo bathymetry gridding workflow).
    for resolved_trench_feature in resolved_trench_features:
        resolved_trench_feature.set_shapefile_attribute('exclude_distance_to_trench_kms', float(exclude_distance_to_trenches_kms))

    # Return resolved features each containing a single shared sub-segment geometry.
    return resolved_trench_features


def _read_list_of_files(
        list_filename):
    """
    Read the filenames listed in a file.
    """

    with open(list_filename, 'r') as list_file:
        filenames = list_file.read().splitlines()
    
    return filenames


if __name__ == '__main__':
    
    ########################
    # Command-line parsing #
    ########################
    
    import argparse
    
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
    
    
    def main():
        
        __description__ = """Generate the present-day locations of trenches.
    
    NOTE: Separate the positional and optional arguments with '--' (workaround for bug in argparse module).
    For example...

    python generate_present_day_trenches.py ... -- trenches.gpmlz
    """
    
        #
        # Gather command-line options.
        #
        
        # The command-line parser.
        parser = argparse.ArgumentParser(description=__description__, formatter_class=argparse.RawDescriptionHelpFormatter)
        
        # Can optionally specify topology filenames.
        topology_argument_group = parser.add_mutually_exclusive_group()
        topology_argument_group.add_argument(
            '-ml', '--topology_list_filename', type=str,
            metavar='topology_list_filename',
            help='File containing list of topology filenames (to create topological model with). '
                 'If no topology list file (or topology files) specified then defaults to {0}'.format(DEFAULT_TOPOLOGY_FILES))
        topology_argument_group.add_argument(
            '-m', '--topology_filenames', type=str, nargs='+',
            metavar='topology_filename',
            help='One or more topology files (to create topological model with).')
        
        # Can optionally specify rotation filenames.
        rotation_argument_group = parser.add_mutually_exclusive_group()
        rotation_argument_group.add_argument(
            '-rl', '--rotation_list_filename', type=str,
            metavar='rotation_list_filename',
            help='File containing list of rotation filenames (to create topological model with). '
                 'If no rotation list file (or rotation files) specified then defaults to {0}'.format(DEFAULT_ROTATION_FILES))
        rotation_argument_group.add_argument(
            '-r', '--rotation_filenames', type=str, nargs='+',
            metavar='rotation_filename',
            help='One or more rotation files (to create topological model with).')
        
        parser.add_argument(
            'trench_filename', type=argparse_unicode,
            metavar='trench_filename',
            help='The output trench filename containing present-day trench locations.')
        
        parser.add_argument('-et', '--exclude_distance_to_trenches_kms', type=float, default=DEFAULT_EXCLUDE_DISTANCE_TO_TRENCHES_KMS,
                help='The distance to present-day trenches (in kms) that will be used to exclude grid points during paleobathymetry gridding. '
                     'Defaults to {} kms.'.format(DEFAULT_EXCLUDE_DISTANCE_TO_TRENCHES_KMS))
        
        # Parse command-line options.
        args = parser.parse_args()
            
        #
        # Do any necessary post-processing/validation of parsed options.
        #
        
        # Get topology files.
        if args.topology_list_filename is not None:
            topology_filenames = _read_list_of_files(args.topology_list_filename)
        elif args.topology_filenames is not None:
            topology_filenames = args.topology_filenames
        else:
            topology_filenames = None
        
        # Get rotation files.
        if args.rotation_list_filename is not None:
            rotation_filenames = _read_list_of_files(args.rotation_list_filename)
        elif args.rotation_filenames is not None:
            rotation_filenames = args.rotation_filenames
        else:
            rotation_filenames = None
        
        # Generate the present-day trenches.
        trench_features = generate_present_day_trenches(topology_filenames, rotation_filenames, args.exclude_distance_to_trenches_kms)

        # Create the trenches feature collection and save to file.
        pygplates.FeatureCollection(trench_features).write(args.trench_filename)
        
        sys.exit(0)
    
    import traceback
    
    try:
        main()
        sys.exit(0)
    except Exception as exc:
        print('ERROR: {0}'.format(exc), file=sys.stderr)
        # Uncomment this to print traceback to location of raised exception.
        #traceback.print_exc()
        sys.exit(1)

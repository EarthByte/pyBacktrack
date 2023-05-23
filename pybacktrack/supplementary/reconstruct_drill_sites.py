import csv
import numpy as np
import os
import os.path
import pybacktrack
import pygplates
import sys

#
# To install the above dependencies with conda:
#   conda create -n <conda-environment> -c conda-forge numpy pybacktrack pygplates
#   conda activate <conda-environment>
# ...where <conda-environment> should be replaced with the name of your conda environment.
#


DEFAULT_OUTPUT_FILENAME_SUFFIX = "_reconstructed.txt"

def reconstruct_drill_sites(
        drill_site_files,           # sequence of drill site filenames
        rotation_features_or_model, # any combination of rotation features and files; or a rotation model
        static_polygon_features,    # any combination of features, feature collection and files
        end_time,
        start_time = 0,
        time_increment = 1,
        output_filename_suffix = DEFAULT_OUTPUT_FILENAME_SUFFIX):
    """Reconstruct the present-day location of one or more drill sites.
    
    Read in one or more drill sites and reconstruct each drill site location
    (by assigning a plate ID using static polygons and reconstructing using rotation files)
    through a range of times (but not older than the age of the oldest stratigraphic layer at the drill site)
    and output the reconstructed lon/lat locations to text files
    (a separate file for each drill site, with same filename but different suffix).
    """

    # Read all the bundled lithologies ("primary" and "extended").
    lithologies = pybacktrack.read_lithologies_files(pybacktrack.BUNDLE_LITHOLOGY_FILENAMES)

    # Rotation model.
    rotation_model = pygplates.RotationModel(rotation_features_or_model)

    # Static polygons partitioner used to assign plate IDs to the drill sites.
    plate_partitioner = pygplates.PlatePartitioner(static_polygon_features, rotation_model)


    # Iterate over the drill sites.
    for drill_site_filename in drill_site_files:
        
        # Read drill site file to get the site location.
        drill_site = pybacktrack.read_well_file(
            drill_site_filename,
            lithologies,
            well_attributes={
                'SiteLongitude': ('longitude', float),  # read 'SiteLongitude' into 'drill_site.longitude'
                'SiteLatitude': ('latitude', float)})   # read 'SiteLatitude' into 'drill_site.latitude'
        
        # Check drill site has stratigraphic layers.
        if not drill_site.stratigraphic_units:
            print('Not reconstructing drill site because it has no stratigraphic layers: "{}"'.format(drill_site_filename))
            continue
        
        # Age of bottom of drill site.
        drill_site_age = drill_site.stratigraphic_units[-1].bottom_age;
        
        if start_time > drill_site_age:
            print('Not reconstructing drill site because "start_time" is older than oldest drilled section: "{}"'.format(drill_site_filename))
            continue
        
        # Time range to reconstruct.
        # We don't reconstruct older than the (bottom) age of the oldest stratigraphic layer in the drill site.
        # Note: Using 1e-6 to ensure the end time gets included (if it's an exact multiple of the time increment, which it likely will be).
        time_range = [float(time) for time in np.arange(start_time, min(end_time, drill_site_age) + 1e-6, time_increment)]
        
        #print('Reconstructing drill site "{}" at location ({}, {})'.format(drill_site_filename, drill_site.longitude, drill_site.latitude))
        
        # Present day location of drill site.
        drill_site_location = pygplates.PointOnSphere(drill_site.latitude, drill_site.longitude)
        
        # Assign a plate ID to the drill site based on its location.
        partitioning_plate = plate_partitioner.partition_point(drill_site_location)
        if not partitioning_plate:
            # Not contained by any plates. Shouldn't happen since static polygons have global coverage,
            # but might if there's tiny cracks between polygons.
            raise ValueError('Unable to assign plate ID. Drill site does not intersect the static polygons.')
        drill_site_plate_id = partitioning_plate.get_feature().get_reconstruction_plate_id()
        
        # Output filename is the input filename appended with a suffix.
        drill_site_output_filename, _ = os.path.splitext(drill_site_filename)
        drill_site_output_filename += output_filename_suffix
        
        # Open the output drill file for writing.
        with open(drill_site_output_filename, 'w', newline='') as drill_site_output_file:
            # Write the header information.
            drill_site_output_file.write('#' + os.linesep)
            drill_site_output_file.write('# Site file: {}'.format(os.path.basename(drill_site_output_filename)) + os.linesep)  # site filename
            drill_site_output_file.write('# Site longitude: {}'.format(drill_site.longitude) + os.linesep)  # site longitude
            drill_site_output_file.write('# Site latitude: {}'.format(drill_site.latitude) + os.linesep)  # site longitude
            drill_site_output_file.write('#' + os.linesep)
            
            # Reconstruct the drill site and write reconstructed locations to output file.
            drill_site_output_writer = csv.writer(drill_site_output_file, delimiter=' ')
            for time in time_range:
                # Get rotation from present day to current time using the drill site plate ID.
                rotation = rotation_model.get_rotation(time, drill_site_plate_id, from_time=0)
                
                # Reconstruct drill site to current time.
                reconstructed_drill_site_location = rotation * drill_site_location
                reconstructed_drill_site_latitude, reconstructed_drill_site_longitude = reconstructed_drill_site_location.to_lat_lon()
                
                # Write reconstructed location to output file.
                drill_site_output_writer.writerow((reconstructed_drill_site_longitude, reconstructed_drill_site_latitude))


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
        
        __description__ = """Reconstruct the present-day location of one or more drill sites.
    
    Read in one or more drill sites and reconstruct each drill site location
    (by assigning a plate ID using static polygons and reconstructing using rotation files)
    through a range of times (but not older than the age of the oldest stratigraphic layer at the drill site)
    and output the reconstructed lon/lat locations to text files
    (a separate file for each drill site, with same filename but different suffix which is '{}' by default).
    
    NOTE: Separate the positional and optional arguments with '--' (workaround for bug in argparse module).
    For example...

    python reconstruct_drill_sites.py ... -- drill_site.txt
    """.format(DEFAULT_OUTPUT_FILENAME_SUFFIX)
    
        #
        # Gather command-line options.
        #
        
        # The command-line parser.
        parser = argparse.ArgumentParser(description=__description__, formatter_class=argparse.RawDescriptionHelpFormatter)
        
        # Rotation filenames.
        parser.add_argument('-r', '--rotation_filenames',
            required=True, type=argparse_unicode, nargs='+', metavar='rotation_filename',
            help='One or more rotation files.')
        
        # Static polygon filenames.
        parser.add_argument('-p', '--static_polygon_filenames',
            required=True, type=argparse_unicode, nargs='+', metavar='static_polygon_filename',
            help='One or more static polygon files.')
        
        # Time range and increment.
        parser.add_argument('-s', '--start_time',
            type=float, default=0,
            help='The start of the time range (youngest time). Defaults to 0Ma.')
        parser.add_argument('-e', '--end_time',
            required=True, type=float,
            help='The end of the time range (oldest time).')
        parser.add_argument('-i', '--time_increment',
            type=float, default = 1,
            help='The increment of the time range. Defaults to 1Myr.')
        
        parser.add_argument('drill_site_filenames',
            type=argparse_unicode, nargs='+', metavar='drill_site_filename',
            help='Drill site file.')
        
        parser.add_argument('-o', '--output_filename_suffix',
            type=str, default=DEFAULT_OUTPUT_FILENAME_SUFFIX, metavar='output_filename_suffix',
            help='Filename suffix of reconstructed drill site output file. Defaults to "{}".'.format(DEFAULT_OUTPUT_FILENAME_SUFFIX))
        
        # Parse command-line options.
        args = parser.parse_args()
        
        # Reconstruct the present-day location of one or more drill sites.
        reconstruct_drill_sites(
            args.drill_site_filenames,
            args.rotation_filenames,
            args.static_polygon_filenames,
            args.end_time,
            args.start_time,
            args.time_increment,
            args.output_filename_suffix)
        
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

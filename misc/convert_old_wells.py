from __future__ import print_function
import glob
import os
import pybacktrack
import warnings

#
# Python 2 and 3 compatibility.
#
# Iterating over a dict.
try:
    dict.iteritems
except AttributeError:
    # Python 3
    def itervalues(d):
        return iter(d.values())
    def iteritems(d):
        return iter(d.items())
    def listvalues(d):
        return list(d.values())
    def listitems(d):
        return list(d.items())
else:
    # Python 2
    def itervalues(d):
        return d.itervalues()
    def iteritems(d):
        return d.iteritems()
    def listvalues(d):
        return d.values()
    def listitems(d):
        return d.items()


def adjust_well_name(
        well_name):
    """
    If the well name has a '1' at the end that is separated from the rest of the well name
    by a space, no space, or a '-', then remove the '1' and the whitespace.
    It seems some well names in the well files do not append the '1' and hence cannot find the well location.
    """
    
    if well_name[-1] == '1':
        well_name = well_name[0:-1]
        if well_name[-1] == ' ' or well_name[-1] == '-':
            well_name = well_name[0:-1]
    
    return well_name


def read_well_locations_file(
        well_locations_filename):
    """
    Reads the latitude/longitude locations associated with each well file.
    
    Parameters
    ----------
    well_locations_filename : str
        Name of well locations text file.
    
    Returns
    -------
    dict
        Dictionary mapping well names to (latitude, longitude) tuples.
    """
    
    well_locations = {}
    with open(well_locations_filename, 'rU') as well_locations_file:
        # Skip the header line.
        line_number = 1
        first_line = well_locations_file.readline()
        if first_line.split()[0] != '>WELL':
            raise ValueError('{0} does not look like a well locations file'.format(well_locations_filename))
        
        while True:
            line_number += 1
            header_line = well_locations_file.readline()
            if not header_line:
                # EOF.
                break
            
            if header_line[0] != '>':
                warnings.warn('Skipping well in {0} at line {1}. Line does not start with a >.'.format(
                    well_locations_filename, line_number))
                # The header is missing so skip to the next line.
                continue
            
            # There can be spaces in the well name, but there's also text after the well name (on same line).
            # Currently it looks like:
            #  * For those lines containing only spaces, the well name does not go past a certain column.
            #  * For those lines containing some tabs, the well name is the part before the first tab.
            well_name = adjust_well_name(header_line.split('\t', 1)[0][1:17].strip().lower())
            
            line_number += 1
            data_line = well_locations_file.readline()
            if not data_line:
                # EOF.
                break
            
            data = data_line.split()
            if len(data) != 2:
                warnings.warn('Skipping well {0} in {1} at line {2}. Expecting a latitude and a longitude.'.format(
                    well_name, well_locations_filename, line_number))
                # Expecting a latitude and a longitude so skip to the next line.
                continue
            
            try:
                well_location = float(data[0]), float(data[1])
            except ValueError:
                warnings.warn('Skipping well {0} in {1} at line {2}. Cannot read latitude/longitude location.'.format(
                    well_name, well_locations_filename, line_number))
                # Cannot read well location so skip to the next line.
                continue
            
            well_locations[well_name] = well_location
    
    return well_locations


# The ".dat" format hardwires 8 lithologies in this order.
DAT_LITHOLOGY_NAMES = [
    'Shale',
    'Limestone',
    'Chalk',
    'Dolostone',
    'Sand',
    'Basalt',
    'Anhydrite',
    'Salt']


def convert_dat_file(
        well_input_filename,
        well_locations,
        lithologies):
    """
    Reads the ".dat" filename and converts to pyBacktrack format (in sub-directory 'pybacktrack').
    
    Parameters
    ----------
    well_input_filename : str
        Name of input ".dat" well file.
    well_locations : dict
        Dictionary mapping well names to 2-tuple (latitude, longitude).
    lithologies : dict
        A dictionary mapping lithology names to pybacktrack.Lithology objects.
    """
    
    print('Converting {0}...'.format(well_input_filename))
    
    # Start with an empty well.
    well = pybacktrack.Well()
    
    # Read all lines in the input well file.
    with open(well_input_filename, 'rU') as well_input_file:
        lines = well_input_file.readlines()
    
    # Skip comments.
    line_index = 0
    while lines[line_index].split()[0] == 'C':
        line_index += 1
    
    # Read some header data.
    well_name = adjust_well_name(lines[line_index].strip().lower())
    subsidence_units_in_feet = bool(float(lines[line_index+1].strip()))
    num_layers = int(float(lines[line_index+2].strip()))
    surface_age = float(lines[line_index+5].strip())
    
    # Skip more comments.
    line_index += 6
    while lines[line_index].split()[0] == 'C':
        line_index += 1
    
    # Find well location.
    if well_name not in well_locations:
        warnings.warn('Skipping well file {0}. Cannot find a well location with well name "{1}".'.format(
            well_input_filename, well_name))
        return
    well.latitude, well.longitude = well_locations[well_name]
    
    # Read the stratigraphic layers.
    top_age = surface_age
    top_depth = 0.0
    for layer_index in range(num_layers):
        layer_line = lines[line_index]
        line_index += 1
        
        bottom_age = float(layer_line[1:10])
        bottom_depth = float(layer_line[10:20])
        # Convert depth from feet to metres (if necessary).
        if subsidence_units_in_feet:
            bottom_depth *= 3.28084
        
        # Add the 8 hardwired lithology components.
        total_lithology_fraction = 0.0
        lithology_components = []
        for lithology_index in range(0, 8):
            lithology_fraction_column_index = 20 + 5 * lithology_index
            lithology_fraction_string = layer_line[lithology_fraction_column_index:lithology_fraction_column_index+5].strip()
            # Add lithology component unless it's just whitespace.
            if lithology_fraction_string:
                lithology_fraction = float(lithology_fraction_string)
                total_lithology_fraction += lithology_fraction
                lithology_components.append((DAT_LITHOLOGY_NAMES[lithology_index], lithology_fraction))
        
        # Ensure the lithology fractions add up to 1.0.
        for lithology_component_index in range(len(lithology_components)):
            lithology_name, lithology_fraction = lithology_components[lithology_component_index]
            lithology_fraction /= total_lithology_fraction
            lithology_components[lithology_component_index] = lithology_name, lithology_fraction
        
        # Note that some ".dat" files have water depths that are not aligned to the correct columns
        # and are wider than 5 columns (apparently determined by the original format).
        # Here we're assuming the first (min) water depth is aligned correctly, but that it is 6 columns
        # wide (instead of 5) and hence the second (max) water depth has an alignment increased by 1 column.
        min_water_depth = float(layer_line[60:66])
        max_water_depth = float(layer_line[66:72])
        # Min/max water depths get added as extra columns since they are only needed for backstripping (not backtracking).
        other_attributes = {
            'min_water_depth': min_water_depth,
            'max_water_depth': max_water_depth}
        
        well.add_compacted_unit(
            top_age, bottom_age,
            top_depth, bottom_depth,
            lithology_components, lithologies,
            other_attributes)
        
        # Bottom of current layer becomes top of next layer.
        top_age = bottom_age
        top_depth = bottom_depth
    
    # Add a '_pybacktrack' suffix to the input base filename.
    well_input_file_dir, well_input_file_basename = os.path.split(well_input_filename)
    well_output_file_dir = os.path.join(well_input_file_dir, 'pybacktrack_format')
    # Create output sub-directory if it doesn't exist.
    if not os.path.isdir(well_output_file_dir):
        os.mkdir(well_output_file_dir)
    well_output_filename = os.path.join(well_output_file_dir, well_input_file_basename)
    
    # Write the well to the pyBacktrack format.
    pybacktrack.write_well_file(
        well,
        well_output_filename,
        other_column_attribute_names=['min_water_depth', 'max_water_depth'],
        well_attributes={'longitude': 'SiteLongitude', 'latitude': 'SiteLatitude'})


# The ".txt" format hardwires 8 lithologies in this order.
TXT_LITHOLOGY_NAMES = [
    'Shale',
    'Limestone',
    'Reef',
    'Dolostone',
    'Sand',
    'Basalt',
    'Anhydrite',
    'Salt']


def convert_txt_file(
        well_input_filename,
        well_locations,
        lithologies):
    """
    Reads the ".txt" filename and converts to pyBacktrack format (in sub-directory 'pybacktrack').
    
    Parameters
    ----------
    well_input_filename : str
        Name of input ".dat" well file.
    well_locations : dict
        Dictionary mapping well names to 2-tuple (latitude, longitude).
    lithologies : dict
        A dictionary mapping lithology names to pybacktrack.Lithology objects.
    """
    
    print('Converting {0}...'.format(well_input_filename))
    
    # Start with an empty well.
    well = pybacktrack.Well()
    
    # Read all lines in the input well file.
    with open(well_input_filename, 'rU') as well_input_file:
        lines = well_input_file.readlines()
    
    # Skip comments.
    line_index = 0
    while lines[line_index].split()[0] == 'C':
        line_index += 1
    
    # Read some header data.
    well_name = adjust_well_name(lines[line_index].strip().lower())
    subsidence_units_in_feet = bool(float(lines[line_index+1].strip()))
    num_layers = int(float(lines[line_index+2].strip()))
    surface_age = float(lines[line_index+5].strip())
    
    # Skip more comments, but look for row starting with "C age" since has column alignment info.
    line_index += 6
    found_column_alignments = False
    while lines[line_index].split()[0] == 'C':
        comment_line = lines[line_index]
        line_index += 1
        if comment_line.startswith('C age'):
            age_column_index = comment_line.find('age')
            depth_column_index = comment_line.find('depth')
            shale_column_index = comment_line.find('shal')
            limestone_column_index = comment_line.find('lmst')
            reef_column_index = comment_line.find('reef')
            dolostone_column_index = comment_line.find('dlst')
            sand_column_index = comment_line.find('sst')
            basalt_column_index = comment_line.find('bslt')
            anhydrite_column_index = comment_line.find('anhy')
            salt_column_index = comment_line.find('salt')
            min_water_depth_column_index = comment_line.find('PWD')
            # Files should have PWDm and PWDM for min/max water depth but some use PWDm for both,
            # so just search PWD for both but skip min PWD when searching for max PWD.
            max_water_depth_column_index = comment_line.find('PWD', min_water_depth_column_index+1)
            sea_column_index = comment_line.find('sea')
            
            if (age_column_index >= 0 and depth_column_index >= 0 and shale_column_index >= 0 and
                limestone_column_index >= 0 and reef_column_index >= 0 and dolostone_column_index >= 0 and
                sand_column_index >= 0 and basalt_column_index >= 0 and anhydrite_column_index >= 0 and
                salt_column_index >= 0 and min_water_depth_column_index >= 0 and max_water_depth_column_index >= 0 and
                sea_column_index >= 0):
                found_column_alignments = True
                # Column indices of the lithologies.
                # The final index is the end of last lithology (beginning of min water depth). 
                lithology_column_indices = [
                    shale_column_index, limestone_column_index, reef_column_index,
                    dolostone_column_index, sand_column_index, basalt_column_index,
                    anhydrite_column_index, salt_column_index, min_water_depth_column_index]
                    
    if not found_column_alignments:
        warnings.warn('Skipping well file {0}. Cannot find line starting with "C age".'.format(well_input_filename))
        return
    
    # Find well location.
    if well_name not in well_locations:
        warnings.warn('Skipping well file {0}. Cannot find a well location with well name "{1}".'.format(
            well_input_filename, well_name))
        return
    well.latitude, well.longitude = well_locations[well_name]
    
    # Read the stratigraphic layers.
    top_age = surface_age
    top_depth = 0.0
    for layer_index in range(num_layers):
        layer_line = lines[line_index]
        line_index += 1
        
        try:
            bottom_age = float(layer_line[age_column_index:depth_column_index])
            bottom_depth = float(layer_line[depth_column_index:shale_column_index])
        except ValueError:
            warnings.warn('Skipping well file {0}. A layer is missing age or depth.'.format(well_input_filename))
            return
        
        # Convert depth from feet to metres (if necessary).
        if subsidence_units_in_feet:
            bottom_depth *= 3.28084
        
        # Add the 8 hardwired lithology components.
        total_lithology_fraction = 0.0
        lithology_components = []
        for lithology_index in range(0, 8):
            lithology_fraction_string = layer_line[
                lithology_column_indices[lithology_index]:
                lithology_column_indices[lithology_index+1]].strip()
            # Add lithology component unless it's just whitespace.
            if lithology_fraction_string:
                lithology_fraction = float(lithology_fraction_string)
                total_lithology_fraction += lithology_fraction
                lithology_components.append((TXT_LITHOLOGY_NAMES[lithology_index], lithology_fraction))
        
        # Ensure the lithology fractions add up to 1.0.
        for lithology_component_index in range(len(lithology_components)):
            lithology_name, lithology_fraction = lithology_components[lithology_component_index]
            lithology_fraction /= total_lithology_fraction
            lithology_components[lithology_component_index] = lithology_name, lithology_fraction
        
        try:
            min_water_depth = float(layer_line[min_water_depth_column_index:max_water_depth_column_index])
            max_water_depth = float(layer_line[max_water_depth_column_index:sea_column_index])
        except ValueError:
            warnings.warn('Skipping well file {0}. A layer is missing min or max water depth.'.format(well_input_filename))
            return
        # Min/max water depths get added as extra columns since they are only needed for backstripping (not backtracking).
        other_attributes = {
            'min_water_depth': min_water_depth,
            'max_water_depth': max_water_depth}
        
        well.add_compacted_unit(
            top_age, bottom_age,
            top_depth, bottom_depth,
            lithology_components, lithologies,
            other_attributes)
        
        # Bottom of current layer becomes top of next layer.
        top_age = bottom_age
        top_depth = bottom_depth
    
    # Add a '_pybacktrack' suffix to the input base filename.
    well_input_file_dir, well_input_file_basename = os.path.split(well_input_filename)
    well_output_file_dir = os.path.join(well_input_file_dir, 'pybacktrack_format')
    # Create output sub-directory if it doesn't exist.
    if not os.path.isdir(well_output_file_dir):
        os.mkdir(well_output_file_dir)
    well_output_filename = os.path.join(well_output_file_dir, well_input_file_basename)
    
    # Write the well to the pyBacktrack format.
    pybacktrack.write_well_file(
        well,
        well_output_filename,
        other_column_attribute_names=['min_water_depth', 'max_water_depth'],
        well_attributes={'longitude': 'SiteLongitude', 'latitude': 'SiteLatitude'})


if __name__ == '__main__':
    
    # Input data files.
    well_locations_file = 'nwshelf_wells/WELL_LOCATIONS.lst'
    well_dat_files_pattern = 'nwshelf_wells/*.dat'
    well_txt_files_pattern = 'nwshelf_wells/*.txt'
    
    # Read the well locations.
    well_locations = read_well_locations_file(well_locations_file)
    #for well_name, well_location in iteritems(well_locations):
    #    print(well_name, well_location)
    
    # Read all the lithology files and merge their dicts.
    lithologies = pybacktrack.read_lithologies_files(pybacktrack.BUNDLE_LITHOLOGY_FILENAMES)
    
    # Read the ".dat" files.
    dat_filenames = glob.glob(well_dat_files_pattern)
    for dat_filename in dat_filenames:
        convert_dat_file(dat_filename, well_locations, lithologies)
    
    # Read the ".txt" files - they have a slightly different format.
    txt_filenames = glob.glob(well_txt_files_pattern)
    for txt_filename in txt_filenames:
        convert_txt_file(txt_filename, well_locations, lithologies)

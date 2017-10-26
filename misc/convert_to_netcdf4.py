from call_system_command import call_system_command
import glob
import os.path
import re

#
# Convert any NetCDF3 grids to NetCDF4 (since it's compressed).
# We simply use GMT grdconvert to do this.
#
# We also strip away all 
#

input_path = r'E:\Users\John\Downloads\dynamic_topography_reconstruction\models\M7\Dynamic_topography\MantleFrame'
output_path = r'C:\Users\John\Development\Usyd\gplates\source-code\pygplates_scripts\Other\Backstrip\backstrip\bundle_data\dynamic_topography\models\Muller2017\M7'
grid_ext = 'nc'
grid_spacing_degrees = 1.0

grid_filenames = glob.glob(os.path.join(input_path, '*.{0}'.format(grid_ext)))
for grid_filename in grid_filenames:
    # Search for the last integer and assume that is the age.
    age = float(re.findall(r'\d+', grid_filename)[-1])
    output_grid_filename = os.path.join(output_path, '{0:.2f}.{1}'.format(age, grid_ext))
    call_system_command([
        'gmt',
        'grdfilter',
        grid_filename,
        '-G{0}'.format(output_grid_filename),
        '-D4',
        '-Fc{0}'.format(200.0 * grid_spacing_degrees), # 200km filter width (100km radius) per degree of grid spacing
        '-I{0}'.format(grid_spacing_degrees)])

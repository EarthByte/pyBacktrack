import os.path
import pygplates
import sys

#
# Quick test to make sure that, for a particular dynamic topography model, a multipoint that has
# previously been assigned plate IDs matches the static polygons associated with that model.
#
# This is done by comparing the plate IDs of the original multipoint with the plate IDs we will
# assign to this multipoint (in script below) using the static polygons.
# Any differences are printed to console.
#

DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH = r'D:\Users\john\Development\Usyd\gplates\source-code\pygplates_scripts\Other\Backstrip\backstrip\bundle_data\dynamic_topography\reconstructions\2014_1_401'

multipoints_file = os.path.join(DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'lat_lon_velocity_domain_720_1440.gpml')
static_polygons_file = os.path.join(DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'Global_EarthByte_GPlates_PresentDay_StaticPlatePolygons_2014.1.shp')
rotation_files = [
    os.path.join(DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'Global_EarthByte_TPW_GeeK07_2014.1_VanDerMeer_CrossoverFix.rot')
]
# DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH = r'D:\Users\john\Development\Usyd\gplates\source-code\pygplates_scripts\Other\Backstrip\backstrip\bundle_data\dynamic_topography\reconstructions\Global_Model_WD_Internal_Release_2015_v2'
#
# multipoints_file = os.path.join(DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'lat_lon_velocity_domain_720_1440.shp')
# static_polygons_file = os.path.join(DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'Global_EarthByte_GPlates_PresentDay_StaticPlatePolygons_2015_v2.gpmlz')
# rotation_files = [
#     os.path.join(DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'Global_EB_250-0Ma_GK07_2015_v2.rot'),
#     os.path.join(DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'Global_EB_410-250Ma_GK07_2015_v2.rot')
# ]

plate_partitioner = pygplates.PlatePartitioner(static_polygons_file, rotation_files)

failed_multipoints = []
for multipoint in pygplates.FeatureCollection(multipoints_file):
    partitioned_multipoints = plate_partitioner.partition_features(
        multipoint,
        properties_to_copy=[
            pygplates.PartitionProperty.reconstruction_plate_id,
            pygplates.PartitionProperty.valid_time_period])
    
    for partitioned_multipoint in partitioned_multipoints:
        if partitioned_multipoint.get_reconstruction_plate_id() != multipoint.get_reconstruction_plate_id():
            failed_multipoints.append(partitioned_multipoint)
            print 'Failed ({0} points): original plate {1}, new plate {2}'.format(
                  sum(len(geometry) for geometry in partitioned_multipoint.get_geometries()),
                  multipoint.get_reconstruction_plate_id(),
                  partitioned_multipoint.get_reconstruction_plate_id())
        elif partitioned_multipoint.get_valid_time()[0] != multipoint.get_valid_time()[0]:
            print 'Failed ({0} points): original appearance {1}, new appearance {2}'.format(
                  sum(len(geometry) for geometry in partitioned_multipoint.get_geometries()),
                  multipoint.get_valid_time()[0],
                  partitioned_multipoint.get_valid_time()[0])
            failed_multipoints.append(partitioned_multipoint)

if failed_multipoints:
    # Write out the failed multipoints so we can see them in GPlates.
    pygplates.FeatureCollection(failed_multipoints).write(
        os.path.join(DYNAMIC_TOPOGRAPHY_RECONSTRUCTIONS_PATH, 'failed_multipoints.gpml'))
    sys.exit(1)

sys.exit(0)

These 2019 v2 files were obtained from https://www.earthbyte.org/webdav/ftp/Data_Collections/Muller_etal_2019_Tectonics/Muller_etal_2019_PlateMotionModel/ .

To help avoid the 260 character maximum (absolute) path length limit on Windows:
* "Global_250-0Ma_Rotations_2019_v2.rot" was renamed to "rotations_250-0Ma.rot".
* "Global_EarthByte_GPlates_PresentDay_StaticPlatePolygons_2019_v1.shp" was renamed to "static_polygons.shp".

The rift start/end time 5 minute grids were generated with 'misc/generate_rift_grids.py' using the Muller et al. (2019) deforming model to find
when deformation started and ended on submerged continental crust inside extensional deforming areas. A default rifting period of 200-0Ma was used
for non-extensional deforming areas. And non-deforming continental crust locations use the rift period from nearest location in deforming regions.

import pytest
import pybacktrack.backtrack as backtrack
import pybacktrack.bundle_data as bundle_data
import py


def test_backtrack(tmpdir):
    """Test backtrack_and_write_decompacted function in backtrack module."""
    
    # Test data directory is in 'data' sub-directory of directory containing this test module.
    test_data_dir = py.path.local(__file__).dirpath('data')
    
    # Test data filenames.
    input_well_filename = test_data_dir.join('ODP-114-699-Lithology.txt')
    ammended_well_output_base_filename = 'ODP-114-699_backtrack_amended.txt'
    ammended_well_output_filename = test_data_dir.join(ammended_well_output_base_filename)
    decompacted_output_base_filename = 'ODP-114-699_backtrack_decompat.txt'
    decompacted_output_filename = test_data_dir.join(decompacted_output_base_filename)
    
    # We'll be writing to temporary directory (provided by pytest 'tmpdir' fixture).
    test_ammended_well_output_filename = tmpdir.join(ammended_well_output_base_filename)
    test_decompacted_output_filename = tmpdir.join(decompacted_output_base_filename)
    
    #
    # This function call is the equivalent of:
    #
    #     python -m pybacktrack.backtrack
    #         -w tests/data/ODP-114-699-Lithology.txt
    #         -l pybacktrack/bundle_data/lithologies/lithologies.txt
    #         -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density water_depth tectonic_subsidence lithology
    #         -a pybacktrack/bundle_data/age/agegrid_6m.grd
    #         -t pybacktrack/bundle_data/topography/ETOPO1_0.1.grd
    #         -s pybacktrack/bundle_data/sediment_thickness/sedthick_world_v3_5min_epsg4326_cf.nc
    #         -k pybacktrack/bundle_data/crustal_thickness/crsthk.grd
    #         -y pybacktrack/bundle_data/dynamic_topography/models/M2.grids pybacktrack/bundle_data/dynamic_topography/reconstructions/2013.2-r213/static_polygons.shp pybacktrack/bundle_data/dynamic_topography/reconstructions/2013.2-r213/rotations.rot
    #         -sl pybacktrack/bundle_data/sea_level/Haq87_SealevelCurve_Longterm.dat
    #         -o tests/data/ODP-114-699_backtrack_amended.txt
    #         --
    #         tests/data/ODP-114-699_backtrack_decompat.txt
    #
    backtrack.backtrack_and_write_decompacted(
        str(test_decompacted_output_filename),
        str(input_well_filename),
        bundle_data.BUNDLE_LITHOLOGIES_FILENAME,
        bundle_data.BUNDLE_AGE_GRID_FILENAME,
        bundle_data.BUNDLE_TOPOGRAPHY_FILENAME,
        bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,
        bundle_data.BUNDLE_CRUSTAL_THICKNESS_FILENAME,
        bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_INFOS['M2'],
        bundle_data.BUNDLE_SEA_LEVEL_MODEL_FILES['Haq87_SealevelCurve_Longterm'],
        decompacted_columns=[backtrack.COLUMN_AGE, backtrack.COLUMN_COMPACTED_DEPTH,
                             backtrack.COLUMN_COMPACTED_THICKNESS, backtrack.COLUMN_DECOMPACTED_THICKNESS,
                             backtrack.COLUMN_DECOMPACTED_DENSITY, backtrack.COLUMN_WATER_DEPTH,
                             backtrack.COLUMN_TECTONIC_SUBSIDENCE, backtrack.COLUMN_LITHOLOGY],
        ammended_well_output_filename=str(test_ammended_well_output_filename))
    
    # Compare original output files and temporary output files just written.
    assert test_ammended_well_output_filename.read() == ammended_well_output_filename.read()
    assert test_decompacted_output_filename.read() == decompacted_output_filename.read()

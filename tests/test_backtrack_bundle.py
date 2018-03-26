import pytest
import pybacktrack.backtrack_bundle as backtrack_bundle
import py


def test_backtrack_bundle(tmpdir):
    """Test backtrack_and_write_decompacted function in backtrack_bundle module."""
    
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
    #     python -m pybacktrack.backtrack_bundle
    #         -w tests/data/ODP-114-699-Lithology.txt
    #         -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density water_depth tectonic_subsidence lithology
    #         -y M2
    #         -sl Haq87_SealevelCurve_Longterm
    #         -o tests/data/ODP-114-699_backtrack_amended.txt
    #         --
    #         tests/data/ODP-114-699_backtrack_decompat.txt
    #
    backtrack_bundle.backtrack_and_write_decompacted(
        str(test_decompacted_output_filename),
        str(input_well_filename),
        dynamic_topography_model_name='M2',
        sea_level_model_name='Haq87_SealevelCurve_Longterm',
        ammended_well_output_filename=str(test_ammended_well_output_filename),
        decompacted_columns=[0, 7, 5, 1, 2, 4, 3, 6])
    
    # Compare original output files and temporary output files just written.
    assert test_ammended_well_output_filename.read() == ammended_well_output_filename.read()
    assert test_decompacted_output_filename.read() == decompacted_output_filename.read()

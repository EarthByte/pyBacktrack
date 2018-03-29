from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pytest
import pybacktrack.backtrack as backtrack
import py


def test_backtrack_ODP(tmpdir):
    """Test ODP well site using backtrack_and_write_decompacted function in backtrack module."""
    
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
    #         -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density water_depth tectonic_subsidence lithology
    #         -ym M2
    #         -slm Haq87_SealevelCurve_Longterm
    #         -o tests/data/ODP-114-699_backtrack_amended.txt
    #         --
    #         tests/data/ODP-114-699_backtrack_decompat.txt
    #
    backtrack.backtrack_and_write_decompacted(
        str(test_decompacted_output_filename),
        str(input_well_filename),
        dynamic_topography_model='M2',
        sea_level_model='Haq87_SealevelCurve_Longterm',
        decompacted_columns=[backtrack.COLUMN_AGE, backtrack.COLUMN_COMPACTED_DEPTH,
                             backtrack.COLUMN_COMPACTED_THICKNESS, backtrack.COLUMN_DECOMPACTED_THICKNESS,
                             backtrack.COLUMN_DECOMPACTED_DENSITY, backtrack.COLUMN_WATER_DEPTH,
                             backtrack.COLUMN_TECTONIC_SUBSIDENCE, backtrack.COLUMN_LITHOLOGY],
        ammended_well_output_filename=str(test_ammended_well_output_filename))
    
    # Compare original output files and temporary output files just written.
    assert test_ammended_well_output_filename.read() == ammended_well_output_filename.read()
    assert test_decompacted_output_filename.read() == decompacted_output_filename.read()


def test_backtrack_DSDP(tmpdir):
    """Test DSDP well site using backtrack_and_write_decompacted function in backtrack module."""
    
    # Test data directory is in 'data' sub-directory of directory containing this test module.
    test_data_dir = py.path.local(__file__).dirpath('data')
    
    # Test data filenames.
    input_well_filename = test_data_dir.join('DSDP-36-327-Lithology.txt')
    ammended_well_output_base_filename = 'DSDP-36-327_backtrack_amended.txt'
    ammended_well_output_filename = test_data_dir.join(ammended_well_output_base_filename)
    decompacted_output_base_filename = 'DSDP-36-327_backtrack_decompat.txt'
    decompacted_output_filename = test_data_dir.join(decompacted_output_base_filename)
    
    # We'll be writing to temporary directory (provided by pytest 'tmpdir' fixture).
    test_ammended_well_output_filename = tmpdir.join(ammended_well_output_base_filename)
    test_decompacted_output_filename = tmpdir.join(decompacted_output_base_filename)
    
    #
    # This function call is the equivalent of:
    #
    #     python -m pybacktrack.backtrack
    #         -w tests/data/DSDP-36-327-Lithology.txt
    #         -c 0 1 4
    #         -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density water_depth tectonic_subsidence lithology
    #         -ym M2
    #         -slm Haq87_SealevelCurve_Longterm
    #         -o tests/data/DSDP-36-327_backtrack_amended.txt
    #         --
    #         tests/data/DSDP-36-327_backtrack_decompat.txt
    #
    backtrack.backtrack_and_write_decompacted(
        str(test_decompacted_output_filename),
        str(input_well_filename),
        dynamic_topography_model='M2',
        sea_level_model='Haq87_SealevelCurve_Longterm',
        decompacted_columns=[backtrack.COLUMN_AGE, backtrack.COLUMN_COMPACTED_DEPTH,
                             backtrack.COLUMN_COMPACTED_THICKNESS, backtrack.COLUMN_DECOMPACTED_THICKNESS,
                             backtrack.COLUMN_DECOMPACTED_DENSITY, backtrack.COLUMN_WATER_DEPTH,
                             backtrack.COLUMN_TECTONIC_SUBSIDENCE, backtrack.COLUMN_LITHOLOGY],
        well_lithology_column=4,  # Skip min_water_depth and max_water_depth columns (2 and 3).
        ammended_well_output_filename=str(test_ammended_well_output_filename))
    
    # Compare original output files and temporary output files just written.
    assert test_ammended_well_output_filename.read() == ammended_well_output_filename.read()
    assert test_decompacted_output_filename.read() == decompacted_output_filename.read()

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pytest
import pybacktrack
from pybacktrack.util.call_system_command import call_system_command
import py
import sys
import warnings


# Test data directory is inside the pybacktrack module.
TEST_DATA_DIR = py.path.local(__file__).dirpath('..', 'pybacktrack', 'test_data')


def test_backtrack_script(tmpdir):
    """Test the built-in backtrack script."""
    
    # Test data filenames.
    input_well_filename = TEST_DATA_DIR.join('ODP-114-699-Lithology.txt')
    ammended_well_output_base_filename = 'ODP-114-699_backtrack_amended.txt'
    ammended_well_output_filename = TEST_DATA_DIR.join(ammended_well_output_base_filename)
    decompacted_output_base_filename = 'ODP-114-699_backtrack_decompat.txt'
    decompacted_output_filename = TEST_DATA_DIR.join(decompacted_output_base_filename)
    
    # We'll be writing to temporary directory (provided by pytest 'tmpdir' fixture).
    test_ammended_well_output_filename = tmpdir.join(ammended_well_output_base_filename)
    test_decompacted_output_filename = tmpdir.join(decompacted_output_base_filename)
    
    # Use the same python that is running this test.
    python = sys.executable
    if not python:
        python = 'python'
    
    # The command-line strings to execute:
    #
    #     python -m pybacktrack.backtrack
    #         -w test_data/ODP-114-699-Lithology.txt
    #         -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density decompacted_sediment_rate decompacted_depth dynamic_topography water_depth tectonic_subsidence lithology
    #         -ym M2
    #         -slm Haq87_SealevelCurve_Longterm
    #         -o ODP-114-699_backtrack_amended.txt
    #         --
    #         ODP-114-699_backtrack_decompat.txt
    #
    backtrack_script_command_line = [python, '-m', 'pybacktrack.backtrack',
                                     '-w', str(input_well_filename),
                                     '-d', 'age', 'compacted_depth', 'compacted_thickness', 'decompacted_thickness',
                                     'decompacted_density', 'decompacted_sediment_rate', 'decompacted_depth',
                                     'dynamic_topography', 'water_depth', 'tectonic_subsidence', 'lithology',
                                     '-ym', 'M2',
                                     '-slm', 'Haq87_SealevelCurve_Longterm',
                                     '-o', str(test_ammended_well_output_filename),
                                     '--',
                                     str(test_decompacted_output_filename)]
    
    # Call the system command.
    call_system_command(backtrack_script_command_line)
    
    # Compare original output files and temporary output files just written.
    assert test_ammended_well_output_filename.read() == ammended_well_output_filename.read()
    assert test_decompacted_output_filename.read() == decompacted_output_filename.read()


def test_backtrack_ODP(tmpdir):
    """Test ODP well site using the pybacktrack.backtrack_and_write_well function."""
    
    # Test data filenames.
    input_well_filename = TEST_DATA_DIR.join('ODP-114-699-Lithology.txt')
    ammended_well_output_base_filename = 'ODP-114-699_backtrack_amended.txt'
    ammended_well_output_filename = TEST_DATA_DIR.join(ammended_well_output_base_filename)
    decompacted_output_base_filename = 'ODP-114-699_backtrack_decompat.txt'
    decompacted_output_filename = TEST_DATA_DIR.join(decompacted_output_base_filename)
    
    # We'll be writing to temporary directory (provided by pytest 'tmpdir' fixture).
    test_ammended_well_output_filename = tmpdir.join(ammended_well_output_base_filename)
    test_decompacted_output_filename = tmpdir.join(decompacted_output_base_filename)
    
    #
    # This function call is the equivalent of:
    #
    #     python -m pybacktrack.backtrack
    #         -w test_data/ODP-114-699-Lithology.txt
    #         -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density decompacted_sediment_rate decompacted_depth dynamic_topography water_depth tectonic_subsidence lithology
    #         -ym M2
    #         -slm Haq87_SealevelCurve_Longterm
    #         -o ODP-114-699_backtrack_amended.txt
    #         --
    #         ODP-114-699_backtrack_decompat.txt
    #
    pybacktrack.backtrack_and_write_well(
        str(test_decompacted_output_filename),
        str(input_well_filename),
        dynamic_topography_model='M2',
        sea_level_model='Haq87_SealevelCurve_Longterm',
        decompacted_columns=[pybacktrack.BACKTRACK_COLUMN_AGE, pybacktrack.BACKTRACK_COLUMN_COMPACTED_DEPTH, pybacktrack.BACKTRACK_COLUMN_COMPACTED_THICKNESS,
                             pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_THICKNESS, pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_DENSITY,
                             pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_SEDIMENT_RATE, pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_DEPTH,
                             pybacktrack.BACKTRACK_COLUMN_DYNAMIC_TOPOGRAPHY, pybacktrack.BACKTRACK_COLUMN_WATER_DEPTH, pybacktrack.BACKTRACK_COLUMN_TECTONIC_SUBSIDENCE,
                             pybacktrack.BACKTRACK_COLUMN_LITHOLOGY],
        ammended_well_output_filename=str(test_ammended_well_output_filename))
    
    # Compare original output files and temporary output files just written.
    assert test_ammended_well_output_filename.read() == ammended_well_output_filename.read()
    assert test_decompacted_output_filename.read() == decompacted_output_filename.read()


def test_backtrack_DSDP(tmpdir):
    """Test DSDP well site using the pybacktrack.backtrack_and_write_well function."""
    
    # Test data filenames.
    input_well_filename = TEST_DATA_DIR.join('DSDP-36-327-Lithology.txt')
    ammended_well_output_base_filename = 'DSDP-36-327_backtrack_amended.txt'
    ammended_well_output_filename = TEST_DATA_DIR.join(ammended_well_output_base_filename)
    decompacted_output_base_filename = 'DSDP-36-327_backtrack_decompat.txt'
    decompacted_output_filename = TEST_DATA_DIR.join(decompacted_output_base_filename)
    
    # We'll be writing to temporary directory (provided by pytest 'tmpdir' fixture).
    test_ammended_well_output_filename = tmpdir.join(ammended_well_output_base_filename)
    test_decompacted_output_filename = tmpdir.join(decompacted_output_base_filename)
    
    #
    # This function call is the equivalent of:
    #
    #     python -m pybacktrack.backtrack
    #         -w test_data/DSDP-36-327-Lithology.txt
    #         -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density decompacted_sediment_rate decompacted_depth dynamic_topography water_depth tectonic_subsidence lithology
    #         -ym M2
    #         -slm Haq87_SealevelCurve_Longterm
    #         -o DSDP-36-327_backtrack_amended.txt
    #         --
    #         DSDP-36-327_backtrack_decompat.txt
    #
    with warnings.catch_warnings():
        # Ignore user warnings related to dynamic topography.
        warnings.simplefilter("ignore", UserWarning)
        
        pybacktrack.backtrack_and_write_well(
            str(test_decompacted_output_filename),
            str(input_well_filename),
            dynamic_topography_model='M2',
            sea_level_model='Haq87_SealevelCurve_Longterm',
            decompacted_columns=[pybacktrack.BACKTRACK_COLUMN_AGE, pybacktrack.BACKTRACK_COLUMN_COMPACTED_DEPTH, pybacktrack.BACKTRACK_COLUMN_COMPACTED_THICKNESS,
                                 pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_THICKNESS, pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_DENSITY,
                                 pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_SEDIMENT_RATE, pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_DEPTH,
                                 pybacktrack.BACKTRACK_COLUMN_DYNAMIC_TOPOGRAPHY, pybacktrack.BACKTRACK_COLUMN_WATER_DEPTH, pybacktrack.BACKTRACK_COLUMN_TECTONIC_SUBSIDENCE,
                                 pybacktrack.BACKTRACK_COLUMN_LITHOLOGY],
            ammended_well_output_filename=str(test_ammended_well_output_filename))
    
    # Compare original output files and temporary output files just written.
    assert test_ammended_well_output_filename.read() == ammended_well_output_filename.read()
    assert test_decompacted_output_filename.read() == decompacted_output_filename.read()

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


def test_backstrip_script(tmpdir):
    """Test the built-in backstrip script."""
    
    # Test data filenames.
    input_well_filename = TEST_DATA_DIR.join('sunrise_lithology.txt')
    ammended_well_output_base_filename = 'sunrise_backstrip_amended.txt'
    ammended_well_output_filename = TEST_DATA_DIR.join(ammended_well_output_base_filename)
    decompacted_output_base_filename = 'sunrise_backstrip_decompat.txt'
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
    #     python -m pybacktrack.backstrip
    #         -w test_data/sunrise_lithology.txt
    #         -l primary extended
    #         -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density decompacted_sediment_rate decompacted_depth min_tectonic_subsidence max_tectonic_subsidence average_tectonic_subsidence min_water_depth max_water_depth average_water_depth lithology
    #         -slm Haq87_SealevelCurve_Longterm
    #         -o sunrise_backstrip_amended.txt
    #         --
    #         sunrise_backstrip_decompat.txt
    #
    backstrip_script_command_line = [python, '-m', 'pybacktrack.backstrip',
                                     '-w', str(input_well_filename),
                                     '-l', 'primary', 'extended',
                                     '-d', 'age', 'compacted_depth', 'compacted_thickness', 'decompacted_thickness',
                                     'decompacted_density', 'decompacted_sediment_rate', 'decompacted_depth',
                                     'min_tectonic_subsidence', 'max_tectonic_subsidence', 'average_tectonic_subsidence',
                                     'min_water_depth', 'max_water_depth', 'average_water_depth',
                                     'lithology',
                                     '-slm', 'Haq87_SealevelCurve_Longterm',
                                     '-o', str(test_ammended_well_output_filename),
                                     '--',
                                     str(test_decompacted_output_filename)]
    
    # Call the system command.
    call_system_command(backstrip_script_command_line)
    
    # Compare original output files and temporary output files just written.
    assert test_ammended_well_output_filename.read() == ammended_well_output_filename.read()
    assert test_decompacted_output_filename.read() == decompacted_output_filename.read()


def test_backstrip(tmpdir):
    """Test backstrip_and_write_decompacted function."""
    
    # Test data filenames.
    input_well_filename = TEST_DATA_DIR.join('sunrise_lithology.txt')
    ammended_well_output_base_filename = 'sunrise_backstrip_amended.txt'
    ammended_well_output_filename = TEST_DATA_DIR.join(ammended_well_output_base_filename)
    decompacted_output_base_filename = 'sunrise_backstrip_decompat.txt'
    decompacted_output_filename = TEST_DATA_DIR.join(decompacted_output_base_filename)
    
    # We'll be writing to temporary directory (provided by pytest 'tmpdir' fixture).
    test_ammended_well_output_filename = tmpdir.join(ammended_well_output_base_filename)
    test_decompacted_output_filename = tmpdir.join(decompacted_output_base_filename)
    
    #
    # These function calls are the equivalent of:
    #
    #     python -m pybacktrack.backstrip
    #         -w test_data/sunrise_lithology.txt
    #         -l primary extended
    #         -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density decompacted_sediment_rate decompacted_depth min_tectonic_subsidence max_tectonic_subsidence average_tectonic_subsidence min_water_depth max_water_depth average_water_depth lithology
    #         -slm Haq87_SealevelCurve_Longterm
    #         -o sunrise_backstrip_amended.txt
    #         --
    #         sunrise_backstrip_decompat.txt
    #
    with warnings.catch_warnings():
        # Ignore user warnings related to well thickness being larger than total sediment thickness.
        warnings.simplefilter("ignore", UserWarning)
        
        pybacktrack.backstrip_and_write_well(
            str(test_decompacted_output_filename),
            str(input_well_filename),
            lithology_filenames=[pybacktrack.PRIMARY_BUNDLE_LITHOLOGY_FILENAME,
                                 pybacktrack.EXTENDED_BUNDLE_LITHOLOGY_FILENAME],
            sea_level_model='Haq87_SealevelCurve_Longterm',
            decompacted_columns=[pybacktrack.BACKSTRIP_COLUMN_AGE, pybacktrack.BACKSTRIP_COLUMN_COMPACTED_DEPTH, pybacktrack.BACKSTRIP_COLUMN_COMPACTED_THICKNESS, pybacktrack.BACKSTRIP_COLUMN_DECOMPACTED_THICKNESS,
                                 pybacktrack.BACKSTRIP_COLUMN_DECOMPACTED_DENSITY, pybacktrack.BACKSTRIP_COLUMN_DECOMPACTED_SEDIMENT_RATE, pybacktrack.BACKSTRIP_COLUMN_DECOMPACTED_DEPTH,
                                 pybacktrack.BACKSTRIP_COLUMN_MIN_TECTONIC_SUBSIDENCE, pybacktrack.BACKSTRIP_COLUMN_MAX_TECTONIC_SUBSIDENCE, pybacktrack.BACKSTRIP_COLUMN_AVERAGE_TECTONIC_SUBSIDENCE,
                                 pybacktrack.BACKSTRIP_COLUMN_MIN_WATER_DEPTH, pybacktrack.BACKSTRIP_COLUMN_MAX_WATER_DEPTH, pybacktrack.BACKSTRIP_COLUMN_AVERAGE_WATER_DEPTH,
                                 pybacktrack.BACKSTRIP_COLUMN_LITHOLOGY],
            ammended_well_output_filename=str(test_ammended_well_output_filename))
    
    # Compare original output files and temporary output files just written.
    assert test_ammended_well_output_filename.read() == ammended_well_output_filename.read()
    assert test_decompacted_output_filename.read() == decompacted_output_filename.read()

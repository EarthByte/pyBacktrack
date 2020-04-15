from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pytest
import pybacktrack
from pybacktrack.util.call_system_command import call_system_command
import py
import sys


# Test data directory is inside the pybacktrack module.
TEST_DATA_DIR = py.path.local(__file__).dirpath('..', 'pybacktrack', 'test_data')


def test_convert_age_to_depth():
    """Test convert_age_to_depth function."""
    
    assert(2600.0 == pytest.approx(pybacktrack.convert_age_to_depth(0.0, pybacktrack.AGE_TO_DEPTH_MODEL_GDH1)))
    
    # Crosby model not as accurate at 0Ma due to iterative solution.
    assert(2600.0 == pytest.approx(pybacktrack.convert_age_to_depth(0.0, pybacktrack.AGE_TO_DEPTH_MODEL_CROSBY_2007), abs=2.0))
    
    with pytest.raises(ValueError):
        pybacktrack.convert_age_to_depth(-0.01)  # Negative age.


def test_convert_age_to_depth_files(tmpdir):
    """Test convert_age_to_depth_files function."""
    
    # Original input/output age-to-depth test data.
    input_filename = TEST_DATA_DIR.join('test_ages.txt')
    output_base_filename = 'test_depths_from_ages.txt'
    output_filename = TEST_DATA_DIR.join(output_base_filename)
    
    # We'll be writing to temporary directory (provided by pytest 'tmpdir' fixture).
    test_output_filename = tmpdir.join(output_base_filename)
    
    # Convert input ages to output depths and ages (written to temporary output file).
    pybacktrack.convert_age_to_depth_files(
        str(input_filename),
        str(test_output_filename),
        model=pybacktrack.AGE_TO_DEPTH_MODEL_GDH1,
        reverse_output_columns=True)
    
    # Compare original output file and temporary output file just written.
    assert test_output_filename.read() == output_filename.read()


def test_age_to_depth_script(tmpdir):
    """Test the built-in age_to_depth script."""
    
    # Original input/output age-to-depth test data.
    input_filename = TEST_DATA_DIR.join('test_ages.txt')
    output_base_filename = 'test_depths_from_ages.txt'
    output_filename = TEST_DATA_DIR.join(output_base_filename)
    
    # We'll be writing to temporary directory (provided by pytest 'tmpdir' fixture).
    test_output_filename = tmpdir.join(output_base_filename)
    
    # Convert input ages to output depths and ages (written to temporary output file).
    pybacktrack.convert_age_to_depth_files(
        str(input_filename),
        str(test_output_filename),
        model=pybacktrack.AGE_TO_DEPTH_MODEL_GDH1,
        reverse_output_columns=True)
    
    # Use the same python that is running this test.
    python = sys.executable
    if not python:
        python = 'python'
    
    # The command-line strings to execute:
    #
    #     python -m pybacktrack.age_to_depth
    #        -m GDH1
    #        -r
    #        test_data/test_ages.txt
    #        test_depths_from_ages.txt
    #
    age_to_depth_script_command_line = [python, '-m', 'pybacktrack.age_to_depth',
                                        '-m', 'GDH1',
                                        '-r',
                                        str(input_filename),
                                        str(test_output_filename)]
    
    # Call the system command.
    call_system_command(age_to_depth_script_command_line)
    
    # Compare original output file and temporary output file just written.
    assert test_output_filename.read() == output_filename.read()

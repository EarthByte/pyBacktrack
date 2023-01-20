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


def test_convert_stratigraphic_depth_to_age():
    """Test convert_stratigraphic_depth_to_age function."""
    
    # Read the age(depth) function.
    age_depth_filename = TEST_DATA_DIR.join('Site1089B_age_depth.txt')
    depth_column_index = 1
    age_column_index = 0
    depth_to_age_model, _, _ = pybacktrack.read_interpolate_function(age_depth_filename, depth_column_index, age_column_index)
   
    assert(0.331424 == pytest.approx(pybacktrack.convert_stratigraphic_depth_to_age(46, depth_to_age_model)))
    assert(1.710399 == pytest.approx(pybacktrack.convert_stratigraphic_depth_to_age(209.438, depth_to_age_model)))
    
    with pytest.raises(ValueError):
        pybacktrack.convert_stratigraphic_depth_to_age(-0.01, depth_to_age_model)  # Negative depth.


def test_convert_stratigraphic_depth_to_age_files(tmpdir):
    """Test convert_stratigraphic_depth_to_age_files function."""
    
    # Read the age(depth) function.
    age_depth_filename = TEST_DATA_DIR.join('Site1089B_age_depth.txt')
    depth_column_index = 1
    age_column_index = 0
    depth_to_age_model, _, _ = pybacktrack.read_interpolate_function(age_depth_filename, depth_column_index, age_column_index)
    
    # Original input/output depth-to-age test data.
    input_filename = TEST_DATA_DIR.join('Site1089B_strat_depth.txt')
    output_base_filename = 'Site1089B_age_strat_depth.txt'
    output_filename = TEST_DATA_DIR.join(output_base_filename)
    
    # We'll be writing to temporary directory (provided by pytest 'tmpdir' fixture).
    test_output_filename = tmpdir.join(output_base_filename)
    
    # Convert input ages to output depths and ages (written to temporary output file).
    pybacktrack.convert_stratigraphic_depth_to_age_files(
        str(input_filename),
        str(test_output_filename),
        depth_to_age_model)
    
    # Compare original output file and temporary output file just written.
    assert test_output_filename.read() == output_filename.read()


def test_stratigraphic_depth_to_age_script(tmpdir):
    """Test the built-in stratigraphic_depth_to_age script."""
    
    # Read the age(depth) function.
    age_depth_filename = TEST_DATA_DIR.join('Site1089B_age_depth.txt')
    depth_column_index = 1
    age_column_index = 0
    depth_to_age_model, _, _ = pybacktrack.read_interpolate_function(age_depth_filename, depth_column_index, age_column_index)
    
    # Original input/output age-to-depth test data.
    input_filename = TEST_DATA_DIR.join('Site1089B_strat_depth.txt')
    output_base_filename = 'Site1089B_strat_depth_age.txt'
    output_filename = TEST_DATA_DIR.join(output_base_filename)
    
    # We'll be writing to temporary directory (provided by pytest 'tmpdir' fixture).
    test_output_filename = tmpdir.join(output_base_filename)
    
    # Convert input ages to output depths and ages (written to temporary output file).
    pybacktrack.convert_stratigraphic_depth_to_age_files(
        str(input_filename),
        str(test_output_filename),
        depth_to_age_model,
        reverse_output_columns=True)
    
    # Use the same python that is running this test.
    python = sys.executable
    if not python:
        python = 'python'
    
    # The command-line strings to execute:
    #
    #     python -m pybacktrack.stratigraphic_depth_to_age_cli
    #        -m GDH1
    #        -r
    #        test_data/Site1089B_strat_depth.txt
    #        Site1089B_strat_depth_age.txt
    #
    age_to_depth_script_command_line = [python, '-m', 'pybacktrack.stratigraphic_depth_to_age_cli',
                                        '-m', str(age_depth_filename), '0', '1',
                                        '-r',
                                        str(input_filename),
                                        str(test_output_filename)]
    
    # Call the system command.
    call_system_command(age_to_depth_script_command_line)
    
    # Compare original output file and temporary output file just written.
    assert test_output_filename.read() == output_filename.read()

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pytest
import pybacktrack.age_to_depth as age_to_depth
import py


def test_age_to_depth():
    """Test age_to_depth function in age_to_depth module."""
    
    assert(2600.0 == pytest.approx(age_to_depth.age_to_depth(0.0, age_to_depth.MODEL_GDH1)))
    
    # Crosby model not as accurate at 0Ma due to iterative solution.
    assert(2600.0 == pytest.approx(age_to_depth.age_to_depth(0.0, age_to_depth.MODEL_CROSBY_2007), abs=2.0))
    
    with pytest.raises(ValueError):
        age_to_depth.age_to_depth(-0.01)  # Negative age.


def test_age_to_depth_file(tmpdir):
    """Test age_to_depth_file function in age_to_depth module."""
    
    # Test data directory is in 'data' sub-directory of directory containing this test module.
    test_data_dir = py.path.local(__file__).dirpath('data')
    
    # Original input/output age-to-depth test data.
    input_filename = test_data_dir.join('test_ages.txt')
    output_base_filename = 'test_depths_from_ages.txt'
    output_filename = test_data_dir.join(output_base_filename)
    
    # We'll be writing to temporary directory (provided by pytest 'tmpdir' fixture).
    test_output_filename = tmpdir.join(output_base_filename)
    
    # Convert input ages to output depths and ages (written to temporary output file).
    age_to_depth.age_to_depth_file(
        str(input_filename),
        str(test_output_filename),
        model=age_to_depth.MODEL_GDH1,
        reverse_output_columns=True)
    
    # Compare original output file and temporary output file just written.
    assert test_output_filename.read() == output_filename.read()

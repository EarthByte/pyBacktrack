import pytest
import pybacktrack.backstrip as backstrip
import pybacktrack.bundle_data as bundle_data
from pybacktrack.well import write_well_file
import py


def test_backstrip(tmpdir):
    """Test backstrip and write_decompacted functions in backstrip module."""
    
    # Test data directory is in 'data' sub-directory of directory containing this test module.
    test_data_dir = py.path.local(__file__).dirpath('data')
    
    # Test data filenames.
    input_well_filename = test_data_dir.join('DSDP-36-327-Lithology.txt')
    ammended_well_output_base_filename = 'DSDP-36-327_backstrip_amended.txt'
    ammended_well_output_filename = test_data_dir.join(ammended_well_output_base_filename)
    decompacted_output_base_filename = 'DSDP-36-327_backstrip_decompat.txt'
    decompacted_output_filename = test_data_dir.join(decompacted_output_base_filename)
    
    # We'll be writing to temporary directory (provided by pytest 'tmpdir' fixture).
    test_ammended_well_output_filename = tmpdir.join(ammended_well_output_base_filename)
    test_decompacted_output_filename = tmpdir.join(decompacted_output_base_filename)
    
    #
    # These function calls are the equivalent of:
    #
    #     python -m pybacktrack.backstrip
    #         -w tests/data/DSDP-36-327-Lithology.txt
    #         -l pybacktrack/bundle_data/lithologies/lithologies.txt
    #         -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density average_tectonic_subsidence average_water_depth lithology
    #         -s pybacktrack/bundle_data/sediment_thickness/sedthick_world_v3_5min_epsg4326_cf.nc
    #         -sl pybacktrack/bundle_data/sea_level/Haq87_SealevelCurve_Longterm.dat
    #         -o tests/data/DSDP-36-327_backstrip_amended.txt
    #         --
    #         tests/data/DSDP-36-327_backstrip_decompat.txt
    #
    
    # Decompact the well.
    well, decompacted_wells = backstrip.backstrip(
        str(input_well_filename),
        bundle_data.BUNDLE_LITHOLOGIES_FILENAME,
        bundle_data.BUNDLE_TOTAL_SEDIMENT_THICKNESS_FILENAME,
        bundle_data.BUNDLE_SEA_LEVEL_MODELS['Haq87_SealevelCurve_Longterm'])
    
    # Attributes of well object to write to file as metadata.
    well_attributes = {'longitude': 'SiteLongitude', 'latitude': 'SiteLatitude'}
    
    # Write out amended well data (ie, extra stratigraphic base unit).
    write_well_file(
        well,
        str(test_ammended_well_output_filename),
        ['min_water_depth', 'max_water_depth'],
        # Attributes of well object to write to file as metadata...
        well_attributes=well_attributes)
    
    # Write the decompactions of the well at the ages of its stratigraphic units.
    backstrip.write_decompacted_wells(
        decompacted_wells,
        str(test_decompacted_output_filename),
        well,
        # Attributes of well object to write to file as metadata...
        well_attributes,
        decompacted_columns=[backstrip.COLUMN_AGE, backstrip.COLUMN_COMPACTED_DEPTH, backstrip.COLUMN_COMPACTED_THICKNESS,
                             backstrip.COLUMN_DECOMPACTED_THICKNESS, backstrip.COLUMN_DECOMPACTED_DENSITY,
                             backstrip.COLUMN_AVERAGE_TECTONIC_SUBSIDENCE, backstrip.COLUMN_AVERAGE_WATER_DEPTH, backstrip.COLUMN_LITHOLOGY])
    
    # Compare original output files and temporary output files just written.
    assert test_ammended_well_output_filename.read() == ammended_well_output_filename.read()
    assert test_decompacted_output_filename.read() == decompacted_output_filename.read()

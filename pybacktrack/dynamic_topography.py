
#
# Copyright (C) 2018 The University of Sydney, Australia
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License, version 2, as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

"""Reconstruct point locations and sample the time-dependent dynamic topography *mantle* frame grid files.

:class:`pybacktrack.DynamicTopography` can be used to query dynamic topography.
"""


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import codecs
import math
import os.path
import pybacktrack.bundle_data
from pybacktrack.util.call_system_command import call_system_command
import pygplates
import sys


class DynamicTopography(object):
    """
    Class to reconstruct ocean point location and sample the time-dependent dynamic topography *mantle* frame grid files.
    """
    
    def __init__(self, grid_list_filename, static_polygon_filename, rotation_filenames, longitude, latitude, age=None):
        """
        Load dynamic topography grid filenames and associated ages from grid list file 'grid_list_filename'.
        
        Parameters
        ----------
        grid_list_filename : str
            The filename of the grid list file.
        static_polygon_filename : str
            The filename of the static polygons file.
        rotation_filenames : list of str
            The list of rotation filenames.
        longitude : float
            Longitude of the ocean point location.
        latitude : float
            Latitude of the ocean point location.
        age : float, optional
            The age of the crust that the point location is on.
            If not specified then the appearance age of the static polygon containing the point is used.
        
        Notes
        -----
        Each row in the grid list file should contain two columns. First column containing
        filename (relative to directory of list file) of a dynamic topography grid at a particular time.
        Second column containing associated time (in Ma).
        
        The present day location ('longitude' / 'latitude' in degrees) is also assigned a plate ID using the static polygons,
        and the rotations are used to reconstruct the location when sampling the grids at a reconstructed time.
        """
        
        self.location = pygplates.PointOnSphere((latitude, longitude))
        self.age = age
        
        self.grids = TimeDependentGrid(grid_list_filename)
        self.rotation_model = pygplates.RotationModel(rotation_filenames)
        
        # Find the plate ID of the static polygon containing the location (or zero if not in any plates).
        plate_partitioner = pygplates.PlatePartitioner(static_polygon_filename, self.rotation_model)
        partitioning_plate = plate_partitioner.partition_point(self.location)
        if partitioning_plate:
            self.reconstruction_plate_id = partitioning_plate.get_feature().get_reconstruction_plate_id()
        else:
            self.reconstruction_plate_id = 0
        
        # Use the age of the containing static polygon if location is None (ie, outside age grid).
        if self.age is None:
            if partitioning_plate:
                self.age, _ = partitioning_plate.get_feature().get_valid_time()
            else:
                self.age = 0.0
    
    @staticmethod
    def create_from_bundled_model(dynamic_topography_model_name, longitude, latitude, age=None):
        """create_from_bundled_model(dynamic_topography_model_name)
        Create a DynamicTopography instance from a bundled dynamic topography model name.
        
        Parameters
        ----------
        dynamic_topography_model_name : string
            Name of a bundled dynamic topography model.
            Choices include ``terra``, ``M1``, ``M2``, ``M3``, ``M4``, ``M5``, ``M6``, ``M7``, ``ngrand``, ``s20rts`` and ``smean``.
        longitude : float
            Longitude of the ocean point location.
        latitude : float
            Latitude of the ocean point location.
        age : float, optional
            The age of the crust that the point location is on.
            If not specified then the appearance age of the static polygon containing the point is used.
        
        Returns
        -------
        :class:`pybacktrack.DynamicTopography`
            The bundled dynamic topography model.
        
        Raises
        ------
        ValueError
            If ``dynamic_topography_model_name`` is not the name of a bundled dynamic topography model.
        """
        
        if dynamic_topography_model_name not in pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_NAMES:
            raise ValueError("'dynamic_topography_model_name' should be one of {0}.".format(
                ', '.join(pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_NAMES)))
        
        dynamic_topography_model = pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS[dynamic_topography_model_name]
        dynamic_topography_list_filename, dynamic_topography_static_polygon_filename, dynamic_topography_rotation_filenames = dynamic_topography_model
        
        return DynamicTopography(
            dynamic_topography_list_filename, dynamic_topography_static_polygon_filename, dynamic_topography_rotation_filenames,
            longitude, latitude, age)
    
    def sample(self, time):
        """
        Samples the time-dependent grid files at 'time' at the internal location.
        
        Parameters
        ----------
        time : float
            Time to sample dynamic topography.
        
        Returns
        -------
        float
            The sampled dynamic topography value.
            
            This will be ``float('NaN`)`` if:
            
            - ``time`` is outside age range of grids, or
            - the age of either (of two) interpolated grids is older than age of the ocean point location.
        
        Notes
        -----
        The location is first reconstructed to the two grid ages bounding 'time' before sampling
        the two grids (and interpolating between them).
        """
        
        # Search for the two grids bounding 'time'.
        grids_bounding_time = self.grids.get_grids_bounding_time(time)
        # Return NaN if 'time' outside age range of grids.
        if grids_bounding_time is None:
            return float('nan')
        
        (grid_age_0, grid_filename_0), (grid_age_1, grid_filename_1) = grids_bounding_time
        
        # If the age of the older grid is prior to appearance of location then return NaN.
        if grid_age_1 > self.age + 1e-6:
            return float('nan')
        
        # If 'time' matches either grid age then sample associated grid.
        if math.fabs(time - grid_age_0) < 1e-6:
            return self._sample_grid(grid_age_0, grid_filename_0)
        if math.fabs(time - grid_age_1) < 1e-6:
            return self._sample_grid(grid_age_1, grid_filename_1)
        
        # Sample both grids (we'll interpolate between them).
        grid_value_0 = self._sample_grid(grid_age_0, grid_filename_0)
        grid_value_1 = self._sample_grid(grid_age_1, grid_filename_1)
        
        # If either value is NaN then return NaN.
        # This shouldn't happen since mantle-frame grids have global coverage.
        if math.isnan(grid_value_0) or math.isnan(grid_value_1):
            return float('nan')
        
        # Linearly interpolate.
        # We already know that no two ages are the same (from TimeDependentGrid constructor).
        # So divide-by-zero is not possible.
        return ((grid_age_1 - time) * grid_value_0 + (time - grid_age_0) * grid_value_1) / (grid_age_1 - grid_age_0)
    
    def sample_oldest(self):
        """
        Samples the oldest grid file that is younger than the age-of-appearance of the ocean point location.
        
        Returns
        -------
        grid_value : float
            The sampled dynamic topography value.
        grid_age : float
            The age of the oldest grid file that is younger than the age-of-appearance of the ocean point location.
        
        Notes
        -----
        This function is useful when :meth:`pybacktrack.DynamicTopography.sample` has already been called but returns ``float('NaN')``
        due to the specific time having bounding grid times older than the ocean floor at that location.
        """
        
        # Search backward until we find a grid age younger than the age of the internal location.
        for index in range(len(self.grids.grid_ages_and_filenames) - 1, -1, -1):
            grid_age, grid_filename = self.grids.grid_ages_and_filenames[index]
            if grid_age < self.age + 1e-6:
                grid_value = self._sample_grid(grid_age, grid_filename)
                return grid_value, grid_age
        
        # Unable to sample a non-NaN grid value, so just return NaN.
        first_grid_age, _ = self.grid_ages_and_filenames[0]
        return float('nan'), first_grid_age
    
    def _sample_grid(self, grid_age, grid_filename):
        
        # Get rotation from present day to 'grid_age' using the reconstruction plate ID of the location.
        rotation = self.rotation_model.get_rotation(grid_age, self.reconstruction_plate_id)
        
        # Reconstruct location to 'grid_age'.
        reconstructed_location = rotation * self.location
        reconstructed_latitude, reconstructed_longitude = reconstructed_location.to_lat_lon()
        
        #
        # Sample mantle frame grid.
        #
        
        location_data = '{0} {1}\n'.format(reconstructed_longitude, reconstructed_latitude)

        # The command-line strings to execute GMT 'grdtrack'.
        grdtrack_command_line = ["gmt", "grdtrack", "-G{0}".format(grid_filename.encode(sys.getfilesystemencoding()))]
        
        # Call the system command.
        stdout_data = call_system_command(grdtrack_command_line, stdin=location_data, return_stdout=True)
        
        # GMT grdtrack returns a single line containing "longitude latitude sampled_value".
        # Note that if GMT returns "NaN" then we'll return float('nan').
        return float(stdout_data.split()[2])


class TimeDependentGrid(object):
    """
    Class to sample the time-dependent grid files.
    """
    
    def __init__(self, grid_list_filename):
        """
        Load grid filenames and associated ages from grid list file 'grid_list_filename'.
        
        Raises ValueError if:
        - not all rows contain a grid filename followed by age, or
        - there are two ages in list file with same age, or
        - list file contains fewer than two grids.
        """
        
        self.grid_list_filename = grid_list_filename
        
        self.grid_ages_and_filenames = []
        
        # Grid filenames in the list file are relative to the directory of the list file.
        grids_relative_dir = os.path.dirname(grid_list_filename)
        
        # Read list of grids and associated ages.
        #
        # Assume file is encoded as UTF8 (which includes basic 7-bit ascii).
        detect_duplicate_ages = set()
        with codecs.open(grid_list_filename, 'r', 'utf-8') as grid_list_file:
            for line_number, line in enumerate(grid_list_file):
                line_number = line_number + 1  # Make line number 1-based instead of 0-based.
                if line.strip().startswith('#'):  # Skip comments.
                    continue
                row = line.split()
                if len(row) != 2:
                    raise ValueError(u'Grid list file "{0}" does not contain two columns at line {1}.'.format(
                        grid_list_filename, line_number))
                
                grid_filename = os.path.join(grids_relative_dir, row[0])
                try:
                    grid_age = float(row[1])
                except ValueError:
                    # Re-raise error with different error message.
                    raise ValueError(u'Grid list file "{0}" does not contain a valid age (2nd column) at line {1}.'.format(
                        grid_list_filename, line_number))
                
                # Make sure same age doesn't appear twice.
                if grid_age in detect_duplicate_ages:
                    raise ValueError(u'There are two ages in grid list file "{0}" with the same value {1}.'.format(
                        grid_list_filename, grid_age))
                detect_duplicate_ages.add(grid_age)
                
                self.grid_ages_and_filenames.append((grid_age, grid_filename))
        
        # Sort in order of increasing age.
        self.grid_ages_and_filenames.sort()
        
        # Need at least two grids.
        if len(self.grid_ages_and_filenames) < 2:
            raise ValueError(u'The grid list file "{0}" contains fewer than two grids.'.format(grid_list_filename))
    
    def sample(self, longitude, latitude, time):
        """
        Samples the time-dependent grid files at 'time' and the 'longitude' / 'latitude' location (in degrees).
        
        Returns sampled float value (which can be NaN if location is in a masked region of grid).
        """
        
        # Search for ages neighbouring 'time'.
        grids_bounding_time = self.get_grids_bounding_time(time)
        # Return NaN if 'time' outside age range of grids.
        if grids_bounding_time is None:
            return float('nan')
        
        (grid_age_0, grid_filename_0), (grid_age_1, grid_filename_1) = grids_bounding_time
        
        # If 'time' matches either grid age then sample associated grid.
        if math.fabs(time - grid_age_0) < 1e-6:
            return _sample_grid(longitude, latitude, grid_filename_0)
        if math.fabs(time - grid_age_1) < 1e-6:
            return _sample_grid(longitude, latitude, grid_filename_1)
        
        grid_value_0 = _sample_grid(longitude, latitude, grid_filename_0)
        grid_value_1 = _sample_grid(longitude, latitude, grid_filename_1)
        
        # If either value is NaN then return NaN.
        if math.isnan(grid_value_0) or math.isnan(grid_value_1):
            # Need to interpolate between grids but one grid's value is invalid.
            return float('nan')
        
        # Linearly interpolate.
        # We've already verified in constructor that no two ages are the same (so divide-by-zero is not possible).
        return ((grid_age_1 - time) * grid_value_0 + (time - grid_age_0) * grid_value_1) / (grid_age_1 - grid_age_0)
    
    def get_grids_bounding_time(self, time):
        """
        Returns the two adjacent grid files (and associated times) that surround 'time' as the 2-tuple
        ((grid_age_0, grid_filename_0), (grid_age_1, grid_filename_1)).
        
        Returns None if 'time' is outside time range of grids.
        """
        
        # Search for ages neighbouring 'time'.
        first_grid_age, _ = self.grid_ages_and_filenames[0]
        if time < first_grid_age - 1e-6:
            # Time is outside grid age range ('time' is less than first grid age).
            return None
        
        for grid_index in range(1, len(self.grid_ages_and_filenames)):
            grid_age_1, grid_filename_1 = self.grid_ages_and_filenames[grid_index]
            
            if time < grid_age_1 + 1e-6:
                grid_age_0, grid_filename_0 = self.grid_ages_and_filenames[grid_index - 1]
                return (
                    (grid_age_0, grid_filename_0),
                    (grid_age_1, grid_filename_1)
                )
        
        # Time is outside grid age range ('time' is greater than last grid age).
        return None
    
    def sample_oldest_unmasked(self, longitude, latitude):
        """
        Samples the oldest grid file that gives an unmasked value (non-NaN) at the 'longitude' / 'latitude' location (in degrees).
        
        This function is useful when 'sample()' has already been called but returns NaN due to the specific time being
        older than the ocean floor at that location (or the plate frame grids were reconstructed using static polygons
        but without using age grid, resulting in static-polygon-sized chunks of the grid disappearing back through time rather
        than the more gradual disappearance due to using age grid for appearance times in reconstruction as opposed to using
        appearance times from static polygons).
        
        Returns 2-tuple (value, age) where sampled value can be still be NaN if present-day grid does not have full global coverage.
        """
        
        # Search backward until we sample a non-NaN grid value at requested location.
        for index in range(len(self.grid_ages_and_filenames) - 1, -1, -1):
            grid_age, grid_filename = self.grid_ages_and_filenames[index]
            
            grid_value = _sample_grid(longitude, latitude, grid_filename)
            if not math.isnan(grid_value):
                return grid_value, grid_age
            
        # Unable to sample a non-NaN grid value, so just return NaN.
        first_grid_age = self.grid_ages_and_filenames[0][0]
        return float('nan'), first_grid_age

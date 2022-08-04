
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

import argparse
import codecs
import math
import numpy as np
import os.path
import pybacktrack.bundle_data
from pybacktrack.util.call_system_command import call_system_command
import pygplates
import sys
import warnings


class DynamicTopography(object):
    """
    Class that reconstructs point location(s) and samples (and interpolates) time-dependent dynamic topography *mantle* frame grid files.
    
    Attributes
    ----------
    longitude : float or list of float
        Longitude of the point location, or list of longitudes (if multiple point locations).
    latitude : float or list of float
        Latitude of the point location, or list of latitudes (if multiple point locations).
    age : float or list of float
        The age of the crust that the point location is on, or list of ages (if multiple point locations).
        
        .. note:: If no age(s) was supplied then the age(s) of the static polygon(s)
                  containing location(s) is used (or zero when no polygon contains a location).
        
    Notes
    -----
    .. versionchanged:: 1.4
        Can have multiple point locations (version 1.3 allowed only one location).
        So ``longitude``, ``latitude`` and ``age`` can all have either a single value or multiple values (same number for each).
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
        longitude : float or list of float
            Longitude of the point location, or list of longitudes (if multiple point locations).
        latitude : float or list of float
            Latitude of the point location, or list of latitudes (if multiple point locations).
        age : float or list of float, optional
            The age of the crust that the point location is on, or list of ages (if multiple point locations).
            If not specified then the appearance age(s) of the static polygon(s) containing the point(s) is used.
        
        Raises
        ------
        ValueError
            If any ``age`` is negative (if specified).
        ValueError
            If ``longitude`` and ``latitude`` (and ``age`` if specified) are all not a single value or all not a sequence (of same length).
        ValueError
            If ``grid_list_filename`` does not contain a grid at present day, or
            ``grid_list_filename`` contains fewer than two grids, or
            not all rows in ``grid_list_filename`` contain a grid filename followed by an age, or
            there are two ages in ``grid_list_filename`` with same age.
        
        Notes
        -----
        Each dynamic topography grid should be in the *mantle* reference frame (not *plate* reference frame) and
        should have global coverage (such that no sample location will return NaN).
        
        Each row in the grid list file should contain two columns. First column containing
        filename (relative to directory of list file) of a dynamic topography grid at a particular time.
        Second column containing associated time (in Ma).

        Each present day location is also assigned a plate ID using the static polygons,
        and the rotations are used to reconstruct each location when sampling the grids at a reconstructed time.
        
        .. versionchanged:: 1.4
           The following changes were made:

           - Added ability to specify a list of point locations (as an alternative to specifying a single location).
           - Raises ``ValueError`` if there's no present day grid or if any age is negative.
        """
        
        # For interpolating dynamic topography grids at reconstructed locations.
        self.interpolate_dynamic_topography = InterpolateDynamicTopography(grid_list_filename)

        # Rotation model for reconstructing locations.
        self.rotation_model = pygplates.RotationModel(rotation_filenames)
        
        # Find the plate ID of the static polygon containing the location (or zero if not in any plates).
        plate_partitioner = pygplates.PlatePartitioner(static_polygon_filename, self.rotation_model)

        # See if we've been provided a single location or a sequence of locations (by seeing if we can iterate over longitude or not).
        try:
            iter(longitude)
        except TypeError: # longitude is a single value ...
            self.is_sequence_of_locations = False
        else: # longitude is a sequence ...
            self.is_sequence_of_locations = True
        
        # Make sure latitude is the same type as longitude (ie, a sequence or a single value).
        try:
            iter(latitude)
        except TypeError: # latitude is a single value ...
            if self.is_sequence_of_locations:
                raise ValueError('longitude is a sequence but latitude is a single value')
        else: # latitude is a sequence ...
            if not self.is_sequence_of_locations:
                raise ValueError('longitude is a single value but latitude is a sequence')
        
        # Make sure age (if specified) is the same type as longitude and latitude (ie, a sequence or a single value).
        if age is not None:
            try:
                iter(age)
            except TypeError: # age is a single value ...
                if self.is_sequence_of_locations:
                    raise ValueError('longitude and latitude are sequences but age is a single value')
            else: # age is a sequence ...
                if not self.is_sequence_of_locations:
                    raise ValueError('longitude and latitude are single values but age is a sequence')
        
        # If sequences, make sure longitude, latitude and optional age are the same length.
        if self.is_sequence_of_locations:
            if len(longitude) != len(latitude):
                raise ValueError('longitude and latitude sequences are not the same length')
            if age is not None:
                if len(longitude) != len(age):
                    raise ValueError('age sequence is not same length as longitude and latitude sequences')

        # Create a sequence of pygplates.PointOnSphere for use with reconstructing.
        if self.is_sequence_of_locations:
            self._locations = [pygplates.PointOnSphere(latitude[index], longitude[index]) for index in range(len(longitude))]
        else:
            # Sequence containing a single item.
            self._locations = [pygplates.PointOnSphere(latitude, longitude)]

        # Creat a sequence of ages (in self._ages).
        if age is None:
            # We'll initialise the age(s) below.
            self._ages = []
        else:
            if self.is_sequence_of_locations:
                # Already a sequence of ages.
                self._ages = age
            else:
                # Turn into a sequence of ages (a sequence containing a single age).
                self._ages = [age]

        self.reconstruction_plate_id =  []

        # Assign a plate ID to each location (and optionally an age if not already provided).
        for point in self._locations:
            partitioning_plate = plate_partitioner.partition_point(point)
            if partitioning_plate:
                reconstruction_plate_id = partitioning_plate.get_feature().get_reconstruction_plate_id()
            else:
                reconstruction_plate_id = 0
            self.reconstruction_plate_id.append(reconstruction_plate_id)
        
            # Use the age of the containing static polygon if age not provided (eg, if outside age grid).
            if age is None:
                if partitioning_plate:
                    time_of_appearance, _ = partitioning_plate.get_feature().get_valid_time()
                else:
                    time_of_appearance = 0.0
                self._ages.append(time_of_appearance)
        
        if any(a < 0 for a in self._ages):
            raise ValueError('Dynamic topography: age values must not be negative')
        
        # Attributes used by clients of this class.
        #
        # Note: These attributes are either a list of values or a single value (similar to what client passed into constructor).
        self.longitude = longitude
        self.latitude = latitude
        if age is None:
            if self.is_sequence_of_locations:
                self.age = self._ages
            else:
                # Extract single age.
                self.age = self._ages[0]
        else:
            self.age = age

    
    @staticmethod
    def create_from_bundled_model(dynamic_topography_model_name, longitude, latitude, age=None):
        """create_from_bundled_model(dynamic_topography_model_name, longitude, latitude, age=None)
        Create a DynamicTopography instance from a bundled dynamic topography model name.
        
        Parameters
        ----------
        dynamic_topography_model_name : str
            Name of a bundled dynamic topography model.
            Choices include ``terra``, ``M1``, ``M2``, ``M3``, ``M4``, ``M5``, ``M6``, ``M7``, ``ngrand``, ``s20rts``, ``smean``, ``AY18`` and ``KM16``.
        longitude : float or list of float
            Longitude of the point location, or list of longitudes (if multiple point locations).
        latitude : float or list of float
            Latitude of the point location, or list of latitudes (if multiple point locations).
        age : float or list of float, optional
            The age of the crust that the point location is on, or list of ages (if multiple point locations).
            If not specified then the appearance age(s) of the static polygon(s) containing the point(s) is used.
        
        Returns
        -------
        :class:`pybacktrack.DynamicTopography`
            The bundled dynamic topography model.
        
        Raises
        ------
        ValueError
            If ``dynamic_topography_model_name`` is not the name of a bundled dynamic topography model.
        
        Notes
        -----
        .. versionadded:: 1.2
        
        .. versionchanged:: 1.4
           Added ability to specify a list of point locations (as an alternative to specifying a single location).
        """
        
        if dynamic_topography_model_name not in pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_NAMES:
            raise ValueError("'dynamic_topography_model_name' should be one of {0}.".format(
                ', '.join(pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_NAMES)))
        
        dynamic_topography_model = pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS[dynamic_topography_model_name]
        dynamic_topography_list_filename, dynamic_topography_static_polygon_filename, dynamic_topography_rotation_filenames = dynamic_topography_model
        
        return DynamicTopography(
            dynamic_topography_list_filename, dynamic_topography_static_polygon_filename, dynamic_topography_rotation_filenames,
            longitude, latitude, age)
    
    @staticmethod
    def create_from_model_or_bundled_model_name(dynamic_topography_model_or_bundled_model_name, longitude, latitude, age=None):
        """create_from_model_or_bundled_model_name(dynamic_topography_model_or_bundled_model_name, longitude, latitude, age=None)
        Create a DynamicTopography instance from a user-provided model or from a bundled model.
        
        Parameters
        ----------
        dynamic_topography_model_or_bundled_model_name : str or 3-tuple (str, str, list of str)
            Either the name of a bundled dynamic topography model (see :meth:`pybacktrack.DynamicTopography.create_from_bundled_model`), or
            a user-provided model specified as a 3-tuple (filename of the grid list file, filename of the static polygons file, list of rotation filenames)
            (see first three parameters of :meth:`pybacktrack.DynamicTopography.__init__`).
        longitude : float or list of float
            Longitude of the point location, or list of longitudes (if multiple point locations).
        latitude : float or list of float
            Latitude of the point location, or list of latitudes (if multiple point locations).
        age : float or list of float, optional
            The age of the crust that the point location is on, or list of ages (if multiple point locations).
            If not specified then the appearance age(s) of the static polygon(s) containing the point(s) is used.
        
        Returns
        -------
        :class:`pybacktrack.DynamicTopography`
            The dynamic topography model loaded from a user-provided model or from a bundled model.
        
        Notes
        -----
        .. versionadded:: 1.4
        """
        
        # If a dynamic topography *bundled model name* was specified then create it from a bundled dynamic topography model.
        if isinstance(dynamic_topography_model_or_bundled_model_name, str if sys.version_info[0] >= 3 else basestring):  # Python 2 vs 3.
            return DynamicTopography.create_from_bundled_model(dynamic_topography_model_or_bundled_model_name, longitude, latitude, age)
        else:
            # Otherwise we're expecting a 3-tuple.
            dynamic_topography_list_filename, dynamic_topography_static_polygon_filename, dynamic_topography_rotation_filenames = dynamic_topography_model_or_bundled_model_name
            return DynamicTopography(dynamic_topography_list_filename, dynamic_topography_static_polygon_filename, dynamic_topography_rotation_filenames, longitude, latitude, age)
    
    def sample(self, time, fallback=True):
        """
        Samples and interpolates the two time-dependent dynamic topography grids surrounding ``time`` at point location(s) reconstructed to ``time``,
        but optionally falls back to a non-optimal sampling if necessary (depending on ``time``)
        
        Parameters
        ----------
        time : float
            Time to sample dynamic topography.
        fallback : bool
            Whether to fall back to a non-optimal sampling if neccessary (see notes below).
            Defaults to ``True``.
        
        Returns
        -------
        float or list of float
            The sampled dynamic topography value or list of values.
            If constructed with a single location then returns a single value, otherwise
            returns a list of values (one per location).

            When ``fallback`` is ``True`` then ``float('NaN`)`` will never be returned (see notes below).
            When ``fallback`` is ``False`` then ``float('NaN`)`` will be returned:

            - for all points when the oldest dynamic topography grid is younger than ``time``, or
            - for each point location whose age is younger than ``time`` (ie, has not yet appeared).
        
        Notes
        -----
        Each point location is first reconstructed to ``time`` before sampling the two grids surrounding ``time``
        at the reconstructed location and interpolating between them.

        For each point location, if ``time`` is older than its appearance age then it is still reconstructed to ``time``
        when ``fallback`` is ``True``, otherwise ``float('NaN`)`` is returned (for that location) when ``fallback`` is ``False``.
        
        If ``time`` is older than the oldest grid then the oldest grid is sampled when ``fallback`` is ``True``,
        otherwise ``float('NaN`)`` is returned for all locations when ``fallback`` is ``False``.
        
        .. versionchanged:: 1.2
           Previously this method was called *sample_interpolated* and did not fall back to non-optimal sampling when necessary.
        
        .. versionchanged:: 1.4
           The following changes were made:

           - Merged *sample*, *sample_interpolated* and *sample_oldest* methods into one method (this method).
           - Added *fallback* parameter (where ``False`` behaves like removed *sample_interpolated* method).
           - Added ability to specify a list of point locations (as an alternative to specifying a single location).
           - Changed how grids are interpolated:

             * Version 1.3 (and earlier) reconstructed each location to two times (of the two grids surrounding ``time``) to get *two* reconstructed locations.
               Then each reconstructed location sampled its respective grid (ie, each grid was sampled at a *different* reconstructed location).
               Then these two samples were interpolated (based on ``time``).
             * Version 1.4 reconstructs each location to the single ``time`` to get a *single* reconstructed location.
               Then that single reconstructed location samples both grids surrounding ``time`` (ie, each grid is sampled at the *same* reconstructed location).
               Then these two samples are interpolated (based on ``time``).
             
             ...note that there is no difference *at* grid times (only between grid times).
        """

        grid_sample = [float('nan')] * len(self._locations)

        # Reconstruct the present day locations to 'time'.
        gmt_reconstructed_locations = []
        location_point_indices = []  # Keep track of where to write sampled locations back to.
        for point_index in range(len(self._locations)):
            if not fallback:
                # Fallback is disabled so we should not reconstruct to times earlier than the location's appearance age.
                # Skip locations that appear after 'time' (leave them as NaN to indicate this).
                if time > self._ages[point_index] + 1e-6:
                    continue
            # else: Fallback is enabled so allow a location to be reconstructed earlier than its time of appearance.
            #       There's a small chance that its rotation doesn't extend earlier than its appearance age but
            #       the caller shouldn't really be using values sampled much earlier than the appearance age anyway.
            
            # Get rotation from present day to 'time' using the reconstruction plate ID of the location.
            rotation = self.rotation_model.get_rotation(time, self.reconstruction_plate_id[point_index])
            
            # Reconstruct location to 'time'.
            reconstructed_location = rotation * self._locations[point_index]
            gmt_reconstructed_latitude, gmt_reconstructed_longitude = reconstructed_location.to_lat_lon()

            gmt_reconstructed_locations.append((gmt_reconstructed_longitude, gmt_reconstructed_latitude))
            location_point_indices.append(point_index)

        # If there are no reconstructed locations to sample.
        if not gmt_reconstructed_locations:
            return grid_sample  # All NaNs.
        
        # Sample the dynamic topography at the reconstructed locations.
        sampled_values = self.interpolate_dynamic_topography.sample(time, gmt_reconstructed_locations, fallback)

        # If 'time' is older than oldest dynamic topography grid then return all grid samples as NaN.
        # Note: Can only happen when 'fallback' is False.
        if sampled_values is None:
            return grid_sample  # All NaNs.

        # Extract the sampled values (and write them back to correct index in returned grid sample).
        for sample_index, sampled_value in enumerate(sampled_values):
            # The output sampled values should be in the same order as the input reconstructed locations.
            point_index = location_point_indices[sample_index]
            grid_sample[point_index] = sampled_value
        
        # If constructed with a single location then return a single grid value, otherwise return a sequence.
        if self.is_sequence_of_locations:
            return grid_sample
        else:
            return grid_sample[0]


class InterpolateDynamicTopography(object):
    """
    Class that just samples and interpolates time-dependent dynamic topography *mantle* frame grid files.

    This class accepts locations that have already been reconstructed whereas :class:`pybacktrack.DynamicTopography`
    accepts present day locations and reconstructs them prior to sampling the dynamic topography grids.
        
    Notes
    -----
    .. versionadded:: 1.4
    """
    
    def __init__(self, grid_list_filename):
        """
        Load dynamic topography grid filenames and associated ages from grid list file 'grid_list_filename'.
        
        Parameters
        ----------
        grid_list_filename : str
            The filename of the grid list file.
        
        Raises
        ------
        ValueError
            If ``grid_list_filename`` does not contain a grid at present day, or
            ``grid_list_filename`` contains fewer than two grids, or
            not all rows in ``grid_list_filename`` contain a grid filename followed by an age, or
            there are two ages in ``grid_list_filename`` with same age.
        
        Notes
        -----
        Each dynamic topography grid should be in the *mantle* reference frame (not *plate* reference frame) and
        should have global coverage (such that no sample location will return NaN).
        
        Each row in the grid list file should contain two columns. First column containing
        filename (relative to directory of list file) of a dynamic topography grid at a particular time.
        Second column containing associated time (in Ma).

        .. versionadded:: 1.4
        """
        
        self.grids = TimeDependentGrid(grid_list_filename)
    
    @staticmethod
    def create_from_bundled_model(dynamic_topography_model_name):
        """create_from_bundled_model(dynamic_topography_model_name)
        Create a InterpolateDynamicTopography instance from a bundled dynamic topography model name.
        
        Parameters
        ----------
        dynamic_topography_model_name : str
            Name of a bundled dynamic topography model.
            Choices include ``terra``, ``M1``, ``M2``, ``M3``, ``M4``, ``M5``, ``M6``, ``M7``, ``ngrand``, ``s20rts``, ``smean``, ``AY18`` and ``KM16``.
        
        Returns
        -------
        :class:`pybacktrack.InterpolateDynamicTopography`
            The bundled dynamic topography model.
        
        Raises
        ------
        ValueError
            If ``dynamic_topography_model_name`` is not the name of a bundled dynamic topography model.
        
        Notes
        -----
        .. versionadded:: 1.4
        """
        
        if dynamic_topography_model_name not in pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_NAMES:
            raise ValueError("'dynamic_topography_model_name' should be one of {0}.".format(
                ', '.join(pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_NAMES)))
        
        dynamic_topography_model = pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS[dynamic_topography_model_name]
        dynamic_topography_list_filename, _, _ = dynamic_topography_model
        
        return InterpolateDynamicTopography(dynamic_topography_list_filename)
    
    @staticmethod
    def create_from_model_or_bundled_model_name(dynamic_topography_model_or_bundled_model_name):
        """create_from_model_or_bundled_model_name(dynamic_topography_model_or_bundled_model_name)
        Create a InterpolateDynamicTopography instance from a user-provided model or from a bundled model.
        
        Parameters
        ----------
        dynamic_topography_model_or_bundled_model_name : str
            Either the name of a bundled dynamic topography model (see :meth:`pybacktrack.InterpolateDynamicTopography.create_from_bundled_model`), or
            a user-provided model specified as the filename of the grid list file (see parameter of :meth:`pybacktrack.InterpolateDynamicTopography.__init__`).
        
        Raises
        ------
        ValueError
            If ``dynamic_topography_model_or_bundled_model_name`` is not the name of a bundled dynamic topography model or
            the filename of an existing grid list file.
        
        Returns
        -------
        :class:`pybacktrack.InterpolateDynamicTopography`
            The dynamic topography model loaded from a user-provided model or from a bundled model.
        
        Notes
        -----
        .. versionadded:: 1.4
        """
        
        # If a dynamic topography *bundled model name* was specified then create it from a bundled dynamic topography model.
        if dynamic_topography_model_or_bundled_model_name in pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_NAMES:
            dynamic_topography_list_filename, _, _ = pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS[dynamic_topography_model_or_bundled_model_name]
            return InterpolateDynamicTopography(dynamic_topography_list_filename)

        # Else it should refer to an existing grid list file.
        if os.path.isfile(dynamic_topography_model_or_bundled_model_name):
            dynamic_topography_list_filename = dynamic_topography_model_or_bundled_model_name
            return InterpolateDynamicTopography(dynamic_topography_list_filename)
        
        raise ValueError('"{}" is not an internal dynamic topography model name or an existing file (user-provided grid list).'.format(
                dynamic_topography_model_or_bundled_model_name))
    
    def sample(self, time, locations, fallback_to_oldest=True):
        """
        Samples and interpolates the two time-dependent dynamic topography grids surrounding ``time`` at the specified point location(s), but
        optionally falls back to sampling oldest grid (if ``time`` is too old).
        
        Parameters
        ----------
        time : float
            Time to sample dynamic topography.
        locations : sequence of 2-tuple (float, float)
            A sequence of (longitude, latitude) point locations.
        fallback_to_oldest : bool
            Whether to fall back to sampling oldest grid (if ``time`` is too old) rather than
            interpolating the two grids surrounding ``time``.
            Defaults to ``True``.
        
        Returns
        -------
        list of float, or None
            The sampled dynamic topography values (one per location).
            
            When ``time`` is older than the oldest dynamic topography grid:

            - if ``fallback_to_oldest`` is ``True`` then the oldest dynamic topography grid is sampled, or
            - if ``fallback_to_oldest`` is ``False`` then ``None`` is returned.
        
        Notes
        -----
        The point location(s) sample the two grids with ages bounding ``time`` and then interpolate between them.
        
        However if ``time`` is older than the oldest grid then the oldest grid is sampled (if ``fallback_to_oldest`` is ``True``).

        All returned sample values are non-NaN.
        
        .. versionadded:: 1.4
        """
        
        # Search for the two grids bounding 'time'.
        grids_bounding_time = self.grids.get_grids_bounding_time(time)
 
        # If there are no grids bounding 'time'.
        if grids_bounding_time is None:

            # There are no grids bounding 'time', so if we're not falling back to oldest grid then return None.
            if not fallback_to_oldest:
                return None

            # Fall back to the oldest grid that is after/younger than 'time'.
            # Since the grids are sorted in order of increasing age (and they start at present day)
            # we know that a non-negative 'time' will be older than the oldest grid which is the last grid.
            oldest_grid_index = len(self.grids.grid_ages_and_filenames) - 1

            # Sample oldest mantle frame grid.
            grid_sample = self.grids.sample_grid(oldest_grid_index, locations)
        
        else: # There are two grids bounding 'time' ...

            grid_index_younger, grid_index_older = grids_bounding_time

            grid_age_younger, _ = self.grids.grid_ages_and_filenames[grid_index_younger]
            grid_age_older, _ = self.grids.grid_ages_and_filenames[grid_index_older]
            
            # Sample both mantle frame grids (we'll interpolate between them).
            grid_sample_younger = self.grids.sample_grid(grid_index_younger, locations)
            grid_sample_older = self.grids.sample_grid(grid_index_older, locations)
            
            grid_sample = [
                # Linearly interpolate between the older and younger grids.
                # We already know that no two ages are the same (from TimeDependentGrid constructor), so divide-by-zero is not possible.
                ((grid_age_older - time) * grid_sample_younger[point_index] + (time - grid_age_younger) * grid_sample_older[point_index])
                        / (grid_age_older - grid_age_younger)
                for point_index in range(len(locations))
            ]

        return grid_sample


class TimeDependentGrid(object):
    """
    Class to sample the time-dependent grid files.
    """
    
    def __init__(self, grid_list_filename):
        """
        Load grid filenames and associated ages from grid list file 'grid_list_filename' and
        sort in order of increasing age.
        
        Raises ValueError if:
        - list file does not contain a grid at present day, or
        - list file contains fewer than two grids, or
        - not all rows contain a grid filename followed by age, or
        - there are two ages in list file with same age.
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
        
        # Need a present day grid.
        if self.grid_ages_and_filenames[0][0] != 0:
            raise ValueError(u'The grid list file "{0}" does not contain a grid at present day.'.format(grid_list_filename))
    
    def get_grids_bounding_time(self, time):
        """
        Returns the two adjacent grid files (and associated times) that surround 'time' as the 2-tuple (grid_index_younger, grid_index_older).
        
        Returns None if 'time' is outside time range of grids.
        """
        
        # Search for ages neighbouring 'time'.
        first_grid_age, _ = self.grid_ages_and_filenames[0]
        if time < first_grid_age - 1e-6:
            # Time is outside grid age range ('time' is less than first grid age).
            #
            # Note: This shouldn't happen since the first grid should be at present day and
            #       'time' should be non-negative.
            return None
        
        for grid_index in range(1, len(self.grid_ages_and_filenames)):
            grid_age_older, _ = self.grid_ages_and_filenames[grid_index]
            
            if time < grid_age_older + 1e-6:
                return grid_index - 1, grid_index
        
        # Time is outside grid age range ('time' is greater than last grid age).
        return None
    
    def sample_grid(self, grid_index, locations):
        """
        Samples the grid at specified grid index using the specified locations (a sequence of (longitude, latitude) tuples).
        
        Returns a list of sampled values (one per input location).
        
        Raises AssertionError if dynamic topography model does not include the locations.
        This should not happen if the dynamic topography grids have global coverage (ie, have no NaN values).
        The dynamic topography grids should be in the *mantle* reference frame (not *plate* reference frame) and
        therefore should have global coverage (such that no sample location will return NaN).
        """
        
        grid_age, grid_filename = self.grid_ages_and_filenames[grid_index]

        # Create a single multiline string (one line per lon/lat row).
        gmt_location_data = ''.join('{0} {1}\n'.format(longitude, latitude) for longitude, latitude in locations)
        
        #
        # Sample mantle frame grid.
        #

        # The command-line strings to execute GMT 'grdtrack'.
        grdtrack_command_line = ["gmt", "grdtrack", "-Z", "-G{0}".format(grid_filename)]
        
        # Call the system command.
        gmt_output_data = call_system_command(grdtrack_command_line, stdin=gmt_location_data, return_stdout=True)
        
        # Extract the sampled values.
        grid_sample = []
        for line_index, line in enumerate(gmt_output_data.splitlines()):
            # Due to "-Z" option each line returned by GMT grdtrack contains only the sampled value.
            # Note that if GMT returns "NaN" then we'll return float('nan').
            sample_value = float(line)

            # Raise error if grid returns NaN at current location.
            # This shouldn't happen with *mantle* frame grids (typically have global coverage).
            if math.isnan(sample_value):
                longitude, latitude = locations[line_index]
                raise AssertionError(u'Internal error: Dynamic topography grid "{0}" has grid at {1}Ma that does not include location ({2}, {3}).'.format(
                    self.grid_list_filename, grid_age, longitude, latitude))

            grid_sample.append(sample_value)
        
        return grid_sample


# Action to parse dynamic topography model information.
class ArgParseDynamicTopographyAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if len(values) < 3:
            parser.error('Dynamic topography model info must have three or more parameters '
                            '(grid list filename, static polygons filename, rotation filename1 [, rotation filename2 [, ...]]).')
        
        grid_list_filename = values[0]
        static_polygons_filename = values[1]
        rotation_filenames = values[2:]  # Needs to be a list.
        
        setattr(namespace, self.dest, (grid_list_filename, static_polygons_filename, rotation_filenames))


########################
# Command-line parsing #
########################

def main():
    
    __description__ = \
        """Calculate dynamic topography for a present-day location reconstructed through time.
        
        NOTE: Separate the positional and optional arguments with '--' (workaround for bug in argparse module).
        For example...

        python -m pybacktrack.dynamic_topography_cli -ym M7 -p 0 30 -- 10
        """

    # Action to parse a longitude/latitude location.
    class ArgParseLocationAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            # Need two numbers (lon and lat).
            if len(values) != 2:
                parser.error('location must be specified as two numbers (longitude and latitude)')
            
            try:
                # Convert strings to float.
                longitude = float(values[0])
                latitude = float(values[1])
            except ValueError:
                raise argparse.ArgumentTypeError("encountered a longitude or latitude that is not a number")
            
            if longitude < -360 or longitude > 360:
                parser.error('longitude must be in the range [-360, 360]')
            if latitude < -90 or latitude > 90:
                parser.error('latitude must be in the range [-90, 90]')
            
            setattr(namespace, self.dest, (longitude, latitude))
        
    def parse_positive_float(value_string):
        try:
            value = float(value_string)
        except ValueError:
            raise argparse.ArgumentTypeError("%s is not a (floating-point) number" % value_string)
        
        if value <= 0:
            raise argparse.ArgumentTypeError("%g is not a positive (floating-point) number" % value)
        
        return value
        
    def parse_non_negative_float(value_string):
        try:
            value = float(value_string)
        except ValueError:
            raise argparse.ArgumentTypeError("%s is not a (floating-point) number" % value_string)
        
        if value < 0:
            raise argparse.ArgumentTypeError("%g is a negative (floating-point) number" % value)
        
        return value
    
    #
    # Gather command-line options.
    #
    
    # The command-line parser.
    parser = argparse.ArgumentParser(description=__description__, formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument('--version', action='version', version=pybacktrack.version.__version__)
    
    # Specify dynamic topography as a triplet of filenames or a model name (if using bundled data) but not both.
    dynamic_topography_argument_group = parser.add_mutually_exclusive_group(required=True)
    dynamic_topography_argument_group.add_argument(
        '-ym', '--bundle_dynamic_topography_model', type=str,
        metavar='bundle_dynamic_topography_model',
        help='Dynamic topography through time. '
             'Choices include {0}.'.format(', '.join(pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODEL_NAMES)))
    dynamic_topography_argument_group.add_argument(
        '-y', '--dynamic_topography_model', nargs='+', action=ArgParseDynamicTopographyAction,
        metavar='dynamic_topography_filename',
        help='Dynamic topography through time. '
             'First filename contains a list of dynamic topography grids (and associated times). '
             'Note that each grid must be in the mantle reference frame. '
             'Second filename contains static polygons associated with dynamic topography model '
             '(used to assign plate ID to well location so it can be reconstructed). '
             'Third filename (and optional fourth, etc) are the rotation files associated with model '
             '(only the rotation files for static continents/oceans are needed - ie, deformation rotations not needed). '
             'Each row in the grid list file should contain two columns. First column containing '
             'filename (relative to directory of list file) of a dynamic topography grid at a particular time. '
             'Second column containing associated time (in Ma).')
    
    parser.add_argument('-i', '--time_increment', type=parse_positive_float, default=1,
            help='The time increment in My. Value must be positive (and can be non-integral). Defaults to 1 My.')
    
    parser.add_argument(
        '-p', '--point_location', nargs=2, action=ArgParseLocationAction, required=True,
        metavar=('point_longitude', 'point_latitude'),
        help='Optional location of a present-day point to query dynamic topography over time. '
             'Longitude and latitude are in degrees.')

    parser.add_argument('oldest_time', type=parse_non_negative_float,
        metavar='oldest_time',
        help='Output is generated from present day back to the oldest time (in Ma). Value must not be negative.')
    
    # Parse command-line options.
    args = parser.parse_args()
   
    # Create times from present day to the oldest requested time in the requested time increments.
    # Note: Using 1e-6 to ensure the oldest time gets included (if it's an exact multiple of the time increment, which it likely will be).
    time_range = [float(time) for time in np.arange(0, args.oldest_time + 1e-6, args.time_increment)]
    
    # Get dynamic topography model info.
    if args.bundle_dynamic_topography_model is not None:
        try:
            # Convert dynamic topography model name to model info.
            # We don't need to do this (since DynamicTopography.create_from_model_or_bundled_model_name() will do it for us) but it helps check user errors.
            dynamic_topography_model = pybacktrack.bundle_data.BUNDLE_DYNAMIC_TOPOGRAPHY_MODELS[args.bundle_dynamic_topography_model]
        except KeyError:
            raise ValueError("%s is not a valid dynamic topography model name" % args.bundle_dynamic_topography_model)
    else:
        dynamic_topography_model = args.dynamic_topography_model

    point_age = None
    point_longitude, point_latitude = args.point_location
    dynamic_topography_model = DynamicTopography.create_from_model_or_bundled_model_name(dynamic_topography_model, point_longitude, point_latitude, point_age)

    for time in time_range:
        dynamic_topography = dynamic_topography_model.sample(time)
        print('{}: {}'.format(time, dynamic_topography))


if __name__ == '__main__':

    import traceback
    
    def warning_format(message, category, filename, lineno, file=None, line=None):
        # return '{0}:{1}: {1}:{1}\n'.format(filename, lineno, category.__name__, message)
        return '{0}: {1}\n'.format(category.__name__, message)

    # Print the warnings without the filename and line number.
    # Users are not going to want to see that.
    warnings.formatwarning = warning_format
    
    #
    # User should use 'dynamic_topography_cli' module (instead of this module 'dynamic_topography'), when executing as a script, to avoid Python 3 warning:
    #
    #   RuntimeWarning: 'pybacktrack.dynamic_topography' found in sys.modules after import of package 'pybacktrack',
    #                   but prior to execution of 'pybacktrack.dynamic_topography'; this may result in unpredictable behaviour
    #
    # For more details see https://stackoverflow.com/questions/43393764/python-3-6-project-structure-leads-to-runtimewarning
    #
    # Importing this module (eg, 'import pybacktrack.dynamic_topography') is fine though.
    #
    warnings.warn("Use 'python -m pybacktrack.dynamic_topography ...', instead of 'python -m pybacktrack.dynamic_topography ...'.", DeprecationWarning)

    try:
        main()
        sys.exit(0)
    except Exception as exc:
        print('ERROR: {0}'.format(exc), file=sys.stderr)
        # Uncomment this to print traceback to location of raised exception.
        # traceback.print_exc()
        sys.exit(1)

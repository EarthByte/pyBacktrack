
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
import warnings


class DynamicTopography(object):
    """
    Class that reconstructs ocean point location(s) and samples (and interpolates) time-dependent dynamic topography *mantle* frame grid files.
    
    Attributes
    ----------
    longitude : float or list of float
        Longitude of the point location, or list of longitudes (if multiple point locations).
    latitude : float or list of float
        Latitude of the point location, or list of latitudes (if multiple point locations).
    age : float or list of float
        The age of the crust that the point location is on, or list of ages (if multiple point locations).
        
        .. note:: If no age(s) was supplied and the location(s) is on continental crust then the age(s) of the static polygon(s)
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
            If ``longitude`` and ``latitude`` are both not a single value or both not a sequence (of same length).
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
        """
        
        self.grids = TimeDependentGrid(grid_list_filename)
        self.rotation_model = pygplates.RotationModel(rotation_filenames)
        
        # Find the plate ID of the static polygon containing the location (or zero if not in any plates).
        plate_partitioner = pygplates.PlatePartitioner(static_polygon_filename, self.rotation_model)

        # Cache the sample grids on demand with a dictionary mapping each grid index to its sampled grid values.
        self.grid_samples = {}
        
        self.latitude = latitude
        self.longitude = longitude
        self.age = age

        # See if we've been provided a single location or a sequence of locations (by seeing if we can iterate over longitude/latitude or not).
        try:
            iter(longitude)
        except TypeError: # longitude is a single value ...
            # Make sure latitude is also a single value.
            try:
                iter(latitude)
            except TypeError: # latitude is a single value ...
                self.is_sequence_of_locations = False
            else: # latitude is a sequence ...
                raise ValueError('longitude is a single value but latitude is a seqence')
        else: # longitude is a sequence ...
            # Make sure latitude is also a sequence.
            try:
                iter(latitude)
            except TypeError: # latitude is a single value ...
                raise ValueError('longitude is a seqence but latitude is a single value')
            else: # latitude is a sequence ...
                if len(longitude) != len(latitude):
                    raise ValueError('longitude and latitude sequences are not the same length')
                self.is_sequence_of_locations = True

        if self.is_sequence_of_locations:

            self.location = []
            self.reconstruction_plate_id =  []

            if self.age is None:
                self.age = []
                find_age = True
            else:
                find_age = False

            for latitude, longitude in zip(self.latitude, self.longitude):
                location = pygplates.PointOnSphere(latitude, longitude)
                self.location.append(location)

                partitioning_plate = plate_partitioner.partition_point(location)
                if partitioning_plate:
                    reconstruction_plate_id = partitioning_plate.get_feature().get_reconstruction_plate_id()
                else:
                    reconstruction_plate_id = 0
                self.reconstruction_plate_id.append(reconstruction_plate_id)
            
                # Use the age of the containing static polygon if age no provided (eg, outside age grid).
                if find_age:
                    if partitioning_plate:
                        age, _ = partitioning_plate.get_feature().get_valid_time()
                    else:
                        age = 0.0
                    self.age.append(age)
            
            if any(age < 0 for age in self.age):
                raise ValueError('Dynamic topography: age values must not be negative')
            
        else: # A single location...

            self.location = pygplates.PointOnSphere(self.latitude, self.longitude)
            partitioning_plate = plate_partitioner.partition_point(self.location)
            if partitioning_plate:
                self.reconstruction_plate_id = partitioning_plate.get_feature().get_reconstruction_plate_id()
            else:
                self.reconstruction_plate_id = 0
        
            # Use the age of the containing static polygon if age is None (eg, outside age grid).
            if self.age is None:
                if partitioning_plate:
                    self.age, _ = partitioning_plate.get_feature().get_valid_time()
                else:
                    self.age = 0.0
            
            if self.age < 0:
                raise ValueError('Dynamic topography: age values must not be negative')
    
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
        Samples the time-dependent dynamic topography grid files at ``time``, but optionally falls back to a
        non-optimal sampling if necessary (depending on ``time``).
        
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
            When ``fallback`` is ``False`` then ``float('NaN`)`` will be returned for each point location where:
            
            - ``time`` is outside age range of grids, or
            - the age of either (of two) interpolated grids is older than the age of that point location.
        
        Raises
        ------
        AssertionError
            If dynamic topography model does not include the point location(s).
            This should not happen if the dynamic topography grids have global coverage (ie, have no NaN values).
            The dynamic topography grids should be in the *mantle* reference frame (not *plate* reference frame) and
            therefore should have global coverage (such that no sample location will return NaN).
        
        Notes
        -----
        The point location(s) is first reconstructed to the two grid ages bounding ``time`` before sampling
        the two grids (and interpolating between them).
        
        However if ``time`` is outside the age range of grids, or the age of either (of two) interpolated grids
        is older than age(s) of the point location(s), then the oldest grid file that is younger than the
        age-of-appearance of the point location(s) is sampled (if ``fallback`` is ``True``).
        If this happens and we were constructed with a *single* location (not a sequence of locations) then a
        warning is also emitted to notify user (since a single location is likely a well site, as opposed to
        paleo bathymetry gridding which uses a sequence of locations).
        
        .. versionchanged:: 1.2
           Previously this method was called *sample_interpolated* and did not fall back to non-optimal sampling when necessary.
        
        .. versionchanged:: 1.4
           Merged *sample*, *sample_interpolated* and *sample_oldest* methods into one method (this method).
           Added *fallback* parameter (where ``False`` behaves like removed *sample_interpolated* method).
           Added ability to specify a list of point locations (as an alternative to specifying a single location).
        """
        
        # Search for the two grids bounding 'time'.
        grids_bounding_time = self.grids.get_grids_bounding_time(time)
        
        # If there are no grids bounding 'time'.
        if grids_bounding_time is None:
            if self.is_sequence_of_locations:
                sample = [float('nan')] * len(self.location)

                # Optionally fall back to the oldest samples that are after/younger than the appearances of the locations.
                if fallback:
                    for point_index in range(len(self.location)):
                        # Search backwards (from oldest to youngest) until find a younger grid.
                        for grid_index in range(len(self.grids.grid_ages_and_filenames)-1, -1, -1):
                            grid_age, _ = self.grids.grid_ages_and_filenames[grid_index]
                            if grid_age < self.age[point_index] + 1e-6:
                                grid_sample = self._get_grid_sample(grid_index)
                                sample[point_index] = grid_sample[point_index]
                                # Note: We should arrive here for every location since there is always
                                #       a grid at present day and location ages can never be negative.
                                break
                
                return sample
            else:
                # Optionally fall back to the oldest sample that is after/younger the appearance of the location.
                if fallback:
                    # Search backwards (from oldest to youngest) until find a younger grid.
                    for grid_index in range(len(self.grids.grid_ages_and_filenames)-1, -1, -1):
                        grid_age, _ = self.grids.grid_ages_and_filenames[grid_index]
                        if grid_age < self.age + 1e-6:
                            # Warn user that dynamic topography model requires sampling a grid prior (older) than crustal appearance age at location.
                            #
                            # Note: We only warn for the single location case (not for the sequence of locations case above) since that
                            #       typically means a well location where we'd like to inform the user (rather than paleo bathymetry
                            #       gridding where it's expected that this will happen, a lot).
                            warnings.warn(u'Dynamic topography model "{0}" cannot interpolate between two grids at time {1} because grids only go back to time {2}. '
                                          'Using dynamic topography grid at time {3} which is younger than crustal appearance age {4} at well location ({5}, {6}).'.format(
                                            self.grids.grid_list_filename,
                                            time, self.grids.grid_ages_and_filenames[-1][0], grid_age, self.age,
                                            self.longitude, self.latitude))
                            grid_sample = self._get_grid_sample(grid_index)
                            # Note: We should arrive here since there is always a grid at present day
                            #       and location ages can never be negative.
                            return grid_sample
                
                return float('nan')
        
        grid_index_younger, grid_index_older = grids_bounding_time

        grid_age_younger, _ = self.grids.grid_ages_and_filenames[grid_index_younger]
        grid_age_older, _ = self.grids.grid_ages_and_filenames[grid_index_older]
        
        # Sample both grids (we'll attempt to interpolate between them).
        grid_sample_younger = self._get_grid_sample(grid_index_younger)
        grid_sample_older = self._get_grid_sample(grid_index_older)
        
        if self.is_sequence_of_locations:
            sample = [float('nan')] * len(self.location)

            for point_index in range(len(self.location)):
                # If age of sample in older grid is prior/older to appearance of location then optionally
                # fall back to the oldest sample that is after/younger than appearance of location.
                # NaN indicates sample is older than location.
                if math.isnan(grid_sample_older[point_index]):
                    if fallback:
                        # Search backwards (from oldest to youngest) until find a younger grid.
                        for grid_index in range(grid_index_younger, -1, -1):
                            grid_age, _ = self.grids.grid_ages_and_filenames[grid_index]
                            if grid_age < self.age[point_index] + 1e-6:
                                grid_sample = self._get_grid_sample(grid_index)
                                sample[point_index] = grid_sample[point_index]
                                # Note: We should arrive here for every location since there is always
                                #       a grid at present day and location ages can never be negative.
                                break
                    
                    # If we didn't fall back then leave sample value as NaN.
                    continue
                
                # Linearly interpolate between the older and younger grids.
                # We already know that no two ages are the same (from TimeDependentGrid constructor), so divide-by-zero is not possible.
                sample[point_index] = (
                    ((grid_age_older - time) * grid_sample_younger[point_index] +
                     (time - grid_age_younger) * grid_sample_older[point_index])
                        / (grid_age_older - grid_age_younger))

            return sample
        else:
            # If age of sample in older grid is prior/older to appearance of location then optionally
            # fall back to the oldest sample that is after/younger than appearance of location.
            # NaN indicates sample is older than location.
            if math.isnan(grid_sample_older):
                if fallback:
                    # Search backwards (from oldest to youngest) until find a younger grid.
                    for grid_index in range(grid_index_younger, -1, -1):
                        grid_age, _ = self.grids.grid_ages_and_filenames[grid_index]
                        if grid_age < self.age + 1e-6:
                            # Warn user that dynamic topography model requires sampling a grid prior (older) than crustal appearance age at location.
                            #
                            # Note: We only warn for the single location case (not for the sequence of locations case above) since that
                            #       typically means a well location where we'd like to inform the user (rather than paleo bathymetry
                            #       gridding where it's expected that this will happen, a lot).
                            warnings.warn(u'Dynamic topography model "{0}" cannot interpolate between two grids at time {1} because older grid '
                                          'at time {2} is prior (older) to crustal appearance age {3} at well location ({4}, {5}). '
                                          'Using dynamic topography grid at time {6} instead.'.format(
                                            self.grids.grid_list_filename,
                                            time, grid_age_older, self.age,
                                            self.longitude, self.latitude,
                                            grid_age))
                            grid_sample = self._get_grid_sample(grid_index)
                            # Note: We should arrive here since there is always a grid at present day
                            #       and location ages can never be negative.
                            return grid_sample
                
                return float('nan')
            
            # Linearly interpolate between the older and younger grids.
            # We already know that no two ages are the same (from TimeDependentGrid constructor), so divide-by-zero is not possible.
            return (
                ((grid_age_older - time) * grid_sample_younger +
                 (time - grid_age_younger) * grid_sample_older)
                    / (grid_age_older - grid_age_younger))
    
    def _get_grid_sample(self, grid_index):

        # If we have *not* sampled this before then sample it now and cache the results.
        if grid_index not in self.grid_samples:
            self.grid_samples[grid_index] = self._sample_grid(grid_index)

        return self.grid_samples[grid_index]
    
    def _sample_grid(self, grid_index):
        
        grid_age, _ = self.grids.grid_ages_and_filenames[grid_index]

        if self.is_sequence_of_locations:
            grid_sample = [float('nan')] * len(self.location)

            gmt_locations = []
            gmt_location_point_indices = []  # Keep track of where to write GMT sampled locations back to.
            for point_index in range(len(self.location)):
                # Skip locations that appear after the grid age (leave them as NaN to indicate this).
                # This is because we should not reconstruct to times earlier than the location's appearance age.
                if grid_age > self.age[point_index] + 1e-6:
                    continue
                
                # Get rotation from present day to 'grid_age' using the reconstruction plate ID of the location.
                rotation = self.rotation_model.get_rotation(grid_age, self.reconstruction_plate_id[point_index])
                
                # Reconstruct location to 'grid_age'.
                gmt_location = rotation * self.location[point_index]
                gmt_latitude, gmt_longitude = gmt_location.to_lat_lon()

                gmt_locations.append((gmt_longitude, gmt_latitude))
                gmt_location_point_indices.append(point_index)

            # If there are no locations to sample.
            if not gmt_locations:
                return grid_sample  # All NaNs.
            
        else:
            # Skip locations that appear after the grid age (leave them as NaN to indicate this).
            # This is because we should not reconstruct to times earlier than the location's appearance age.
            if grid_age > self.age + 1e-6:
                return float('nan')
            
            # Get rotation from present day to 'grid_age' using the reconstruction plate ID of the location.
            rotation = self.rotation_model.get_rotation(grid_age, self.reconstruction_plate_id)
            
            # Reconstruct location to 'grid_age'.
            gmt_location = rotation * self.location
            gmt_latitude, gmt_longitude = gmt_location.to_lat_lon()

            # List containing the single location.
            gmt_locations = [(gmt_longitude, gmt_latitude)]
        
        # Sample mantle frame grid.
        sample_values = self.grids.sample_grid(grid_index, gmt_locations)
        
        if self.is_sequence_of_locations:
            # Extract the sampled values (and write them back to correct index in returned grid sample).
            for sample_index, sample_value in enumerate(sample_values):
                # The GMT output data should be in the same order as the GMT input data.
                point_index = gmt_location_point_indices[sample_index]
                grid_sample[point_index] = sample_value
            
            return grid_sample
        
        else:
            # Only a single sample value for single location.
            grid_sample = sample_values[0]

            return grid_sample


class InterpolateDynamicTopography(object):
    """
    Class that just samples (and interpolates) time-dependent dynamic topography *mantle* frame grid files.

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
    
    def sample(self, time, longitude, latitude, fallback=True):
        """
        Samples the time-dependent dynamic topography grid files at ``time`` at the specified point location(s), but
        optionally falls back to a non-optimal sampling if necessary (depending on ``time``).
        
        Parameters
        ----------
        time : float
            Time to sample dynamic topography.
        longitude : float or list of float
            Longitude of the point location, or list of longitudes (if multiple point locations).
        latitude : float or list of float
            Latitude of the point location, or list of latitudes (if multiple point locations).
        fallback : bool
            Whether to fall back to a non-optimal sampling if neccessary (see notes below).
            Defaults to ``True``.
        
        Returns
        -------
        float or list of float or None
            The sampled dynamic topography value or list of values.
            If ``longitude`` and ``latitude`` are each a ``float`` value then returns a single value, otherwise
            returns a list of values (one per location).
            
            When ``fallback`` is ``True`` then ``None`` will never be returned (see notes below).
            When ``fallback`` is ``False`` then ``None`` will be returned when ``time`` is outside age range of the grids.
        
        Raises
        ------
        ValueError
            If ``longitude`` and ``latitude`` are both not a single value or both not a sequence (of same length).
        AssertionError
            If dynamic topography model does not include the point location(s).
            This should not happen if the dynamic topography grids have global coverage (ie, have no NaN values).
            The dynamic topography grids should be in the *mantle* reference frame (not *plate* reference frame) and
            therefore should have global coverage (such that no sample location will return NaN).
        
        Notes
        -----
        The point location(s) sample the two grids with ages bounding ``time`` and then interpolate between them.
        
        However if ``time`` is outside the age range of grids then the oldest grid file that is younger than ``time``
        is sampled (if ``fallback`` is ``True``).
        
        .. versionadded:: 1.4
        """

        # See if we've been provided a single location or a sequence of locations (by seeing if we can iterate over longitude/latitude or not).
        try:
            iter(longitude)
        except TypeError: # longitude is a single value ...
            # Make sure latitude is also a single value.
            try:
                iter(latitude)
            except TypeError: # latitude is a single value ...
                is_sequence_of_locations = False
            else: # latitude is a sequence ...
                raise ValueError('longitude is a single value but latitude is a seqence')
        else: # longitude is a sequence ...
            # Make sure latitude is also a sequence.
            try:
                iter(latitude)
            except TypeError: # latitude is a single value ...
                raise ValueError('longitude is a seqence but latitude is a single value')
            else: # latitude is a sequence ...
                if len(longitude) != len(latitude):
                    raise ValueError('longitude and latitude sequences are not the same length')
                is_sequence_of_locations = True
        
        # Search for the two grids bounding 'time'.
        grids_bounding_time = self.grids.get_grids_bounding_time(time)
 
        # If there are no grids bounding 'time' and we're not falling back to oldest grid then return None.
        if grids_bounding_time is None and not fallback:
            return None

        # List of (lon, lat) tuples.
        if is_sequence_of_locations:
            locations = list(zip(longitude, latitude))
        else:
            # List containing a single location.
            locations = [(longitude, latitude)]

        # If there are no grids bounding 'time'.
        if grids_bounding_time is None:
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
            
            grid_sample = []
            for point_index in range(len(locations)):
                # Linearly interpolate between the older and younger grids.
                # We already know that no two ages are the same (from TimeDependentGrid constructor), so divide-by-zero is not possible.
                grid_sample.append(
                    ((grid_age_older - time) * grid_sample_younger[point_index] +
                    (time - grid_age_younger) * grid_sample_older[point_index])
                        / (grid_age_older - grid_age_younger))

        if is_sequence_of_locations:
            # Return a list of sample values.
            return grid_sample
        else:
            # Only a single location, so return a single sampled value (rather than a list containing a single value).
            return grid_sample[0]


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

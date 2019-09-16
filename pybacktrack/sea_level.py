
"""
    Copyright (C) 2017 The University of Sydney, Australia
    
    This program is free software; you can redistribute it and/or modify it under
    the terms of the GNU General Public License, version 2, as published by
    the Free Software Foundation.
    
    This program is distributed in the hope that it will be useful, but WITHOUT
    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
    FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
    for more details.
    
    You should have received a copy of the GNU General Public License along
    with this program; if not, write to Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""


#####################################################################################
# Read sea level file and compute average sea level variations during time periods. #
#                                                                                   #
# This can be used to calculate average variation in sea level (since present day)  #
# of a stratigraphic layer during its interval of deposition.                       #
#####################################################################################


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pybacktrack.bundle_data
import pybacktrack.util.interpolate
import math
import scipy.integrate
import warnings


# Warn the user if the inaccuracy of average sea level exceeds this amount (in metres)...
_MAX_SEA_LEVEL_ERROR = 1


class SeaLevel(object):
    """
    Class to calculate integrated sea levels (relative to present day) over a time period.
    """
    
    def __init__(self, sea_level_filename):
        """
        Load sea level curve (linear segments) from file.
        
        Parameters
        ----------
        sea_level_filename : str
            Text file with first column containing ages (Ma) and a corresponding second column of sea levels (m).
        """
        
        # Read the sea level curve sea_level=function(age) from sea level file.
        self.sea_level_function, self.sea_level_times, _ = pybacktrack.util.interpolate.read_curve_function(sea_level_filename)
    
    @staticmethod
    def create_from_bundled_model(sea_level_model_name):
        """create_from_bundled_model(sea_level_model_name)
        Create a SeaLevel instance from a bundled sea level model name.
        
        Parameters
        ----------
        sea_level_model_name : string
            Name of a bundled sea level model.
            Bundled sea level models include ``Haq87_SealevelCurve`` and ``Haq87_SealevelCurve_Longterm``.
        
        Returns
        -------
        :class:`pybacktrack.SeaLevel`
            The bundled sea level model.
        
        Raises
        ------
        ValueError
            If ``sea_level_model_name`` is not the name of a bundled sea level model.
        """
        
        if sea_level_model_name not in pybacktrack.bundle_data.BUNDLE_SEA_LEVEL_MODEL_NAMES:
            raise ValueError("'sea_level_model_name' should be one of {0}.".format(
                ', '.join(pybacktrack.bundle_data.BUNDLE_SEA_LEVEL_MODEL_NAMES)))
        
        return SeaLevel(pybacktrack.bundle_data.BUNDLE_SEA_LEVEL_MODELS[sea_level_model_name])

    def get_average_level(self, begin_time, end_time):
        """get_average_level(begin_time, end_time)
        Return the average sea level over the specified time period.
        
        Parameters
        ----------
        begin_time : float
            The begin time (in Ma). Should be larger than *end_time*.
        end_time : float
            The end time (in Ma). Should be smaller than *begin_time*.
        
        Returns
        -------
        float
            Average sea level (in metres).
        
        Notes
        -----
        The average sea level is obtained by integrating sea level curve over the specified time period and then dividing by time period.
        """
        
        time_interval = begin_time - end_time
        if time_interval == 0.0:
            return 0.0
        
        # Get the times of the points in the sea level curve that are within the time range.
        # Passing these times to scipy.integrate.quad avoids warnings caused by the non-smooth
        # changes in sea level curve at these points.
        times = [time for time in self.sea_level_times if time <= begin_time and time >= end_time]
        
        # Integrate sea level curve over time interval.
        sea_level_integral, sea_level_integral_error = scipy.integrate.quad(
            self.sea_level_function,
            end_time,
            begin_time,
            points=times,
            limit=2 * len(times))
        
        # Average sea level over integrated interval.
        average_sea_level = sea_level_integral / time_interval
        
        # Warn the user if average sea level is inaccurate.
        average_sea_level_error = sea_level_integral_error / time_interval
        if math.fabs(average_sea_level_error) > _MAX_SEA_LEVEL_ERROR:
            warnings.warn('Unable to accurately integrate sea level curve over time period [{0}, {1}]. '
                          'Average sea level will be inaccurate on the order of {2} metres. '.format(
                              begin_time, end_time, math.fabs(average_sea_level_error)))
        
        return average_sea_level


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


from __future__ import print_function
import interpolate
import math
import scipy.integrate
import sys


# Warn the user if the inaccuracy of average sea level exceeds this amount (in metres)...
MAX_SEA_LEVEL_ERROR = 1


class SeaLevel(object):
    """
    Class to calculate integrated sea levels (relative to present day) over a time period.
    """
    
    def __init__(self, sea_level_filename):
        """
        Load sea level curve (linear segments) from file.
        """
        
        # Read the sea level curve sea_level=function(age) from sea level file.
        self.sea_level_function, self.sea_level_times, _ = interpolate.read_curve_function(sea_level_filename)

    
    def get_average_level(self, begin_time, end_time):
        """
        The average sea level is obtained by integrating sea level curve over the specified time period
        and dividing by time period.
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
                points = times,
                limit = 2 * len(times))
        
        # Average sea level over integrated interval.
        average_sea_level = sea_level_integral / time_interval
        
        # Warn the user if average sea level is inaccurate.
        average_sea_level_error = sea_level_integral_error / time_interval
        if math.fabs(average_sea_level_error) > MAX_SEA_LEVEL_ERROR:
            print('WARNING: Unable to accurately sea level curve over time period [{0}, {1}]. '
                'Average sea level will be inaccurate on the order of {2} metres. '.format(
                    begin_time, end_time, math.fabs(average_sea_level_error)),
                file=sys.stderr)
        
        return average_sea_level


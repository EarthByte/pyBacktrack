
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


############################################################################################
# Continental passive margin initial rifting subsidence and subsequent thermal subsidence.
#
# Rifting is assumed instantaneous in that thermal contraction only happens after rifting has ended.
############################################################################################


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import math
import numpy as np
from scipy.optimize import minimize_scalar
import sys


_y_l = 125000.0   # Initial lithospheric thickness               [m]
_alpha_v = 3.28e-5    # Volumetric coefficient of thermal expansion  [1/K]
_Tm = 1333.0     # Temperature of the mantle                    [C]
_kappa = 1e-6       # Thermal diffusivity                          [m^2/s]

# Densities of mantle, crust and water (in kg/m^3).
_rhoM = 3330.0
_rhoC = 2800.0
_rhoW = 1030.0


def syn_rift_subsidence(
        beta,
        pre_rift_crustal_thickness):
    """
    Initial subsidence (in metres) due to continental stretching.
    
    beta: Stretching factor.
    
    pre_rift_crustal_thickness: Initial crustal thickness prior to rifting (in metres).
    """
    
    # Assuming subsidence filled with water (no sediment).
    # If we were using sediment (plus water) then we'd replace '_rhoW' with the column
    # density of sediment plus water. However we use water only since we can later adjust
    # subsidence with an isostatic sediment contribution.
    tc = pre_rift_crustal_thickness
    return (_y_l * (1 - 1 / beta) *
            ((_rhoM - _rhoC) * (tc / _y_l) * (1 - _alpha_v * _Tm * tc / _y_l) - _alpha_v * _Tm * _rhoM / 2.0) /
            (_rhoM * (1 - _alpha_v * _Tm) - _rhoW))


def post_rift_subsidence(
        beta,
        time):
    """
    Thermal subsidence (in metres) as a function of time.
    
    beta: Stretching factor.
    
    time: Time since end of rifting (in My).
    """
    
    E0 = 4 * _y_l * _rhoM * _alpha_v * _Tm / ((np.pi ** 2) * (_rhoM - _rhoW))
    tau = (_y_l ** 2) / ((np.pi ** 2) * _kappa)
    
    # Time in seconds (from My).
    time_seconds = time * 365 * 24 * 3600 * 1e6
    
    return E0 * (beta / np.pi) * np.sin(np.pi / beta) * (1 - np.exp(-time_seconds / tau))


def total_subsidence(
        beta,
        pre_rift_crustal_thickness,
        time,
        rift_end_time,
        rift_start_time=None):
    """
    Total subsidence  as syn-rift plus post-rift.
    
    beta: Stretching factor.
    
    pre_rift_crustal_thickness: Initial crustal thickness prior to rifting (in metres).
    
    time: Time to calculate subsidence (in My).
    
    rift_end_time: Time at which rifting ended (in My).
    
    rift_start_time: Time at which rifting started (in My).
                     If not specified then assumes initial (non-thermal) subsidence happens
                     instantaneously at 'rift_end_time'.
                     Defaults to None.
    """
    
    if time < rift_end_time:
        # Initial rifting plus subsequent thermal subsidence.
        return syn_rift_subsidence(beta, pre_rift_crustal_thickness) + post_rift_subsidence(beta, rift_end_time - time)
    
    else:  # Time is prior to rift end (so no thermal subsidence)...
        
        # If rift start time is not specified then assume rifting happened instantaneously
        # (from the view of crustal thickness, not thermal subsidence).
        if rift_start_time is None:
            # In this case, since 'time' is prior to rifting (time >= rift_end_time), subsidence has not yet happened.
            return 0.0
        
        if rift_start_time <= rift_end_time:
            raise ValueError('Rift start time must be prior to rift end time.')
        
        # If prior to rifting then subsidence has not yet happened.
        if time >= rift_start_time:
            return 0.0
        
        # The stretching factor (beta) is the total strain.
        # Assuming a constant strain rate G over the rifting period, the total strain (beta) is:
        #
        #   beta = e^(G * rift_period)
        #
        # ...see Jarvis and McKenzie 1980.
        #
        # Re-writing for G we get...
        #
        #   G = ln(beta) / rift_period
        #
        # So for a time in the middle of rifting we need to adjust the time interval of rifting.
        #
        #   beta(t) = e^(G * t)
        #           = e^((ln(beta) / rift_period) * t)
        strain_rate = math.log(beta) / (rift_start_time - rift_end_time)
        partial_rift_beta = math.exp(strain_rate * (rift_start_time - time))
        
        return syn_rift_subsidence(partial_rift_beta, pre_rift_crustal_thickness)


def estimate_beta(
        present_day_subsidence,
        present_day_crustal_thickness,
        rift_end_time):
    """
    Calculate stretching factor (beta) by minimizing difference between actual subsidence and
    subsidence calculated from beta (both at present day).
    
    present_day_subsidence: The (sediment-free) subsidence at present day (in metres).
    
    present_day_crustal_thickness: The crustal thickness at present day (in metres).
    
    rift_end_time: The time that rifting ended (in My).
    """
    
    # Objective function for SciPy minimization.
    def objective_func(beta):
        # Initial (pre-rift) crustal thickness is beta times present day crustal thickness.
        pre_rift_crustal_thickness = beta * present_day_crustal_thickness
        
        # Estimate beta using the subsidence at present day.
        # We want to minimize difference between actual present day subsidence and subsidence calculated using 'beta'.
        return np.abs(present_day_subsidence - total_subsidence(beta, pre_rift_crustal_thickness, 0.0, rift_end_time))
    
    # Need to apply limits on the range of beta values.
    # The objective function we're minimizing can produce positive subsidence values when beta < 1.0 so
    # we don't want those beta values to be found. Similarly for arbitrarily large beta values.
    # The 'test_subsidence_rifting' Python notebook demonstrates this problem.
    # Keeping beta bounded to the range [min_beta, max_beta] solves this problem.
    #
    min_beta = 1.0
    # Initial (pre-rift) crustal thickness should not exceed initial lithospheric thickness
    # (perhaps a more realistic limit would be some percentage of lithospheric thickness?).
    max_beta = _y_l / present_day_crustal_thickness
    
    # Run SciPy minimization.
    #
    # We bound the range of allowed beta values to [min_beta, max_beta].
    #
    # Note: It seems SciPy "minimize_scalar()" works a lot better than "minimize()" in this situation.
    #       Well, for some subsidence/thickness values anyway.
    res = minimize_scalar(
        objective_func,
        bounds=(min_beta, max_beta),
        method='bounded',
        options={'maxiter': 100})
    
    # Return estimated beta and the minimum residual between present day subsidence and
    # subsidence calculated using the estimated beta.
    return res['x'], res['fun']

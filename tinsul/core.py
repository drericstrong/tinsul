# -*- coding: utf-8 -*-
"""
    tinsul.core
    ~~~~~~~~~~
    A module to simulate condition-monitoring data for Transformer INSULation 
    prognostics models.

    :copyright: (c) 2017 by Eric Strong.
    :license: Refer to LICENSE.txt for more information.
"""

import numpy as np
import pandas as pd
from numba import jit
from numpy.random import randn


@jit
# Transformer INSULation SIMulator
def tinsul_sim(temps, start_month=1.0, dp_initial=1000, fail_loc=175.0,
               fail_scale=10.0, o=1.0, t0=35.0, tc=30.0, n=1.0, n0=0.8, nc=1.0,
               l=1.0, a=(3.7*10**7)):
    """
    tinsul_sim is a function to simulate condition-monitoring data for 
    Transformer INSULation prognostics models.
    
    :param temps: 12x3 array, containing monthly low, average, and high temps
            supplying "default" will use the temperatures for DC
    :param start_month: first week of January=1, second week=1.25, etc.
    :param dp_initial: starting degree of polymerization (DP) of the paper
    :param fail_loc: "location" parameter of the logistic failure distribution
    :param fail_scale: "scale" parameter of the logistic failure distribution
    :param o: overload_ratio, typically between 0.75 and 1.1 [Montsinger]
            if a list is supplied, simulation will iterate through the list
            as if it were a repeating pattern
    :param t0: temperature rise of oil over ambient [Montsinger]
    :param tc: temperature rise of the windings over the oil [Montsinger]
    :param n: ratio of copper to iron loss at rated load [Montsinger]
    :param n0: 0.8 for self-cooled transformers, 0.5 water-cooled [Montsinger]
    :param nc: 1.0 for vertical windings, 0.8 for horizontal [Montsinger]
    :param l: if hot spot is constant, l=1.0 [Montsinger]
    :param a: a constant based on the type of paper insulation [Emsley]
    :return: A DataFrame of condition indicators per week: co, co2, furan,
            furfural, and paper water content (in order)
    """
    if type(o) is float:
        o_list = [o]
    else:
        o_list = o
    if temps == "default":
        temps = _use_default_temps()
    # Stores the accumulated condition indicator values in a dict
    acc = {}
    # Variables to store some "state" values per iteration
    cur_month = start_month
    cur_dp = dp_initial
    cur_week = 0
    cur_o = 0
    # dp_failed determines the DP at which the paper insulation will
    # fail, drawn from a logistic distribution centered at 200
    fail_dp = np.random.logistic(loc=fail_loc, scale=fail_scale)
    while cur_week < 5000:  # transformers don't live longer than 5000 weeks
        # Simulate 6 hours at low, 12 hours at avg, and 6 hours at high temps
        # The first index is temp, the second index is hours at that temp
        ambient_low = [temps[int(cur_month)-1][0], 6]
        ambient_avg = [temps[int(cur_month)-1][1], 12]
        ambient_high = [temps[int(cur_month)-1][2], 6]
        # Update DP based on the heat stresses from the core hot spot
        for ambient, time in [ambient_low, ambient_avg, ambient_high]:
            chs = _core_hot_spot(ambient, o_list[cur_o], t0, tc, n, n0, nc, l)
            cur_dp = _calculate_dp(chs, time, cur_dp, a)
        # Calculate the condition indicators based on DP
        acc[cur_week] = _oil_contamination(cur_dp)
        # Check for transformer failure (less than 150 DP is instant failure)
        if (cur_dp <= fail_dp) | (cur_dp < 150):
            break
        # Add the value (Months/Weeks) to get proportion of month per week
        cur_month += 0.230769
        cur_week += 1
        cur_o += 1
        # Rollover to the next year, if necessary
        if cur_month >= 13.0:
            cur_month = 1
        if cur_o > (len(o_list) - 1):
            cur_o = 0
    # Convert the dict to a pandas DataFrame
    df = pd.DataFrame.from_dict(acc, orient='index')
    df.columns = ['CO', 'CO2', 'Furan', 'Furfural', 'Water Content']
    return df


# Uses the monthly temperatures from Washington, DC
def _use_default_temps():
    return [[-2, 1, 6],  # January
            [-1, 3, 8],  # February
            [3, 7, 13],  # March
            [8, 13, 19],  # April
            [14, 18, 24],  # May
            [19, 24, 29],  # June
            [22, 28, 31],  # July
            [21, 27, 30],  # August
            [17, 22, 26],  # September
            [10, 15, 20],  # October
            [5, 10, 14],  # November
            [0, 4, 8]]  # December

@jit
# Calculates the core hot spot temperature of the transformer
def _core_hot_spot(amb, o=1.0, t0=35.0, tc=30.0, n=1.0, n0=0.8, nc=1.0, l=1.0):
    # ---Refer to Montsinger's paper for more information---
    # amb is ambient temperature in Celsius
    # o is overload ratio in decimal form (e.g. 0.75 not 75%)
    # t0 is the temperature rise of oil over ambient
    # tc is the temperature rise of the windings over the oil
    # n = ratio of copper to iron loss at rated load (1 for simplification)
    # n0 = 0.8 for self-cooled transformers, 0.5 for water-cooled
    # nc = 1.0 for vertical windings, 0.8 for horizontal windings
    # l = hot spot is constant, kva varies with the ambient -> l=1.0
    t_chs = t0*((n*o**2+1)**n0) + tc*l*o**(2*nc) + amb
    return t_chs


@jit
def _calculate_dp(core_hot_spot, time, dp_initial, a=(3.7*10**7)):
    # ---Refer to Emsley's paper for more information---
    # core_hot_spot is from the _core_hot_spot function (in Celsius)
    # time is measured in hours
    # dp_initial is the initial degree of polymerization
    # a is a constant based on the type of paper insulation:
    #    -upgraded paper: 3.7*10**7
    #    -dry Kraft paper: 1.1*10**8
    #    -Kraft paper + 1% water: 3.5*10**8
    #    -Kraft paper + 2% water: 7.8*10**8
    #    -Kraft paper + 4% water: 3.5*10**9
    k = a * np.exp(-(117000 / (8.314 * (core_hot_spot + 273.15))))
    dp_final = 1 / ((k * 24 * 7 * time) + (1 / dp_initial))
    return dp_final


@jit
def _oil_contamination(dp):
    # dp is the degree of polymerization
    # ------------------------------------------------------------------------
    # This section contains estimates of dissolved gases and other features
    #  based on regression of empirical data in academic papers
    # ---Refer to Pradhan and Ramu's paper for more information---
    # CO and CO2 are the TOTAL accumulation of the gas, not the rate
    co = (-0.0028*dp + 6.28) + (0.13*randn())
    co2 = (-0.0026*dp + 8.08) + (0.66*randn())
    # ---Refer to "On the Estimation of Elapsed Life" for more information---
    furan = (-0.0038*dp + 7.93) + (0.13*randn())
    # ---Refer to "Study on the Aging Characteristics and Bond-Breaking
    # Process of Oil - Paper Insulation" for more information---
    furfural = (-0.0025*dp + 4.72) + (0.11*randn())
    # ---Refer to Emsley's paper for more information---
    water_content = (0.5 * np.log(1000 / dp)) / (np.log(2)) + (0.03*randn())
    return co, co2, furan, furfural, water_content

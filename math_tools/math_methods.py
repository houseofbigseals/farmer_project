import pandas as pd
from scipy.optimize import curve_fit
import numpy as np
from math_tools.adjustment import Q, FE, F
from math_tools.adjustment import red_far_by_curr, white_far_by_curr
import logging


# here we have to keep all methods to do all needed operations in nsearch methods
# and in all other parts
# but
# there must be only that methods, those parameters not changable by new experimental data
# e g no adjustment coefficients or other rude things

logger = logging.getLogger("Worker.MathMethods")


def differentiate_one_point(
        data: pd.DataFrame,
        mass_of_pipe: float,
        cut_number: int = 100,
        points_low_limit: int = 100
        
):
    # get data from one point in pd.DataFrame format
    # it must have all fields
    # then approximate that curve as exp with scipy

    # make a scipy interpolation here
    dc = 1
    cut_co2 = data['CO2'][cut_number::dc]
    # check if there is to few measure points
    if len(cut_co2) < points_low_limit:
        # TODO: lets do it more beautiful
        logger.error("Error: too few points after cutting, be careful")
        cut_co2 = data['CO2'][int(cut_number/2)::dc]

    # approximation functions
    def func(tt, a, b):
        return a * np.exp(b * tt)

    # def linefunc(tt, a, b):
    #     return a * tt + b

    # we will use approximation on first half of data interval
    # to reduce supposed influence of CO2 concentration at shape of that exp curve
    more_cut_co2 = cut_co2[:int(len(cut_co2) / 2):dc]
    y = np.array(more_cut_co2, dtype=float)
    x = np.arange(0, len(y))
    popt, pcov = curve_fit(func, x, y, p0=(2, -1))  # p0=(2.5, -1.3)
    # TODO: we have to use pcov to know how bad was approximation
    b = popt[1]
    a = popt[0]
    logger.info("half approx a = {}, b = {}".format(a, b))

    # photosynthesis function F = - dCO2 / dt
    def F_func(tt, a, b):
        return -1 * a * b * np.exp(b * tt)

    # point for calculating
    x0 = x[int(len(x) / 8)]

    # calculate mean weight by current period of measure
    current_mean_weight = np.mean(
        data['weight'] - mass_of_pipe
    )

    # get current far
    far = red_far_by_curr(data['Ired'][0]) + white_far_by_curr(data['Iwhite'][0])

    # calculating Q from raw dCO2/dt in point x0
    current_q = Q(F_func(x0, a, b), far, current_mean_weight)
    current_fe = FE(F_func(x0, a, b), far, current_mean_weight)
    current_f = F(F_func(x0, a, b), current_mean_weight)
    logger.info("we got F = {}\n Q = {}\n F/E = {}".format(current_f, current_q, current_fe))

    return current_f, current_q, current_fe


"""

This module contains experimental data coefficients for 
calculating what value of currents (Ired, Iwhite) gives us
required values of (FAR, FR/FW) and vice versa

All here is very unstable and depends on configuration of
experimental device, be careful

"""


def red_far_by_curr(Ir:float):
    # this constants are determined from experiment
    a1 = 2.0877467
    b1 = 3.6243109
    return a1*Ir + b1


def white_far_by_curr(Iw:float):
    # this constants are determined from experiment
    a2 = 2.64379709
    b2 = -0.53008089
    return a2*Iw + b2

def currents_from_newcoords(A: float, B: float):
    """
    :param A: A is FAR = FAR_red + FAR_white in mkmoles
    :param B: B is FAR_red / FAR_white
    return: (I_red, I_white)
    """
    # # this constants are determined from experiment
    # # for far lamp position
    # a1 = 1.77451454
    # b1 = 5.52067992
    # a2 = 2.40069694
    # b2 = 0.24050309

    # this constants are determined from experiment
    # for near lamp position
    # [2.0877467  3.6243109]
    # [2.64379709 - 0.53008089]
    a1 = 2.0877467
    b1 = 3.6243109
    a2 = 2.64379709
    b2 = -0.53008089

    if B != 0:

        # formula was gotten analitically
        Ir = ((A*B)/(B+1) - b1)/a1
        Iw = (A/(B+1) - b2)/a2

        return Ir, Iw

    else:
        Ir = 10 # because our lamp cant do less than 10 mA
        z = 18.5809333333
        Iw = (A - z - b2)/a2

        return Ir, Iw


# functions to calculate different Q for moon from raw -dCO2/dt
def Q(dC, E, weight):
    # convert from ppmv/sec to mg CO2/(m3*sec)
    dCC = 1.8 * dC
    # then calculate Q and divide it to mean weight
    return ((0.28 * dCC + 0.72 * (dCC / E)) / weight)

def FE(dC, E, weight):
    # convert from ppmv/sec to mg CO2/(m3*sec)
    dCC = 1.8 * dC
    # then calculate Q and divide it to mean weight
    return ((dCC / E) / weight)

def F(dC, weight):
    # convert from ppmv/sec to mg CO2/(m3*sec)
    dCC = 1.8 * dC
    # then calculate Q and divide it to mean weight
    return (dCC / weight)
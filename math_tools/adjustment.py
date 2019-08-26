
"""

This module contains experimental data coefficients for 
calculating what value of currents (Ired, Iwhite) gives us
required values of (FAR, FR/FW) and vice versa

All here is very unstable and depends on configuration of
experimental device, be careful

"""

volume = 80  # fitotrone volume in litres
raw_to_dry = 0.08  # conversion factor from raw plants weight to dry weight
ppmv_to_mgCO2 = 1.8  # conversion factor from ppmv CO2 to mgCO2/m3
surface = 0.19  # in m2 - surface of lighted crops
surface_to_volume = 0.45  # in m3/m2
mg_CO2_to_kg_dry_mass = 0.68*0.001*0.001 # in kg of dry mass / mg CO2 assimilated
ppfd_to_kW = 0.2*0.001  # kW / (mkmol/m2*sec)


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

        # check if currents less then 10:
        # TODO check if it really good decision
        if Ir < 10:
            Ir = 10
        if Iw < 10:
            Iw = 10

        return Ir, Iw

    else:
        Ir = 10 # because our lamp cant do less than 10 mA
        z = 18.5809333333
        Iw = (A - z - b2)/a2

        return Ir, Iw


# functions to calculate different Q for moon from raw -dCO2/dt

def Q(dC, E, weight):
    global volume
    global raw_to_dry
    global ppmv_to_mgCO2
    # convert from ppmv/sec to mg CO2/(m3*sec)
    dCC = ppmv_to_mgCO2 * dC
    # then convert from 1m3=1000litres to our volume
    dCC = (volume/1000) * dCC
    # convert weight from raw to dry
    dry_weight = weight*raw_to_dry
    # then calculate Q and divide it to mean weight
    # return ((0.28/1.9) * dCC + (0.72/0.0038) * (dCC / E)) / dry_weight
    return ((0.28 / 1.9) * dCC + (0.72 / 0.0038) * (dCC / E))


def rQ(dC, E, weight):
    global volume
    global raw_to_dry
    global ppmv_to_mgCO2
    # convert from ppmv/sec to mg CO2/(m3*sec)
    dCC = ppmv_to_mgCO2 * dC
    # then convert from 1m3=1000litres to our volume
    dCC = (volume/1000) * dCC
    # convert weight from raw to dry
    # dry_weight = weight*raw_to_dry
    # then calculate Q and divide it to mean weight
    # return ((0.28/1.9) * dCC + (0.72/0.0038) * (dCC / E)) / dry_weight
    return (0.28 / dCC) + (0.72 * (E / dCC))


def FE(dC, E, weight):
    global volume
    global raw_to_dry
    global ppmv_to_mgCO2
    # convert from ppmv/sec to mg CO2/(m3*sec)
    dCC = ppmv_to_mgCO2 * dC
    # then convert from 1m3 to our volume
    dCC = (volume/1000) * dCC
    # convert weight from raw to dry
    dry_weight = weight*raw_to_dry
    # then calculate Q and divide it to mean weight
    # return (dCC / E) / (dry_weight * 0.0038)
    return dCC / E


def F(dC, weight):
    global volume
    global raw_to_dry
    global ppmv_to_mgCO2
    # convert from ppmv/sec to mg CO2/(m3*sec)
    dCC = ppmv_to_mgCO2 * dC
    # then convert from 1m3 to our volume
    dCC = (volume/1000) * dCC
    # convert weight from raw to dry
    dry_weight = weight*raw_to_dry
    # then calculate Q and divide it to mean weight
    # return dCC / dry_weight
    return dCC


def intQ(dC, E, dT):
    # dC - first derivative of co2 concentration in ppnmv/sec
    # E - light intencity im mkmoles/m2*sec
    # dT - time period of measure im sec
    global volume
    global surface
    global ppmv_to_mgCO2
    # convert from ppmv/sec to mg CO2/(m3*sec)
    dCC = ppmv_to_mgCO2 * dC
    # then convert from 1m3 to our volume
    dCC = (volume/1000) * dCC
    V = (0.45 * surface)  # effective volume of crop in m3
    # TODO: we need to change dC to dCC because [dC] in ppmv/sec but [dCC] in  mgCO2/sec
    Prod = 0.000001 * (8.5*0.001*dC*dT)  # productivity of crops in kg/m2
    I = E*0.2*0.001  # light power converted to kW
    Qi = 0.28 * V / Prod + 0.72 * I / Prod
    return Qi


def dry_intQ(dC, E, dT):
    # dC - first derivative of co2 concentration in ppnmv/sec
    # E - light intencity im mkmoles/m2*sec
    # dT - time period of measure im sec
    global volume
    global surface
    global ppmv_to_mgCO2
    global surface_to_volume
    # convert from ppmv/sec to mg CO2/(m3*sec)
    dCC = ppmv_to_mgCO2 * dC
    # then convert from 1m3 to our volume
    dCC = (volume/1000) * dCC
    # now dCC is mgCO2/sec in our volume
    V = (surface_to_volume * surface)  # effective volume of crop in m3
    # TODO: we need to change dC to dCC because [dC] in ppmv/sec but [dCC] in mgCO2/sec
    Prod = mg_CO2_to_kg_dry_mass*dCC*dT  # productivity of crops in kg
    # dT must be in sec
    I = E * ppfd_to_kW  # light power converted to kW
    Qi = 0.28 * V / Prod + 0.72 * I / Prod
    return Qi

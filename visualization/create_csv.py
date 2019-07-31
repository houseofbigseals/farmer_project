import pandas as pd
import numpy as np
import pylab as pl
import mpl_toolkits.mplot3d.axes3d as p3
from matplotlib import cm
from scipy import interpolate
from scipy.optimize import curve_fit
from visualization.csv_read import red_far_by_curr, white_far_by_curr
from math_tools.adjustment import rQ, F, FE


mass_of_pipe = 370  # in grams
# mass of pipe 410 without plants
# part of roots - with
# current experiment
# 31 g - mass of crops at start
# 2.39 g - without water

# last experiment
# 38 g - mass of crops at start

def make_cool_far_rw(far, rw):
    # i know, its dumb
    cfar = 0
    crw = 0
    if far > 600:
        cfar = 700
    elif far > 300:
        cfar = 450
    else:
        cfar = 200

    if rw > 1.25:
        crw = 1.5
    elif rw > 0.7:
        crw = 1
    else:
        crw = 0
    return cfar, crw


def test_parse_csv():

    fieldnames = ["date", "time", "Ired", "Iwhite", "temp", "humid",
                   "CO2", "weight", "airflow", "cycle", "K30CO2"]

    # pd_data = pd.read_csv("data/data.csv", header=None, names=fieldnames)
    # pd_data = pd.read_csv("../data/partly_test_prepared_data_4.csv", header=None, names=fieldnames)
    pd_data = pd.read_csv('../data/another_test_prepared_data_4.csv', header=None, names=fieldnames)
    # pd_data = pd.read_csv('../data/another_test_prepared_data_3.csv', header=None, names=fieldnames)
    print(pd_data.head())
    print(pd_data.tail())

    # convert data to np.array
    tmin = 0
    tmax = len(pd_data['time'])
    dt = 1
    ir = np.array(pd_data['Ired'][tmin:tmax:dt])
    iw = np.array(pd_data['Iwhite'][tmin:tmax:dt])
    co2 = np.array(pd_data['CO2'][tmin:tmax:dt])
    co2K30 = np.array(pd_data['K30CO2'][tmin:tmax:dt])
    air = np.array(pd_data['airflow'][tmin:tmax:dt])
    weight = np.array(pd_data['weight'][tmin:tmax:dt])
    times = pd_data['time'][tmin:tmax:dt]
    dates = pd_data['date'][tmin:tmax:dt]
    cycle = np.array(pd_data['cycle'][tmin:tmax:dt])

    fr_fw = np.zeros(len(times))
    far = np.zeros(len(times))

    # creating new coordinates
    for i in range(len(far)):
        fr_fw[i] = red_far_by_curr(ir[i])/white_far_by_curr(iw[i])
        far[i] = red_far_by_curr(ir[i]) + white_far_by_curr(iw[i])

    # creating new array of parts of data in which no airflow

    # new_data = np.array([
    #     [np.array([0, 1]), 1, 2, 3, 4, 5, [0, 0]],
    #     [np.array([0, 1]), 0, 0, 0, 0, 0, [0, 0]]
    #     ]
    # )
    # final data [far, rw, dco2/dt, Q, F/E, num_in_cycle, cycle]
    final_data = np.array([
        [1, 2, 3, 4, 5, 6, 7],
        [0, 0, 0, 0, 0, 0, 0]
        ]
    )
    #
    # print("shape of weight ", np.shape(weight[0]))
    # print(np.mean(weight[0:10000]))
    # current_air = air[0]
    start_pointer = -1
    stop_pointer = -1
    incycle_counter = 0
    cur_cycle = 0
    old_cycle = 0
    # debugs is array that contains pairs (cycle_num, number_points_in_cycle)
    # to find short cycles
    debugs = []
    # parse data in cycle
    for i in range(1, len(times)):
        if air[i] != air[i-1]:
            # it shows that airflow mode was changed
            if air[i] == 0:
                # it means that there is start of new measure epoch
                start_pointer = i
            if air[i] == 1:

                # it means that there is end of measure epoch

                stop_pointer = i-1
                if start_pointer != -1:

                    info_str = str(cycle[stop_pointer - 10]) + " " + \
                               str(dates[stop_pointer - 10]) + " " + \
                                str(times[stop_pointer - 10])
                    print("\n" + info_str)
                    print(start_pointer, stop_pointer)
                    print("far = {}, fr_fw = {}".format(
                        far[stop_pointer - 10], fr_fw[stop_pointer - 10])
                    )
                    co2_part = co2[start_pointer: stop_pointer]

                    # make a scipy interpolation here
                    dc = 1
                    number_of_cut = 100  # for first time
                    cut_co2 = co2_part[number_of_cut::dc]
                    print(len(cut_co2))
                    if(len(cut_co2)<100):
                        print("Error: too few points after cutting 100, be careful")
                        cut_co2 = co2_part[number_of_cut-100::dc]
                        print("new cut part len is: {}".format(len(cut_co2)))
                    # approximation

                    def func(tt, a, b):
                        return a * np.exp(b * tt)

                    def linefunc(tt, a, b):
                        return a * tt + b

                    # at half interval
                    cut2_co2 = cut_co2[:int(len(cut_co2) / 2):dc]
                    y = np.array(cut2_co2, dtype=float)
                    x = np.arange(0, len(y))
                    popt, pcov = curve_fit(func, x, y, p0=(2, -1))  # p0=(2.5, -1.3)
                    b3 = popt[1]
                    a3 = popt[0]
                    print("half approx a = {}, b = {}".format(popt[0],popt[1]))
                    # recalculate (a0, b0) to photosyntethys
                    # F = - dCO2 / dt

                    def Ffunc(tt, a, b):
                        return -1* a * b * np.exp(b * tt)
                        # return a * b * np.exp(b * tt)

                    # point for calculating
                    x0 = x[int(len(x)/8)]
                    # print("current CO2 {}".format(cut_co2[x0]))

                    # Fdata = Ffunc(x0, a0, b0)

                    # new_data = np.append(
                    #     new_data,
                    #     [[co2_part, far[stop_pointer - 2], fr_fw[stop_pointer - 2],
                    #       Fdata, cycle[stop_pointer - 2], info_str, [a0, b0]]],
                    #     axis=0
                    # )

                    # new_data = np.append(
                    #     new_data,
                    #     [[co2_part, far[stop_pointer - 2], fr_fw[stop_pointer - 2],
                    #       -1*Fdata, cycle[stop_pointer - 2], info_str, [a0, b0]]],
                    #     axis=0
                    # )

                    # it is hotfix for bug in data numerating
                    # TODO : remove after fixing that bug in worker
                    # if incycle_counter < 17:
                    #     incycle_counter += 1
                    #     cur_cycle = cycle[stop_pointer - 10]
                    #     print("cycle {} number {}".format(cur_cycle, incycle_counter))
                    # elif incycle_counter == 17:
                    #     incycle_counter = 0
                    #     cur_cycle = cycle[stop_pointer - 10] -1
                    #     print("cycle {} number {}".format(cur_cycle, incycle_counter))

                    # it is hotfix for bug in data numerating
                    # TODO : remove after fixing that bug in worker
                    incycle_counter = incycle_counter + 1
                    cur_cycle = cycle[stop_pointer - 10]
                    cdata = cycle[stop_pointer - 10]

                    # recalculate far and rw to its real meanings
                    cool_far, cool_rw = make_cool_far_rw(far[stop_pointer - 10], fr_fw[stop_pointer - 10])
                    # calculate mean weight by current period of measure
                    current_mean_weight = np.mean(
                        weight[start_pointer: stop_pointer] - mass_of_pipe
                    )
                    print("current mean weight {}".format(current_mean_weight))

                    # # functions to calculate different Q for moon from raw dCO2/dt
                    # def q(dC, E, weight):
                    #     # convert from ppmv to mg CO2/ m3
                    #     dCC = 1.8 * dC
                    #     # then calculate Q and divide it to mean weight
                    #     return ((0.28 * dCC + 0.72 * (dCC/E))/weight)*1000
                    #
                    # def fe(dC, E, weight):
                    #     # convert from ppmv to mg CO2/ m3
                    #     dCC = 1.8 * dC
                    #     # then calculate Q and divide it to mean weight
                    #     return ((dCC/E)/weight)*1000
                    #
                    # def f(dC, weight):
                    #     # convert from ppmv to mg CO2/ m3
                    #     dCC = 1.8 * dC
                    #     # then calculate Q and divide it to mean weight
                    #     return (dCC/weight)*1000

                    current_q = rQ(Ffunc(x0, a3, b3), cool_far, current_mean_weight)
                    current_fe = FE(Ffunc(x0, a3, b3), cool_far, current_mean_weight)
                    current_f = F(Ffunc(x0, a3, b3), current_mean_weight)
                    print("rQ = {}, F = {}, F/E = {}".format(current_q, current_f, current_fe))

                    if cur_cycle > old_cycle:
                        debugs.append((old_cycle, incycle_counter))
                        cdata = old_cycle
                        print("cycle {} number {}".format(cdata, incycle_counter))
                        old_cycle = cycle[stop_pointer - 10]

                        final_data = np.append(
                            final_data,
                            [[cool_far, cool_rw,
                              current_f*1000, current_q, current_fe*1000, incycle_counter, cdata]],
                            axis=0
                        )
                        incycle_counter = 0

                    else:
                        final_data = np.append(
                            final_data,
                            [[cool_far, cool_rw,
                              current_f*1000, current_q, current_fe*1000, incycle_counter, cdata]],
                            axis=0
                        )

                        print("cycle {} number {}".format(cdata, incycle_counter))

                    info_str = str(cdata) + " " + \
                               str(dates[stop_pointer - 10]) + " " + \
                                str(times[stop_pointer - 10])

                    # new_data = np.append(
                    #     new_data,
                    #     [[co2_part, far[stop_pointer - 10], fr_fw[stop_pointer - 10],
                    #       float(-1*a3), cdata, info_str, [a3, b3]]],
                    #     axis=0
                    # )



                    # new_data = np.append(
                    #     new_data,
                    #     [[co2_part, far[stop_pointer - 10], fr_fw[stop_pointer - 10],
                    #       Ffunc(x0, a3, b3), cdata, info_str, [a3, b3]]],
                    #     axis=0
                    # )


    print(debugs)
    # remove first two rows - they are not necessary anymore
    final_data = np.delete(
        final_data,
        slice(0,2),
        axis=0
    )
    print(np.shape(final_data))
    print(np.shape(final_data[0]))
    print(final_data)
    datafile = "last_data_check.csv"
    # now print it to new csv file
    old_pd = pd.DataFrame(final_data)
    # new_pd.columns = ['FAR', 'red/white', 'F', 'Q', 'F/E', 'point_number', 'cycle_number']
    old_pd.columns = ['x1', 'x2', 'y1', 'y2', 'y3', 'point_number', 'cycle_number']
    new_pd = old_pd.loc[:, ['x1', 'x2', 'y1', 'y3', 'point_number', 'cycle_number']]
    # new_pd = old_pd
    new_pd.columns = ['x1', 'x2', 'yF', 'yFE', 'point_number', 'cycle_number']

    # gapminder_years = gapminder[gapminder.year.isin(years)]
    # useful_rows = [1, 3, 6, 8, 11, 12, 14, 16, 17, 19]
    # filtered_pd = new_pd[new_pd['cycle_number'].isin(useful_rows)]
    filtered_pd = new_pd

    filtered_pd.to_csv(datafile, index=False, float_format='%g')

    # for i in range(0, len(new_data)):
    #     with open(datafile, "a", newline='') as out_file:
    #         writer = csv.DictWriter(out_file, delimiter=',', fieldnames=fieldnames)
    #         writer.writerow(new_data[i])

if __name__ == "__main__":
    test_parse_csv()

# module that provides all necessary for parse raw csv co2 data
# and find dC/dt
# also method for show 3d surfaces of dc/dt as f( FAR, FR/FW )

import pandas as pd
import numpy as np
import pylab as pl
import mpl_toolkits.mplot3d.axes3d as p3
from matplotlib import cm
from scipy import interpolate
from scipy.optimize import curve_fit
from tools.visualization.csv_read import red_far_by_curr, white_far_by_curr

mass_of_pipe = 421  # in grams

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

    new_data = np.array([
        [np.array([0, 1]), 1, 2, 3, 4, 5, [0, 0]],
        [np.array([0, 1]), 0, 0, 0, 0, 0, [0, 0]]
        ]
    )
    print("shape of new data ", np.shape(new_data))
    # current_air = air[0]
    start_pointer = -1
    stop_pointer = -1
    incycle_counter = 0
    cur_cycle = 0
    old_cycle = 0
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
                        print("Error: too few points after cutting 200, be careful")
                        cut_co2 = co2_part[number_of_cut-100::dc]
                        print("new cut part len is: {}".format(len(cut_co2)))
                    # approximation

                    def func(tt, a, b):
                        return a * np.exp(b * tt)

                    def linefunc(tt, a, b):
                        return a * tt + b

                    # at full interval
                    y = np.array(cut_co2, dtype=float)
                    x = np.arange(0, len(y))
                    popt, pcov = curve_fit(func, x, y, p0=(2, -1))  # p0=(2.5, -1.3)
                    b3 = popt[1]
                    a3 = popt[0]
                    print("full approx a = {}, b = {}".format(popt[0],popt[1]))


                    # linear at first third of interval
                    # try:
                    #     cut2_co2 = cut_co2[:int(len(cut_co2) / 4):dc]
                    #     y = np.array(cut2_co2, dtype=float)
                    #     x = np.arange(0, len(y))
                    #     popt, pcov = curve_fit(linefunc, x, y, p0=(-2, 100))  # p0=(2.5, -1.3)
                    #     b3 = popt[1]
                    #     a3 = popt[0]
                    #     print("first third linear approx a = {}, b = {}".format(popt[0], popt[1]))
                    # except Exception as e:
                    #     b3 = 0
                    #     a3 = 0
                    #     print("We got error {}".format(e))
                    #     print("The data will be a= {}, b = {}".format(0, 0))
                    #     print("Remember, thats not real data")

                    # # rude linear at first third of interval
                    # cut2_co2 = cut_co2[:int(len(cut_co2) / 4):dc]
                    # y = np.array(cut2_co2, dtype=float)
                    # x = np.arange(0, len(y))
                    # dx = len(y)
                    # dy = - y[0] + y[len(y)-1]
                    # # popt, pcov = curve_fit(linefunc, x, y, p0=(-2, 100))  # p0=(2.5, -1.3)
                    # b3 = -1000 # aaaaaaaaaaaaaa
                    # a3 = float((dy/dx))
                    # print("rude linear approx a = {}".format(a3))
                    # print("far = {}, fr/fw = {}".format(far[stop_pointer - 10],
                    #                                     fr_fw[stop_pointer - 10]))

                    # def func(tt, a, b, c):
                    #     return a * np.exp(b * tt) + c
                    #
                    # # at full interval
                    # y = np.array(cut_co2, dtype=float)
                    # x = np.arange(0, len(y))
                    # try:
                    #     popt, pcov = curve_fit(func, x, y, p0=(2, -1, 100))  # p0=(2.5, -1.3)
                    #     b0 = popt[1]
                    #     a0 = popt[0]
                    #     c0 = popt[2]
                    #     print("full approx a = {}, b = {} c = {}".format(popt[0],popt[1], popt[2]))
                    # except Exception as e:
                    #     print(e)
                    #     a0, b0, c0 = (0, 0, 0)

                    # # at first half of interval
                    # cut2_co2 = cut_co2[:int(len(cut_co2)/2):dc]
                    # y = np.array(cut_co2, dtype=float)
                    # x = np.arange(0, len(y))
                    # popt, pcov = curve_fit(func, x, y, p0=(2, -1))  # p0=(2.5, -1.3)
                    # b1 = popt[1]
                    # print("first half approx a = {}, b = {}".format(popt[0],popt[1]))
                    #
                    # # at second half of interval
                    # cut2_co2 = cut_co2[int(len(cut_co2) / 2)::dc]
                    # y = np.array(cut2_co2, dtype=float)
                    # x = np.arange(0, len(y))
                    # popt, pcov = curve_fit(func, x, y, p0=(2, -1))  # p0=(2.5, -1.3)
                    # b2 = popt[1]
                    # print("second half approx a = {}, b = {}".format(popt[0], popt[1]))
                    #
                    # # at first third of interval
                    # cut2_co2 = cut_co2[:int(len(cut_co2) / 3):dc]
                    # y = np.array(cut2_co2, dtype=float)
                    # x = np.arange(0, len(y))
                    # popt, pcov = curve_fit(func, x, y, p0=(2, -1))  # p0=(2.5, -1.3)
                    # b3 = popt[1]
                    # print("first third approx a = {}, b = {}".format(popt[0], popt[1]))
                    #
                    # # at second third of interval
                    # cut2_co2 = cut_co2[int(len(cut_co2) / 3):int(len(cut_co2)*2 / 3):dc]
                    # y = np.array(cut2_co2, dtype=float)
                    # x = np.arange(0, len(y))
                    # popt, pcov = curve_fit(func, x, y, p0=(2, -1))  # p0=(2.5, -1.3)
                    # b4 = popt[1]
                    # print("second third approx a = {}, b = {}".format(popt[0], popt[1]))
                    #
                    # # at third third of interval
                    # cut2_co2 = cut_co2[int(len(cut_co2)*2 / 3)::dc]
                    # y = np.array(cut2_co2, dtype=float)
                    # x = np.arange(0, len(y))
                    # popt, pcov = curve_fit(func, x, y, p0=(2, -1))  # p0=(2.5, -1.3)
                    # b5 = popt[1]
                    # print("third third approx a = {}, b = {}".format(popt[0], popt[1]))

                    # save results to new array
                    # new_data = np.append(
                    #     new_data,
                    #     [[co2_part, far[stop_pointer - 2], fr_fw[stop_pointer - 2],
                    #      np.mean([b0, b1, b2, b3, b4, b5]), cycle[stop_pointer - 2], info_str]],
                    #     axis=0
                    # )

                    # recalculate (a0, b0) to photosyntethys
                    # F = - dCO2 / dt

                    def Ffunc(tt, a, b):
                        return -1* a * b * np.exp(b * tt)
                        # return a * b * np.exp(b * tt)

                    # point for calculating
                    x0 = x[int(len(x)/8)]
                    print("current CO2 {}".format(cut_co2[x0]))

                    # function to calculate Q for moon from dCO2/dt
                    def q(dC, E, weight):
                        # convert from ppmv to mg CO2/ m3
                        dCC = 1.8 * dC
                        # then calculate Q and divide it to mean weight
                        return (0.28 * dCC + 0.72 * (dCC / E)) / weight

                    def fe(dC, E, weight):
                        # convert from ppmv to mg CO2/ m3
                        dCC = 1.8 * dC
                        # then calculate Q and divide it to mean weight
                        return (dCC / E) / weight

                    def f(dC, weight):
                        # convert from ppmv to mg CO2/ m3
                        dCC = 1.8 * dC
                        # then calculate Q and divide it to mean weight
                        return dCC / weight

                    # current_q = q(Ffunc(x0, a3, b3), cool_far, current_mean_weight)
                    # current_fe = fe(Ffunc(x0, a3, b3), cool_far, current_mean_weight)
                    # current_f = f(Ffunc(x0, a3, b3), current_mean_weight)
                    # print("Q = {}, F = {}".format(current_q, Ffunc(x0, a3, b3)))

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

                    incycle_counter = incycle_counter + 1
                    cur_cycle = cycle[stop_pointer - 10]


                    cdata = cycle[stop_pointer - 10]

                    if cur_cycle > old_cycle:
                        debugs.append((old_cycle, incycle_counter))
                        cdata = old_cycle
                        print("cycle {} number {}".format(cdata, incycle_counter))
                        old_cycle = cycle[stop_pointer - 10]
                        incycle_counter = 0
                    else:
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
                    new_data = np.append(
                        new_data,
                        [[co2_part, far[stop_pointer - 10], fr_fw[stop_pointer - 10],
                          Ffunc(x0, a3, b3), cdata, info_str, [a3, b3]]],
                        axis=0
                    )


    print(debugs)
    # remove first two rows - they are not necessary anymore
    new_data = np.delete(
        new_data,
        slice(0,2),
        axis=0
    )

    # # lets see what we got
    # # 2D plot
    # fig = pl.figure()
    # t = range(len(new_data))
    # # pl.xticks(t, times, rotation='vertical')
    # pl.plot(t, new_data[::, 3]*(-1000), '-og', label="dCO2/dt, coeff b")
    # pl.plot(t, new_data[::, 2], '-ob', label="FARred/FARwhite")
    # pl.plot(t, new_data[::, 1]/100, '-or', label="FAR summ, mkmoles")
    # pl.plot(t, new_data[::, 4], '-k', label="Cycle")
    # # pl.plot(t,  air*400, '-k', label="Airflow ON")
    # # pl.plot(t, co2K30, '-c', label="CO2 outside")
    # # pl.ylabel('CO2, ppm')
    # pl.xlabel('time, dt = 30 min')
    # # pl.title('fit: a={:.4f}, b={:.6f}'.format(popt[0], popt[1]))
    # pl.legend()
    # pl.grid()
    # pl.show()

    # then lets create a test 3d graph
    # schedule table, on which the experiments were made
    # sched = [
    # 0    [10, 284],  # 700, 0
    # 1    [10, 75],  # 200, 0
    # 2    [10, 179],  # 450, 0
    # 3    [194, 146],  # 700, 1
    # 4    [53, 42],  # 200, 1
    # 5    [124, 94],  # 450, 1
    # 6    [234, 117],  # 700, 1.5
    # 7    [65, 33],  # 200, 1.5
    # 8    [149, 75],  # 450, 1.5
    # 9    [194, 146],  # 700, 1  ------------------- repeating
    # 10    [124, 94],  # 450, 1
    # 11    [53, 42],  # 200, 1
    # 12    [149, 75],  # 450, 1.5
    # 13    [234, 117],  # 700, 1.5
    # 14    [65, 33],  # 200, 1.5
    # 15    [10, 284],  # 700, 0
    # 16    [10, 179],  # 450, 0
    # 17    [10, 75]  # 200, 0
    # ]


    # we have to reshape data and summ all repetions to interpolate

    final_data = np.array([
        [np.zeros(9), np.zeros(9), np.zeros(9), 1, [0, 0]],
        [np.zeros(9), np.zeros(9), np.zeros(9), 1, [0, 0]]
        ]
    )

    interval = 18

    maxes = np.array(
        [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0]
        ]
    )

    for i in range(0, len(new_data)):
        if new_data[i, 4] > new_data[i-1, 4]:
            print(i)
            print(new_data[i, 5])
            print("cycle is : ", new_data[i, 4])
            # it means that there is star of new cycle
            fut_arr = new_data[i:i+interval, 3]
            far_arr = new_data[i:i+interval, 1]
            frfw_arr = new_data[i:i+interval, 2]
            if i + interval < len(new_data) and new_data[i+interval - 1, 4] == new_data[i, 4]:

                print(i)
                print(new_data[i, 5])
                d = new_data[i, 5]
                # reshape it and summ all repetions
                # make it acceptable for scipy.interpolate
                # far = np.array([200, 450, 700, 200, 450, 700, 200, 450, 700])
                far = np.array([700, 200, 450, 700, 200, 450, 700, 200, 450])
                rw = np.array([0, 0, 0, 1, 1, 1, 1.5, 1.5, 1.5])
                dco2 = np.zeros(9, dtype=float)
                QQ = np.zeros(9, dtype=float)
                # lets sum repetions
                dco2[0] = float((fut_arr[17] + fut_arr[1]) / 2)
                dco2[1] = float((fut_arr[16] + fut_arr[2]) / 2)
                dco2[2] = float((fut_arr[15] + fut_arr[0]) / 2)
                dco2[3] = float((fut_arr[11] + fut_arr[4]) / 2)
                dco2[4] = float((fut_arr[10] + fut_arr[5]) / 2)
                dco2[5] = float((fut_arr[9] + fut_arr[3]) / 2)
                dco2[6] = float((fut_arr[14] + fut_arr[7]) / 2)
                dco2[7] = float((fut_arr[12] + fut_arr[8]) / 2)
                dco2[8] = float((fut_arr[13] + fut_arr[6]) / 2)

                # farrrr = new_data[i, 1]
                # print("farrrr is ", farrrr)

                def qfunc2(F, E):
                    return 0.28*F + 0.72*(F/E)

                def qfunc(F, E):
                    return (F/E)

                # # another type of plot
                for i in range(0, len(dco2)):
                    QQ[i] = qfunc2(dco2[i], far_arr[i])
                    print('dco2 = {}, QQ = {}, far = {}, frfw = {}'.format(
                        dco2[i], QQ[i], far_arr[i], frfw_arr[i]
                    ))

                # QQ[0] = float(qfunc(dco2[0], far_arr[1]))
                # QQ[1] = float(qfunc(dco2[1], far_arr[2]))
                # QQ[2] = float(qfunc(dco2[2], far_arr[0]))
                # QQ[3] = float(qfunc(dco2[3], far_arr[4]))
                # QQ[4] = float(qfunc(dco2[4], far_arr[5]))
                # QQ[5] = float(qfunc(dco2[5], far_arr[3]))
                # QQ[6] = float(qfunc(dco2[6], far_arr[7]))
                # QQ[7] = float(qfunc(dco2[7], far_arr[8]))
                # QQ[8] = float(qfunc(dco2[8], far_arr[6]))
                # QQ[0] = float(qfunc(dco2[0], far_arr[1]))
                # QQ[1] = float(qfunc(dco2[1], far_arr[2]))
                # QQ[2] = float(qfunc(dco2[2], far_arr[0]))
                # QQ[3] = float(qfunc(dco2[3], far_arr[4]))
                # QQ[4] = float(qfunc(dco2[4], far_arr[5]))
                # QQ[5] = float(qfunc(dco2[5], far_arr[3]))
                # QQ[6] = float(qfunc(dco2[6], far_arr[7]))
                # QQ[7] = float(qfunc(dco2[7], far_arr[8]))
                # QQ[8] = float(qfunc(dco2[8], far_arr[6]))

                mco2 = float(np.max(dco2))
                mrw = float(rw[np.argmax(dco2)])
                mfar = float(far[np.argmax(dco2)])

                mQQ = float(np.max(QQ))
                mQQrw = float(rw[np.argmax(QQ)])
                mQQfar = float(far[np.argmax(QQ)])

                # maxes = np.append(
                #     maxes,
                #     [np.array([mco2, mfar, mrw, new_data[i, 4], d.split(' ')[1]])],
                #     axis=0
                # )
                maxes = np.append(
                    maxes,
                    [np.array([mQQ, mQQfar, mQQrw, new_data[i, 4], d.split(' ')[1]])],
                    axis=0
                )

                for i in range(0, 9):
                    print("dco2/dt = {}, far = {}, fr/fw = {}".format(
                        dco2[i], far[i], rw[i]
                    ))
                for i in range(0, 9):
                    print("Q = {}, far = {}, fr/fw = {}".format(
                        QQ[i], far[i], rw[i]
                    ))
                # add it to final array
                # final_data = np.append(final_data, [[-100000*dco2, far, rw, new_data[i, 5]]], axis=0)
                final_data = np.append(final_data, [[QQ, far, rw, d,
                                                     new_data[i*interval - 2, 6]]], axis=0)

    # remove first two rows - they are not necessary anymore
    print(len(final_data))
    final_data = np.delete(
        final_data,
        slice(0, 2),
        axis=0
    )
    print(len(final_data))

    maxes = np.delete(
        maxes,
        slice(0,2),
        axis=0
    )

    print(np.shape(maxes))
    print(maxes)

    # lets visualize behavior of photosynthesys maximum points
    # at first - plot maximum by time

    # 2D plots
    fig, axs = pl.subplots(3, 1)
    t = range(len(maxes))
    fig.suptitle('-1*dCO2/dt maximum by time', fontsize=14)

    # first subplot
    axs[0].plot(t, maxes[::, 0], '-og')
    # axs[0].set_xlabel('time, cycles (cycle = about 9 hours)')
    axs[0].set_ylabel("-1*dCO2/dt, ppm/sec")
    # axs[0].set_title("-1*dCO2/dt maximum by time")
    axs[0].grid()

    # second subplot
    axs[1].plot(t, maxes[::, 1], '-vr')
    # axs[1].set_xlabel('time, cycles (cycle = about 9 hours)')
    axs[1].set_ylabel("far, ppf")
    axs[1].grid()
    axs[1].set_ylim(200, 750)

    # for i in range(len(maxes)):
    #     # ax.annotate(str(maxes[i, 1])+","+str(maxes[i, 2]), (t[i], maxes[i, 0]))
    #     axs[1].text(t[i], maxes[i, 1], str(maxes[i, 4]))
    # ax.set_xlim(0, len(t))
    # ax.set_ylim(0, 1.5)
    # ax.set_zlim(5, 700)
    # axs[1].set_title("far coordinates of maximum by time")

    # third subplot
    axs[2].plot(t, maxes[::, 2], '-vb')
    axs[2].set_xlabel('time, cycles (cycle = about 9 hours)')
    axs[2].set_ylabel("fr/fw")
    axs[2].grid()
    # axs[2].set_title("fr/fw coordinates of maximum by time")
    pl.xticks(t, maxes[::, 4], rotation='vertical')
    # pl.grid()
    pl.show()

    # 2D plot
    fig = pl.figure()
    t = range(len(maxes))
    print(len(t))
    print(len(maxes[::, 4]))
    print(len(maxes[::, 0]))
    pl.xticks(t, maxes[::, 4], rotation='vertical')
    pl.plot(t, maxes[::, 0], '-og', label="maximum of -1*dCO2/dt , ppm by sec")
    # pl.plot(t, fr_fw*200, '-b', label="FARred/FARwhite")
    # pl.plot(t, far, '-r', label="FAR summ, mkmoles")
    # pl.plot(t,  air*400, '-k', label="Airflow ON")
    # pl.plot(t, co2K30, '-c', label="CO2 outside")
    # pl.plot(t, weight, '-y', label="Raw weight, g")
    # pl.ylabel('CO2, ppm')
    pl.xlabel('time, cycles (cycle = about 9 hours)')
    pl.ylabel("maximum of -1*dCO2/dt , ppm by sec")
    pl.title("-1*dCO2/dt maximum by time")

    for i in range(len(maxes)):
        pl.annotate(str(maxes[i, 1])+","+str(maxes[i, 2]), (t[i], maxes[i, 0]))

    pl.legend()
    pl.grid()
    pl.show()

    # next lets show the trajectory of maximum od -dco2/dt in (far, fr/fw) coordinates
    # and with it lets draw the first surface - in day 1 - for for comparison

    f = interpolate.interp2d([200, 450, 700], [0, 1, 1.5],
                             np.reshape(final_data[1, 0], (3, 3)), kind='linear')
    # far = np.arange(200, 800, 10)
    # fw = np.arange(0, 2, 0.05)
    far = np.arange(200, 700, 20)
    fw = np.arange(0, 1.5, 0.1)

    xx_new, yy_new = np.meshgrid(far, fw, indexing='ij')
    #
    # xx = np.reshape(final_data[i, 1], (3, 3))
    # yy =  np.reshape(final_data[i, 2], (3, 3))
    # interp = f([200, 450, 700], [0, 1, 1.5])
    interp = f(far, fw)
    # # print(np.shape(interp))
    # # print(np.shape(xx_new))
    # # print(np.shape(yy_new))
    # # print(interp)
    fig = pl.figure()
    # ax = p3.Axes3D(fig)
    cs = pl.contour(xx_new, yy_new, interp.T, rstride=1, cstride=1, color='g', cmap=cm.coolwarm)
    pl.plot(maxes[::, 1], maxes[::, 2], "-ob", label='trajectory of maximum')
    pl.clabel(cs, fmt='%.1f')  # , colors="black")
    fig.colorbar(cs, shrink=0.5, aspect=5)
    pl.ylabel('FR/FW')
    pl.xlabel('FAR, mkmoles')
    # ax.set_zlabel('dCO2/dt *-1')
    pl.title('Maximum trajectory')
    # fig.legend()
    # pl.grid()
    # pl.savefig("gradient_metaopt_5678676787656765456765.png")
    pl.show()

    # print(type(maxes[::, 1][0]))
    # ffff = list(map(float, maxes[::, 1]))
    # print(type(ffff[0]))
    # print(ffff[0])
    # print(type(maxes[::, 2][0]))
    # print(type(maxes[::, 0][0]))

    fig = pl.figure()
    # ax = p3.Axes3D(fig)
    ax = pl.axes(projection='3d')
    cs = ax.plot_surface(xx_new, yy_new, interp.T, rstride=1, cstride=1, color='g', cmap=cm.coolwarm)
    pl.clabel(cs, fmt='%.3f')  # , colors="black")

    farp = list(map(float, maxes[::, 1]))
    frfwp = list(map(float, maxes[::, 2]))
    zp = (list(map(float, maxes[::, 0])))
    ax.plot3D(
        farp,
        frfwp,
        zp,
        "-",
        label='trajectory of maximum'
    )
    ax.scatter3D(
        farp,
        frfwp,
        zp,
        # c=list(map(float, maxes[::, 0])),
        cmap='Greens',
        label='trajectory of maximum'
    )

    for i in range(len(maxes)):
        # ax.annotate(str(maxes[i, 1])+","+str(maxes[i, 2]), (t[i], maxes[i, 0]))
        ax.text(farp[i], frfwp[i], zp[i], str(i))

    fig.colorbar(cs, shrink=0.5, aspect=5)
    ax.set_ylabel('FR/FW')
    ax.set_xlabel('FAR, mkmoles')
    ax.set_zlabel('dCO2/dt *-1')
    ax.set_title('Surface and maximum points')
    ax.legend()
    # pl.grid()
    # pl.savefig("gradient_metaopt_5678676787656765456765.png")
    pl.show()


    #
    # # lets show dynamics of max point coordinates
    #
    # fig = pl.figure()
    # ax = p3.Axes3D(fig)
    # # ax = pl.axes(projection='3d')
    # t = range(len(maxes))
    #
    #
    # ax.plot3D(
    #     t,
    #     frfwp,
    #     farp,
    #     "-b",
    #     label='trajectory of maximum'
    # )
    # ax.scatter3D(
    #     t,
    #     frfwp,
    #     farp,
    #     # c=list(map(float, maxes[::, 0])),
    #     cmap='Greens',
    #     label='trajectory of maximum'
    # )
    #
    # for i in range(len(maxes)):
    #     # ax.annotate(str(maxes[i, 1])+","+str(maxes[i, 2]), (t[i], maxes[i, 0]))
    #     ax.text(t[i], frfwp[i], farp[i], maxes[i, 4], 'z')
    #
    # ax.set_xlim(0, len(t))
    # ax.set_ylim(0, 1.5)
    # ax.set_zlim(5, 700)
    #
    # # fig.colorbar(cs, shrink=0.5, aspect=5)
    # ax.set_ylabel('FR/FW')
    # ax.set_xlabel('t, cycles')
    # ax.set_zlabel('FAR, mkmoles')
    # ax.set_title('Dynamics of maximum point')
    # ax.legend()
    # # pl.grid()
    # # pl.savefig("gradient_metaopt_5678676787656765456765.png")
    # pl.show()




    # test surface -------
    ffff = interpolate.interp2d([200, 450, 700], [0, 1, 1.5],
                               np.reshape(final_data[1, 0], (3, 3)), kind='linear')
    # far = np.arange(200, 800, 10)
    # fw = np.arange(0, 2, 0.05)
    far = np.arange(200, 700, 20)
    fw = np.arange(0, 1.5, 0.1)

    xx_new, yy_new = np.meshgrid(far, fw, indexing='ij')
    #
    # xx = np.reshape(final_data[i, 1], (3, 3))
    # yy =  np.reshape(final_data[i, 2], (3, 3))
    # interp = f([200, 450, 700], [0, 1, 1.5])
    interp = ffff(far, fw)
    # print(np.shape(interp))
    # print(np.shape(xx_new))
    # print(np.shape(yy_new))
    # print(interp)
    fig = pl.figure()
    ax = p3.Axes3D(fig)
    cs = ax.plot_surface(xx_new, yy_new, interp.T, rstride=1, cstride=1, color='g', cmap=cm.coolwarm)
    pl.clabel(cs, fmt='%.1f')  # , colors="black")
    fig.colorbar(cs, shrink=0.5, aspect=5)
    ax.set_ylabel('FR/FW')
    ax.set_xlabel('FAR, mkmoles')
    ax.set_zlabel('dCO2/dt *-1')
    ax.set_title('Interpolated, cycle {}'.format(final_data[i, 3]))
    # pl.grid()
    # pl.savefig("gradient_metaopt_5678676787656765456765.png")
    pl.show()

    # and at the end lets print all interpolated surfaces

    for i in range(0, len(final_data)):
        # # plot 3d points
        # print(np.shape(final_data))
        # print(final_data[i])
        # xx = np.reshape(final_data[i, 1], (3, 3))
        # yy =  np.reshape(final_data[i, 2], (3, 3))
        # zz = np.reshape(final_data[i, 0], (3, 3))
        # fig = pl.figure()
        # ax = p3.Axes3D(fig)
        # cs = ax.plot_surface(xx, yy, zz, cmap=cm.coolwarm, rstride=1, cstride=1, color='g')
        # pl.clabel(cs, fmt='%.1f')  # , colors="black")
        # fig.colorbar(cs, shrink=0.5, aspect=5)
        # ax.set_xlabel('FR/FW')
        # ax.set_ylabel('FAR, mkmoles')
        # ax.set_zlabel('dCO2/dt *-100000')
        # ax.set_title('Not interpolated')
        # pl.grid()
        # # pl.savefig("gradient_metaopt_5678676787656765456765.png")
        # pl.show()


        # points for interpolate
        # print(np.shape(final_data))
        # print(final_data[i])
        # print(np.shape(final_data[i, 1]), np.shape(final_data[i, 2]), np.shape(final_data[i, 0]))
        fff = interpolate.interp2d([200, 450, 700], [0, 1, 1.5],
                                 np.reshape(final_data[i, 0], (3, 3)), kind='linear')
        # far = np.arange(200, 800, 10)
        # fw = np.arange(0, 2, 0.05)
        far = np.arange(200, 700, 20)
        fw = np.arange(0, 1.5, 0.1)


        xx_new, yy_new = np.meshgrid(far, fw, indexing='ij')
        #
        # xx = np.reshape(final_data[i, 1], (3, 3))
        # yy =  np.reshape(final_data[i, 2], (3, 3))
        # interp = f([200, 450, 700], [0, 1, 1.5])
        interp = fff(far, fw)
        # print(np.shape(interp))
        # print(np.shape(xx_new))
        # print(np.shape(yy_new))
        # print(interp)
        fig = pl.figure()
        ax = p3.Axes3D(fig)
        cs = ax.plot_surface(xx_new, yy_new, interp.T, rstride=1, cstride=1, color='g', cmap=cm.coolwarm)
        pl.clabel(cs, fmt='%.1f')#, colors="black")
        fig.colorbar(cs, shrink=0.5, aspect=5)
        ax.set_ylabel('FR/FW')
        ax.set_xlabel('FAR, mkmoles')
        ax.set_zlabel('dCO2/dt *-1')
        ax.set_title('Interpolated, cycle {}'.format(final_data[i, 3]))
        # pl.grid()
        # pl.savefig("gradient_metaopt_5678676787656765456765.png")
        pl.show()

if __name__ == "__main__":
    test_parse_csv()



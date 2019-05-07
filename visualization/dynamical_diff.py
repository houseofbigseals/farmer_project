
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
from visualization.csv_read import red_far_by_curr, white_far_by_curr


def test_parse_csv():

    fieldnames = ["date", "time", "Ired", "Iwhite", "temp", "humid",
                   "CO2", "weight", "airflow", "cycle", "K30CO2"]

    # pd_data = pd.read_csv("data/data.csv", header=None, names=fieldnames)
    pd_data = pd.read_csv("data/prepared_data.csv", header=None, names=fieldnames)
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
        [np.array([0, 1]), 1, 2, 3, 4, 5],
        [np.array([0, 1]), 0, 0, 0, 0, 0]
        ]
    )
    print("shape of new data ", np.shape(new_data))
    # current_air = air[0]
    start_pointer = -1
    stop_pointer = -1

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

                    info_str = str(cycle[stop_pointer - 2]) + " " + \
                               str(dates[stop_pointer - 2]) + " " + \
                                str(times[stop_pointer - 2])
                    print("\n" + info_str)

                    co2_part = co2[start_pointer: stop_pointer]

                    # make a scipy interpolation here
                    dc = 1
                    number_of_cut = 220  # for first time
                    cut_co2 = co2_part[number_of_cut::dc]

                    # approximation

                    def func(tt, a, b):
                        return a * np.exp(b * tt)

                    # at full interval
                    y = np.array(cut_co2, dtype=float)
                    x = np.arange(0, len(y))
                    popt, pcov = curve_fit(func, x, y, p0=(2, -1))  # p0=(2.5, -1.3)
                    b0 = popt[1]
                    print("full approx a = {}, b = {}".format(popt[0],popt[1]))

                    # at first half of interval
                    cut2_co2 = cut_co2[:int(len(cut_co2)/2):dc]
                    y = np.array(cut_co2, dtype=float)
                    x = np.arange(0, len(y))
                    popt, pcov = curve_fit(func, x, y, p0=(2, -1))  # p0=(2.5, -1.3)
                    b1 = popt[1]
                    print("first half approx a = {}, b = {}".format(popt[0],popt[1]))

                    # at second half of interval
                    cut2_co2 = cut_co2[int(len(cut_co2) / 2)::dc]
                    y = np.array(cut2_co2, dtype=float)
                    x = np.arange(0, len(y))
                    popt, pcov = curve_fit(func, x, y, p0=(2, -1))  # p0=(2.5, -1.3)
                    b2 = popt[1]
                    print("second half approx a = {}, b = {}".format(popt[0], popt[1]))

                    # at first third of interval
                    cut2_co2 = cut_co2[:int(len(cut_co2) / 3):dc]
                    y = np.array(cut2_co2, dtype=float)
                    x = np.arange(0, len(y))
                    popt, pcov = curve_fit(func, x, y, p0=(2, -1))  # p0=(2.5, -1.3)
                    b3 = popt[1]
                    print("first third approx a = {}, b = {}".format(popt[0], popt[1]))

                    # at second third of interval
                    cut2_co2 = cut_co2[int(len(cut_co2) / 3):int(len(cut_co2)*2 / 3):dc]
                    y = np.array(cut2_co2, dtype=float)
                    x = np.arange(0, len(y))
                    popt, pcov = curve_fit(func, x, y, p0=(2, -1))  # p0=(2.5, -1.3)
                    b4 = popt[1]
                    print("second third approx a = {}, b = {}".format(popt[0], popt[1]))

                    # at third third of interval
                    cut2_co2 = cut_co2[int(len(cut_co2)*2 / 3)::dc]
                    y = np.array(cut2_co2, dtype=float)
                    x = np.arange(0, len(y))
                    popt, pcov = curve_fit(func, x, y, p0=(2, -1))  # p0=(2.5, -1.3)
                    b5 = popt[1]
                    print("third third approx a = {}, b = {}".format(popt[0], popt[1]))

                    # save results to new array
                    new_data = np.append(
                        new_data,
                        [[co2_part, far[stop_pointer - 2], fr_fw[stop_pointer - 2],
                         np.mean([b0, b1, b2, b3, b4, b5]), cycle[stop_pointer - 2], info_str]],
                        axis=0
                    )

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
        [np.zeros(9), np.zeros(9), np.zeros(9), 1],
        [np.zeros(9), np.zeros(9), np.zeros(9), 1]
        ]
    )

    # start_pointer = -1
    start_pointer = -1
    interval = 18

    for i in range(1, len(new_data)):
        if new_data[i, 4] > new_data[i-1, 4]:
            print("cycle is : ", new_data[i, 4])
            # it means that there is starting new cycle
            fut_arr = new_data[i:i+interval, 3]
            if i + interval < len(new_data):
                # reshape it and summ all repetions
                # make it acceptable for scipy.interpolate
                rw = np.array([200, 450, 700, 200, 450, 700, 200, 450, 700])
                far = np.array([0, 0, 0, 1, 1, 1, 1.5, 1.5, 1.5])
                dco2 = np.zeros(9, dtype=float)
                # lets sum repetions
                dco2[0] = (fut_arr[17] + fut_arr[1])/2
                dco2[1] = (fut_arr[16] + fut_arr[2]) / 2
                dco2[2] = (fut_arr[15] + fut_arr[0]) / 2
                dco2[3] = (fut_arr[11] + fut_arr[4]) / 2
                dco2[4] = (fut_arr[10] + fut_arr[5]) / 2
                dco2[5] = (fut_arr[9] + fut_arr[3]) / 2
                dco2[6] = (fut_arr[14] + fut_arr[7]) / 2
                dco2[7] = (fut_arr[12] + fut_arr[8]) / 2
                dco2[8] = (fut_arr[13] + fut_arr[6]) / 2
                # add it to final array
                final_data = np.append(final_data, [[-100000*dco2, far, rw, new_data[i, 5]]], axis=0)

    # remove first two rows - they are not necessary anymore
    print(len(final_data))
    final_data = np.delete(
        final_data,
        slice(0, 2),
        axis=0
    )
    print(len(final_data))

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
        print(np.shape(final_data[i, 1]), np.shape(final_data[i, 2]), np.shape(final_data[i, 0]))
        f = interpolate.interp2d([200, 450, 700], [0, 1, 1.5],
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
        interp = f(far, fw)
        print(np.shape(interp))
        print(np.shape(xx_new))
        print(np.shape(yy_new))
        print(interp)
        fig = pl.figure()
        ax = p3.Axes3D(fig)
        cs = ax.plot_surface(xx_new, yy_new, interp.T, rstride=1, cstride=1, color='g', cmap=cm.coolwarm)
        pl.clabel(cs, fmt='%.1f')#, colors="black")
        fig.colorbar(cs, shrink=0.5, aspect=5)
        ax.set_ylabel('FR/FW')
        ax.set_xlabel('FAR, mkmoles')
        ax.set_zlabel('dCO2/dt *-100000')
        ax.set_title('Interpolated, cycle {}'.format(final_data[i, 3]))
        # pl.grid()
        # pl.savefig("gradient_metaopt_5678676787656765456765.png")
        pl.show()

if __name__ == "__main__":
    test_parse_csv()



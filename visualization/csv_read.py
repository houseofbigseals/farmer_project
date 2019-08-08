import pandas as pd
import numpy as np
import pylab as pl
from math_tools.adjustment import red_far_by_curr, white_far_by_curr


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


def main():

    # old fields

    # fieldnames = ["date", "time", "Ired", "Iwhite", "temp", "humid", "CO2","weight"]

    # new fields

    # fieldnames = ["date", "time", "Ired", "Iwhite", "temp", "humid",
    #                "CO2", "weight", "airflow", "cycle", "K30CO2"]

    fieldnames = ["date", "time", "Ired", "Iwhite", "temp", "humid",
                  "CO2", "weight", "airflow", "K30CO2", "step", "point", "label"]
    # "date": date_,
    # "time": time_,
    # "Ired": ired,
    # "Iwhite": iwhite,
    # "temp": temp,
    # "humid": hum,
    # "CO2": co2,
    # "weight": weight,
    # "airflow": air,
    # "K30CO2": k30_co2,
    # "step": step,
    # "point": point,
    # "label": self.current_comment

    pd_data = pd.read_csv("../data/data_1244", header=None, names=fieldnames)
    # pd_data = pd.read_csv("data/good_transients_data.csv", header=None, names=fieldnames)
    # pd_data = pd.read_csv("../data/another_test_prepared_data_4.csv", header=None, names=fieldnames)
    # pd_data = pd.read_csv("data/data.csv", header=None, names=fieldnames)
    # pd_data = pd.read_csv("data/test_prepared_data_3.csv", header=None, names=fieldnames)
    print(pd_data.head())
    print(pd_data.tail())

    # plotting
    # tmin = 42000
    tmin = 0
    tmax = len(pd_data['time'])
    # tmax = 82000
    dt = 1
    ir = np.array(pd_data['Ired'][tmin:tmax:dt])
    iw = np.array(pd_data['Iwhite'][tmin:tmax:dt])
    co2 = np.array(pd_data['CO2'][tmin:tmax:dt])
    co2K30 = np.array(pd_data['K30CO2'][tmin:tmax:dt])
    air = np.array(pd_data['airflow'][tmin:tmax:dt])
    weight = np.array(pd_data['weight'][tmin:tmax:dt])
    times = np.array(pd_data['time'][tmin:tmax:dt])
    dates = np.array(pd_data['date'][tmin:tmax:dt])

    fr_fw = np.zeros(len(times))
    far = np.zeros(len(times))

    # creating new coordinates

    for i in range(len(far)):
        fr_fw_ = red_far_by_curr(ir[i])/white_far_by_curr(iw[i])
        far_ = red_far_by_curr(ir[i]) + white_far_by_curr(iw[i])
        # far[i], fr_fw[i] = make_cool_far_rw(far_, fr_fw_) # - please stop use it
        far[i]= far_
        fr_fw[i] = fr_fw_

        # # 2D plot of f_r and f_w by I
    # fig = pl.figure()
    # t = range(len(times))
    # # pl.xticks(t, times, rotation='vertical')
    # pl.plot(t, co2, '-g', label="CO2, ppm")
    # pl.plot(t, iw, '-b', label="I_white, mA")
    # pl.plot(t, ir, '-r', label="I_red, mA")
    # # pl.ylabel('CO2, ppm')
    # pl.xlabel('time')
    # pl.title("CO2 ppm with red and white currents")
    # pl.legend()
    # pl.grid()
    # pl.show()


    # 2D plot
    fig = pl.figure()
    t = range(len(times))
    # pl.xticks(t[0::1000], times[0::1000], rotation='vertical')
    pl.xticks(t[0::3500], dates[0::3500], rotation='vertical')
    pl.plot(t, co2, '-g', label="CO2, ppm")
    pl.plot(t, fr_fw*300, '-b', label="FARred/FARwhite")
    pl.plot(t, far, '-r', label="FAR summ, mkmoles")
    pl.plot(t,  air*400, '-k', label="Airflow ON")
    pl.plot(t, co2K30, '-c', label="CO2 outside")
    # pl.plot(t, weight, '-y', label="Raw weight, g")
    # pl.ylabel('CO2, ppm')
    pl.xlabel('time')
    pl.title("CO2 ppm with FARred/FARwhite and FAR summ, mkmoles")
    pl.legend()
    pl.grid()
    pl.show()

    temp = np.array(pd_data['temp'][tmin:tmax:dt])
    hum = np.array(pd_data['humid'][tmin:tmax:dt])

    fig = pl.figure()
    # pl.xticks(t, times, rotation='vertical')
    t = range(len(times))
    pl.xticks(t[0::3000], dates[0::3000], rotation='vertical')
    pl.plot(t, temp, '-r', label="Temp, C")
    # pl.plot(t, fr_fw, '-b', label="FARred/FARwhite")
    pl.plot(t, hum, '-b', label="Humidity, %")
    pl.plot(t, air * 100, '-k', label="Airflow ON")
    # pl.ylabel('CO2, ppm')
    pl.xlabel('time')
    pl.title("Temp and humidity by time")
    pl.legend()
    pl.grid()
    pl.show()

    # fig = pl.figure()
    # t = range(len(times))
    # # pl.xticks(t, times, rotation='vertical')
    # pl.plot(t, temp, '-r', label="Temp, C")
    # # pl.plot(t, fr_fw, '-b', label="FARred/FARwhite")
    # pl.plot(t, hum, '-b', label="Humidity, %")
    # pl.plot(t, air * 100, '-k', label="Airflow ON")
    # # pl.ylabel('CO2, ppm')
    # pl.xlabel('time')
    # pl.title("Temp and humidity by time")
    # pl.legend()
    # pl.grid()
    # pl.show()

    # fig = pl.figure()
    # t = range(len(times))
    # # pl.xticks(t, times, rotation='vertical')
    # pl.plot(t, co2, '-g', label="CO2, ppm")
    # # pl.plot(t, fr_fw, '-b', label="FARred/FARwhite")
    # pl.plot(t, far/10, '-r', label="FAR summ, mkmoles")
    # # pl.ylabel('CO2, ppm')
    # pl.xlabel('time')
    # pl.title("CO2 ppm with FARred/FARwhite and FAR summ, mkmoles")
    # pl.legend()
    # pl.grid()
    # pl.show()

    # lets plot only one index by time in one day
    t1 = 5749
    t2 = 40999

    weight_ = np.array(pd_data['weight'][t1:t2:dt])

    ## TODO warning tube weight added here !

    tube_weight = 375
    tube_weight_ = np.ones(len(weight_))*tube_weight
    times_ = np.array(pd_data['time'][t1:t2:dt])
    fig = pl.figure()
    t_ = range(len(times_))
    pl.xticks(t_[0::1000], times_[0::1000], rotation='vertical')
    pl.plot(t_, weight_ - tube_weight_, '-g', label="Weight, g")
    # pl.plot(t, fr_fw, '-b', label="FARred/FARwhite")
    # pl.plot(t, far/10, '-r', label="FAR summ, mkmoles")
    pl.ylabel('Weight, g')
    # pl.ylim(bottom=300, top=550)
    pl.xlabel('Time')
    pl.title("System raw weight by time")
    pl.legend()
    pl.grid()
    pl.show()


    # lets plot mean values by days
    # lets start from weight
    current_day = 0
    start_pointer = 0
    stop_pointer = 0
    mean_day_weights = []
    date = []
    for i in range(1, len(times)):
        if dates[i] != dates[i-1] or i == len(times) -1:
            print(dates[i-1])
            stop_pointer = i - 1
            mean_day_weights.append(np.mean(weight[start_pointer:stop_pointer]) - tube_weight)
            date.append(dates[i-1])
            start_pointer = i


    # 2D plot
    fig = pl.figure()
    t = range(len(mean_day_weights))
    pl.xticks(t, date, rotation='vertical')
    pl.plot(t, mean_day_weights, '-oy', label="Weight, g")
    # pl.plot(x, y_opt, '-r', label="Appr weight, g")
    pl.xlabel('time')
    pl.ylabel('Weight, g')
    pl.title('Mean day weight')

    pl.legend()
    pl.grid()
    pl.show()

    # # weight approximation with scipy.optimize.curve_fit
    # start_cut = 0
    # stop_cut = len(weight)
    # dc = 1
    #
    #
    # # lets subplot leaf area index
    # #y0 = 0.92
    # #y_end = 3.6
    # # so in model y = kx + b    b = 0.92 and k = 6.507*10^-6
    #
    # # approximation
    #
    # # def func(tt, a, b):
    # #     return a * np.exp(b * tt)
    #
    # def func(tt, a, b):
    #     return a * tt + b
    #
    # y = np.array(weight, dtype=float)
    # x = np.arange(0, len(y))
    # popt, pcov = curve_fit(func, x, y, p0=(2, -1))  # p0=(2.5, -1.3)
    # y_opt = func(x, *popt)
    # y_leaf = func(x, *[6.507*0.000001, 0.92])
    # print("weight: ", popt)
    # print("leaf area index: ", [6.507*0.000001, 0.92])
    # print(pcov)
    # perr = np.sqrt(np.diag(pcov))
    # print(perr)
    # # 2D plot
    # fig = pl.figure()
    # # t = range(len(weight))
    # pl.xticks(x[0::4000], dates[0::4000], rotation='vertical')
    # # pl.xticks(t, times, rotation='vertical')
    # # pl.plot(t, raw_co2, '-.g', label="CO2, ppm")
    # # pl.plot(t[number_of_cut::], cut_co2, '-b', label="cut CO2, ppm")
    # pl.plot(x, y, '-.b', label="Weight, g")
    # pl.plot(x, y_opt, '-r', label="Appr weight, g")
    # # pl.plot(x, y_leaf + 400, '-g', label="leaf area index + 400")
    # # pl.plot(t, fr_fw*200, '-b', label="FARred/FARwhite")
    # # pl.plot(t, far, '-r', label="FAR summ, mkmoles")
    # # pl.plot(t,  air*400, '-k', label="Airflow ON")
    # # pl.plot(t, co2K30, '-c', label="CO2 outside")
    # # pl.ylabel('CO2, ppm')
    # pl.xlabel('time')
    # pl.ylabel('Weight, g')
    # # pl.title('weight fit: weight = a{:.4f}*t + {:.6f}\n'.format(popt[0], popt[1]))
    # pl.title('Weight')
    #
    # pl.legend()
    # pl.grid()
    # pl.show()
    #
    #
    # # approximation with scipy.optimize.curve_fit
    # start_cut = 42067
    # stop_cut = 42543
    # dc = 1
    # number_of_cut = 220  # for first time
    # raw_co2 = co2[start_cut:stop_cut:dc]
    # cut_co2 = co2[start_cut+number_of_cut:stop_cut:dc]
    #
    # # approximation
    #
    # def func(tt, a, b):
    #     return a * np.exp(b * tt)
    #
    # y = np.array(cut_co2, dtype=float)
    # x = np.arange(0, len(y))
    # popt, pcov = curve_fit(func, x, y, p0=(2, -1)) # p0=(2.5, -1.3)
    # y_opt = func(x, *popt)
    # # 2D plot
    # fig = pl.figure()
    # t = range(len(raw_co2))
    # # pl.xticks(t, times, rotation='vertical')
    # # pl.plot(t, raw_co2, '-.g', label="CO2, ppm")
    # # pl.plot(t[number_of_cut::], cut_co2, '-b', label="cut CO2, ppm")
    # pl.plot(x, y, '-.b', label="cut CO2, ppm")
    # pl.plot(x, y_opt, '-g', label="appr CO2, ppm")
    # # pl.plot(t, fr_fw*200, '-b', label="FARred/FARwhite")
    # # pl.plot(t, far, '-r', label="FAR summ, mkmoles")
    # # pl.plot(t,  air*400, '-k', label="Airflow ON")
    # # pl.plot(t, co2K30, '-c', label="CO2 outside")
    # # pl.ylabel('CO2, ppm')
    # pl.xlabel('time')
    # pl.title('fit: a={:.4f}, b={:.6f}'.format(popt[0], popt[1]))
    # pl.legend()
    # pl.grid()
    # pl.show()




if __name__ == "__main__":
    main()
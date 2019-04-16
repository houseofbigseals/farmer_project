import pandas as pd
import numpy as np
import pylab as pl
import mpl_toolkits.mplot3d.axes3d as p3
from matplotlib import cm
from scipy import interpolate


def red_far_by_curr(Ir:float):
    # this constants are determined from experiment
    a1 = 1.77451454
    b1 = 5.52067992
    return a1*Ir + b1


def white_far_by_curr(Iw:float):
    # this constants are determined from experiment
    a2 = 2.40069694
    b2 = 0.24050309
    return a2*Iw + b2


def main():

    # old fields

    # fieldnames = ["date", "time", "Ired", "Iwhite", "temp", "humid", "CO2","weight"]

    # new fields

    fieldnames = ["date", "time", "Ired", "Iwhite", "temp", "humid",
                   "CO2", "weight", "airflow", "cycle", "K30CO2"]

    pd_data = pd.read_csv("data/data.csv", header=None, names=fieldnames)
    print(pd_data.head())
    print(pd_data.tail())

    # plotting
    tmin = 0
    tmax = len(pd_data['time'])
    dt = 1
    ir = np.array(pd_data['Ired'][tmin:tmax:dt])
    iw = np.array(pd_data['Iwhite'][tmin:tmax:dt])
    co2 = np.array(pd_data['CO2'][tmin:tmax:dt])
    air = np.array(pd_data['airflow'][tmin:tmax:dt])
    times = pd_data['time'][tmin:tmax:dt]

    fr_fw = np.zeros(len(times))
    far = np.zeros(len(times))

    # creating new coordinates

    for i in range(len(far)):
        fr_fw[i] = red_far_by_curr(ir[i])/white_far_by_curr(iw[i])
        far[i] = red_far_by_curr(ir[i]) + white_far_by_curr(iw[i])

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
    # pl.xticks(t, times, rotation='vertical')
    pl.plot(t, co2, '-g', label="CO2, ppm")
    pl.plot(t, fr_fw*100, '-b', label="FARred/FARwhite")
    pl.plot(t, far/10, '-r', label="FAR summ, mkmoles")
    pl.plot(t,  air*100, '-k', label="Airflow ON")
    # pl.ylabel('CO2, ppm')
    pl.xlabel('time')
    pl.title("CO2 ppm with FARred/FARwhite and FAR summ, mkmoles")
    pl.legend()
    pl.grid()
    pl.show()

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



if __name__ == "__main__":
    main()
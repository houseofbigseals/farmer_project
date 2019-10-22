import pandas as pd
import numpy as np
import pylab as pl


# from adjustment import


def plot_dynamics_of_search():
    fieldnames = [
        'date',
        'time',
        'x1',
        'x2',
        'Q',
        'F',
        'step',
        'label',
        'dick'
    ]
    # pd_data = pd.read_csv("../data/simple_gradient_method_1300.csv", header=None, names=fieldnames)
    pd_data = pd.read_csv("../data/data_1320/search_method_1320.log", header=None, names=fieldnames)
    print(pd_data.shape)
    # print(pd_data.head())
    useful_rows = ['dF']
    useful_rows = ['the_only_one']
    filtered_pd = pd_data[pd_data['label'].isin(useful_rows)]
    # print(filtered_pd)
    print(filtered_pd.shape)
    print(filtered_pd.head())
    print(filtered_pd.tail())
    print(filtered_pd['x1'].head())
    print(filtered_pd['x2'].head())

    x1 = pd.to_numeric(filtered_pd['x1'])
    x2 = pd.to_numeric(filtered_pd['x2'])
    F = pd.to_numeric(filtered_pd['F'])
    Q = pd.to_numeric(filtered_pd['Q'])
    # Q_true = Q/(0.08*1.8*1000) # TODO corrected due to error in adjustment module (remove after)

    Q_true = Q
    Qmax = Q_true.max()
    Q_true = Q_true/Qmax

    # Q_true = Q_true[np.abs(Q_true - Q_true.mean()) <= (3 * Q_true.std())]
    # keep only the ones that are within +3 to -3 standard deviations in the column 'Data'.

    # Q_true = Q_true[~(np.abs(Q_true - Q_true.mean()) > (3 * Q_true.std()))]
    print(Q_true)
    # for
    step = pd.to_numeric(filtered_pd['step'])
    dates = filtered_pd['date']
    t = range(len(dates))
    t_ticks = np.linspace(0, len(dates)-1, 20)
    # pl.xticks(t[0::1000], times[0::1000], rotation='vertical')

    fig, axs = pl.subplots(4, sharex=True)
    # fig.suptitle('Search dynamics')
    pl.xticks(t[0::11], dates[0::11], rotation='vertical')
    axs[0].plot(t, x1, '-r', label="x1 coordinates of search steps")
    axs[0].grid()
    axs[0].set_ylabel("Total PPFD, mkmoles/m2*sec")
    # axs[0].
    axs[1].plot(t, x2, '-b', label="x2 coordinates of search steps")
    axs[1].grid()
    axs[1].set_ylabel("Red/White")
    axs[2].plot(t, Q_true, '-g', label="Q values for search steps")
    axs[2].set_ylabel("Q_search, kg ESM / kg biomass")
    axs[2].grid()
    axs[3].plot(t, F, '-c', label="F values for search steps")
    # axs[3].plot(t, Q_true, '-c', label="F values for search steps")
    axs[3].set_ylabel("F, mgCO2/sec")
    axs[3].grid()
    pl.show()

    # only Q
    fig = pl.figure()
    pl.xticks(t[0::11], dates[0::11], rotation='vertical')

    # pl.plot(t, Q_true, '-g', label="Q_search, kg ESM / kg biomass ")
    pl.plot(t, Q_true, '-g', label="G_search, отн. ед.")
    # pl.plot(t, fr_fw, '-b', label="FARred/FARwhite")
    # pl.plot(t, far/10, '-r', label="FAR summ, mkmoles")
    pl.ylabel('G / Gmax')
    # pl.ylim(bottom=300, top=550)
    pl.xlabel('Time')
    # pl.title("Q, kg ESM / kg biomass")
    pl.legend()
    pl.grid()
    pl.show()


if __name__ == "__main__":
    plot_dynamics_of_search()

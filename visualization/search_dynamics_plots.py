import csv
import pandas as pd
import numpy as np
import pylab as pl
# from adjustment import
from math_tools.adjustment import final_intQ


def plot_dynamics_of_search():
    fieldnames = [
        'date',
        'time',
        'x1',
        'x2',
        'Q',
        'step',
        'label'
    ]
    pd_data = pd.read_csv("../data/simple_gradient_method_1267.csv", header=None, names=fieldnames)
    print(pd_data.shape)
    # print(pd_data.head())
    useful_rows = ['dF']
    filtered_pd = pd_data[pd_data['label'].isin(useful_rows)]
    # print(filtered_pd)
    print(filtered_pd.shape)
    print(filtered_pd.head())
    print(filtered_pd['x1'].head())
    print(filtered_pd['x2'].head())

    x1 = pd.to_numeric(filtered_pd['x1'])
    x2 = pd.to_numeric(filtered_pd['x2'])
    Q = pd.to_numeric(filtered_pd['Q'])
    Q_true = Q/(0.08*1.8*1000) # TODO corrected due to error in adjustment module (remove after)
    # for
    step = pd.to_numeric(filtered_pd['step'])
    dates = filtered_pd['date']
    t = range(len(dates))
    t_ticks = np.linspace(0, len(dates)-1, 20)
    # pl.xticks(t[0::1000], times[0::1000], rotation='vertical')

    fig, axs = pl.subplots(3, sharex=True)
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
    axs[2].set_ylabel("Q, kg ESM / kg biomass")
    axs[2].grid()
    pl.show()

if __name__ == "__main__":
    plot_dynamics_of_search()

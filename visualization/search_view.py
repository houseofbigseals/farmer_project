
# we have to read search method config and
# then draw all steps and measured points around every step
# all that things must be drawed with parameters from config

import pandas as pd
import pylab as pl
import numpy as np
from matplotlib.ticker import FormatStrFormatter


def draw_search(
        file_path: str,
        fieldnames: list
):

    pd_data = pd.read_csv(file_path, header=None, names=fieldnames)

    final_points = pd_data[pd_data['label'] == 'dF']
    print(final_points.head())
    x1 = np.array(final_points['x1'])
    x2 = np.array(final_points['x2'])
    # 2D plot of search area
    fig, ax = pl.subplots(1, 1)
    t = range(len(x1))
    pl.xticks(t, x1, rotation=90)
    ax.xaxis.set_major_formatter(FormatStrFormatter('%.1f'))
    # pl.xticks(t[0::3500], dates[0::3500], rotation='vertical')
    pl.plot(x1, x2, '-vb', label="gradient search")
    # pl.xticks(rotation=90)
    # pl.tick_params(length=0.1)
    # pl.plot(t, weight, '-y', label="Raw weight, g")
    # pl.ylabel('CO2, ppm')
    # pl.ylim(bottom=100, top=800)
    # pl.xlim(left=-1, right=3)



    # ax.xaxis.set_major_formatter(FormatStrFormatter('%.1f'))

    pl.xlabel('x1 is far')
    pl.ylabel('x2 is red/white')
    pl.title("Search iterations")
    pl.legend()
    pl.grid()
    pl.show()


if __name__ == "__main__":

    search_log_fields = [
        'date',
        'time',
        'x1',
        'x2',
        'Q',
        'step',
        'label'
    ]
    path = "../data/stupid_gradient_method2.log"
    draw_search(path, search_log_fields)
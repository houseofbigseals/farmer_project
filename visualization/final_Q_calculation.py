
import csv
import pandas as pd
import numpy as np
from math_tools.adjustment import final_intQ



def Q_calculation():
    fieldnames = [
        'date',
        'time',
        'x1',
        'x2',
        'Q',
        'step',
        'label'
    ]
    # pd_data = pd.read_csv("../data/search_method_1370.csv", header=None, names=fieldnames)
    # print(pd_data.shape)
    # # print(pd_data.head())
    # # print(pd_data.tail())
    #
    # useful_rows = ['dF']
    # filtered_pd = pd_data[pd_data['label'].isin(useful_rows)]
    # # print(filtered_pd)
    # print(filtered_pd.shape)
    # print(filtered_pd.head())
    # print(filtered_pd['x1'].head())
    # print(filtered_pd['x1'].tail())
    # # x1 = np.array(filtered_pd['x1'])
    # # x1 = np.int(x1)
    # x1 = pd.to_numeric(filtered_pd['x1'])
    # print(x1.head())
    #
    # x1_sum = x1.sum(axis=0)
    # x1_len = len(x1.index)
    # print(x1_sum, x1_len)

    dM_12_22_exp = 197  # grams
    dM_12_22_control = 197   # grams
    E_12_22_control = 500  # mkmoles/m2sec
    E_12_22_exp = 350  # mkmoles/m2sec
    # print(x1_sum/x1_len)

    # Q_12_22_exp = final_intQ(x1_sum/x1_len, dM_12_22_exp)
    Q_12_22_exp = final_intQ(E_12_22_exp, dM_12_22_exp)
    print("G_exp", Q_12_22_exp)
    Q_12_22_control = final_intQ(E_12_22_control, dM_12_22_control)
    print("G_control", Q_12_22_control)
    result = (Q_12_22_control - Q_12_22_exp)/Q_12_22_control
    print(result)



if __name__ == "__main__":
    Q_calculation()
import pandas as pd
import numpy as np
from visualization.csv_read import red_far_by_curr, white_far_by_curr

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

def get_full_cycle_from_csv(cycle: int):
    # lets try get all rows of specific cycle
    fieldnames = ["date", "time", "Ired", "Iwhite", "temp", "humid",
                  "CO2", "weight", "airflow", "cycle", "K30CO2"]
    pd_data = pd.read_csv(
        '../data/another_test_prepared_data_4.csv',
        header=None,
        names=fieldnames
    )
    # df1 = df1.assign(e=p.Series(np.random.randn(sLength)).values)
    # add rw and far columns
    # at first create them
    # i dont know how to do it correctly

    tmin = 0
    tmax = len(pd_data['time'])
    dt = 1
    ir = np.array(pd_data['Ired'][tmin:tmax:dt])
    iw = np.array(pd_data['Iwhite'][tmin:tmax:dt])

    fr_fw = np.zeros(len(pd_data['Ired']))
    far = np.zeros(len(pd_data['Ired']))

    # creating new coordinates
    for i in range(len(far)):
        fr_fw_raw = red_far_by_curr(ir[i])/white_far_by_curr(iw[i])
        far_raw = red_far_by_curr(ir[i]) + white_far_by_curr(iw[i])
        far[i], fr_fw[i] = make_cool_far_rw(far_raw, fr_fw_raw)

    # add them to pd_data
    pd_data = pd_data.assign(far=pd.Series(far).values)
    pd_data = pd_data.assign(fr_fw=pd.Series(fr_fw).values)

    # filtered = pd_data[pd_data.cycle == cycle]
    # filtered[filtered.airflow == 0]


    # filter it by cycle and airflow
    pd_cycle = pd_data[pd_data.cycle == cycle][pd_data.airflow == 0]
    # group it by far and rw values
    # pd_cycle_groups = pd_cycle.groupby('far')
    # print(pd_cycle_groups.groups)

    print(pd_cycle)

if __name__ == "__main__":
    get_full_cycle_from_csv(0)
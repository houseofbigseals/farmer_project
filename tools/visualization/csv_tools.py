import pandas as pd
import numpy as np
from tools.visualization.csv_read import red_far_by_curr, white_far_by_curr

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

def make_table_points_from_rw(far, rw):
    # schedule = [
    #     [10, 258, 10],  # 700, 0
    #     [10, 69, 10],  # 200, 0
    #     [10, 163, 10],  # 450, 0
    #     [166, 133, 10],  # 700, 1
    #     [46, 38, 10],  # 200, 1
    #     [106, 85, 10],  # 450, 1
    #     [199, 106, 10],  # 700, 1.5
    #     [56, 30, 10],  # 200, 1.5
    #     [128, 68, 10],  # 450, 1.5
    #     [166, 133, 10],  # 700, 1  ------------------- repeating
    #     [106, 85, 10],  # 450, 1
    #     [46, 38, 10],  # 200, 1
    #     [128, 68, 10],  # 450, 1.5
    #     [199, 106, 10],  # 700, 1.5
    #     [56, 30, 10],  # 200, 1.5
    #     [10, 258, 10],  # 700, 0
    #     [10, 163, 10],  # 450, 0
    #     [10, 69, 10]  # 200, 0
    # ]

    schedule = [
        [700, 0, 1],
        [200, 0, 2],
        [450, 0, 3],
        [700, 1, 4],
        [200, 1, 5],
        [450, 1, 6],
        [700, 1.5, 7],
        [200, 1.5, 8],
        [450, 1.5, 9],
        [700, 1, 10],
        [450, 1, 11],
        [200, 1, 12],
        [450, 1.5, 13],
        [700, 1.5, 14],
        [200, 1.5, 15],
        [700, 0, 16],
        [450, 0, 17],
        [200, 0, 18]
    ]

    for p in schedule:
        if p[0] == far and p[1] == rw:
            return p[2]

    # if no one point from schedule matches
    raise ValueError("No one point from table match")


def get_full_cycle_from_csv(cycle: int):
    # lets try get all rows of specific cycle
    fieldnames = ["date", "time", "Ired", "Iwhite", "temp", "humid",
                  "CO2", "weight", "airflow", "cycle", "K30CO2"]
    pd_data = pd.read_csv(
        '../data/another_test_prepared_data_4.csv',
        header=None,
        names=fieldnames
    )
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
    point_number = np.zeros(len(pd_data['Ired']))

    # creating new coordinates
    for i in range(len(far)):
        fr_fw_raw = red_far_by_curr(ir[i])/white_far_by_curr(iw[i])
        far_raw = red_far_by_curr(ir[i]) + white_far_by_curr(iw[i])
        far[i], fr_fw[i] = make_cool_far_rw(far_raw, fr_fw_raw)
        point_number[i] = make_table_points_from_rw(far[i], fr_fw[i])

    # add them to pd_data
    pd_data = pd_data.assign(far=pd.Series(far).values)
    pd_data = pd_data.assign(fr_fw=pd.Series(fr_fw).values)
    pd_data = pd_data.assign(point_number=pd.Series(point_number).values)

    # filtered = pd_data[pd_data.cycle == cycle]
    # filtered[filtered.airflow == 0]


    # filter it by cycle and airflow
    pd_cycle = pd_data[pd_data.cycle == cycle][pd_data.airflow == 0]
    # group it by far and rw values
    pd_cycle_groups = pd_cycle.groupby('point_number')
    print(pd_cycle_groups['co2'].groups)

    print(pd_cycle[0:100])

if __name__ == "__main__":
    get_full_cycle_from_csv(0)
import pandas as pd
import numpy as np
import csv
import os

def test_prepare_csv():

    fieldnames = ["date", "time", "Ired", "Iwhite", "temp", "humid",
                   "CO2", "weight", "airflow", "cycle", "K30CO2"]

    # pd_data = pd.read_csv("data/data.csv", header=None, names=fieldnames)
    # old_datafile = os.path.abspath("data/data.csv")
    old_datafile = "../data/data.csv"
    new_datafile = "../data/partly_test_prepared_data_4.csv"
    pd_data = pd.read_csv(old_datafile, header=None, names=fieldnames)
    print(pd_data.head())
    print(pd_data.tail())

    # convert data to np.array
    tmin = 10
    tmax = len(pd_data['time'])
    dt = 1
    with open(new_datafile, "w", newline='') as out_file:
        for i in range(tmin, tmax, dt):
            if pd_data['Ired'][i] == 10 and pd_data['Iwhite'][i] == 10:
                # simple remove this points
                pass
            else:
                # if pd_data['temp'][i] <= 20:
                #     # it means that there is an error with dht11
                #     # TODO: it may cause errors, in another experiment (where 25C is ok)
                #     temp = pd_data['temp'][i-1]
                #     # TODO: it may cause errors, if previous (first) data incorrect
                # else:
                #     temp = pd_data['temp'][i]

                if pd_data['humid'][i] > 110:
                    # it means that there is an error with dht11
                    hum = pd_data['humid'][i-1]
                    # TODO: it may cause errors, if previous (first) data incorrect
                else:
                    hum = pd_data['humid'][i]

                if abs(pd_data['weight'][i] - pd_data['weight'][i-1])>50  :
                    # it means that its noize
                    weight = pd_data['weight'][i-1]
                else:
                    weight = pd_data['weight'][i]

                # at least add new row to new csv file
                data = {
                    "date": pd_data['date'][i],
                    "time": pd_data['time'][i],
                    "Ired": pd_data['Ired'][i],
                    "Iwhite": pd_data['Iwhite'][i],
                    "temp": pd_data['temp'][i],
                    "humid": hum,
                    "CO2": pd_data['CO2'][i],
                    "weight": weight,
                    "airflow": pd_data['airflow'][i],
                    "cycle": pd_data['cycle'][i],
                    "K30CO2": pd_data['K30CO2'][i]
                }

                writer = csv.DictWriter(out_file, delimiter=',', fieldnames=fieldnames)
                # writer.writeheader()
                writer.writerow(data)

if __name__ == "__main__":
    test_prepare_csv()
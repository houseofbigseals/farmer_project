import os
import csv
import pandas as pd
import logging

logger = logging.getLogger("Worker.DataHandler")


class DataHandler(object):
    """
    This class must contain all methods and objects
    that are used with measures parsing, saving and loading
    It must work with local csv files and with remote sql db
    """

    def __init__(
            self,
            worker: int,  # really its id
            session: int,  # really its id
            fields: list  # list of fields in data table
    ):
        self.session = session
        self.worker = worker
        self.fields = fields
        # here we must check if there is table, that corresponds
        # to current session (i e if there is csv file data_{session_id} on disc
        # and if there is data_{session_id} table on sql server)
        # if no, we have to create them both

        # lets check if we have directory
        data_path = os.path.abspath('../data')
        if not os.path.exists(data_path):
            os.mkdir(data_path)
            logger.info("Directory {} created ".format(data_path))
            print()
        else:
            logger.info("Directory {} found ".format(data_path))

        # then lets check file on disc
        local_data_path = os.path.join(data_path, 'data_{}'.format(self.session))

        if os.path.isfile(local_data_path):
            self.data_path = local_data_path
        else:
            # add header to new empty csv file
            with open(local_data_path, "w", newline='') as out_file:
                # writer = csv.DictWriter(out_file, delimiter=',', fieldnames=self.fields)
                # writer.writeheader()

                # we have not to write header !!!!
                pass
            self.data_path = local_data_path

        # then check if this table exists in db

        # if not SQLHandler.check_session(worker, session)
        # SQLHandler.add_session(worker, session, fields)

    def get_one_point(self, step, point):
        pd_data = pd.read_csv(
            self.data_path,
            header=None,
            names=self.fields
        )
        # filter it by step and airflow
        # TODO: add here filtering by label in future
        # pd_point = pd_data[pd_data.step == step][pd_data.point == point][pd_data.airflow == 0][pd_data.label != 'loading']
        # print(pd_data['step'])
        pd_point = pd_data.loc[(pd_data['step'] == step)
                              & (pd_data['point'] == point)
                              & (pd_data.airflow == 0)
                              & (pd_data.label == 'measure')
              ]
        print(pd_point)
        # print(pd_data.loc[pd_data['step'] == 0])

        # print(type(pd_data.))
        # [pd_data.point == point][pd_data.airflow == 0]
        # [
        #     pd_data.label != 'loading']

        return pd_point

    def get_full_data(self):
        pd_data = pd.read_csv(
            self.data_path,
            header=None,
            names=self.fields
        )
        # mb add here some filtering or smth
        return pd_data

    def add_measure(self, data: dict):
        # data must be a dictionary with keys - columns names
        # and values - row values for each column
        # TODO: add check if not all required fields are in dict
        fieldnames = data.keys()
        # TODO: mb fill missing fields with smth in future
        with open(self.data_path, "a", newline='') as out_file:
            writer = csv.DictWriter(out_file, delimiter=',', fieldnames=fieldnames)
            writer.writerow(data)
        # then add row to sql table
        # SQLHandler.add_measure(data)


if __name__ == "__main__":
    print(os.path.abspath('../data'))
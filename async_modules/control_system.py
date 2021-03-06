import time
import logging
import asyncio
from typing import Any
import localconfig
import os
from reports.config_handler import ConfigHandler
from async_modules.tasks import SingleTask, LongSingleTask, PeriodicCoro, SingleCoro
from math_tools.search_methods import StupidGradientMethod, SimpleGradientMethod, TableSearch, StaticSearch
from async_modules.data_handler import DataHandler
from math_tools.adjustment import currents_from_newcoords, red_far_by_curr, white_far_by_curr
from math_tools.math_methods import differentiate_one_point
import csv
import async_modules.units as units

logger = logging.getLogger("Worker.ControlSystem")
logger2 = logging.getLogger("SearchLog")


class ControlSystem:
    """
    This is search system object
    It rules all experimental things
    such as timings of measures, algorithms and smth
    """
    def __init__(
            self,
            data_path: str,
            worker: Any = None,  # TODO is this correct way or not
            config_path: str = "worker.conf"
    ):
        self.loop = asyncio.get_event_loop()
        # read config
        # config = localconfig.config
        # config.read(config_path)
        config = ConfigHandler(config_path)
        self.worker = worker
        self.calibration_time = config.get_value('control_system', 'calibration_time')
        # self.search_params_file = config.get_value('control_system', 'search_point_file')
        # start red and white for time where no search
        self.start_red = config.get_value('control_system', 'start_red')
        self.start_white = config.get_value('control_system', 'start_white')
        self.datafile = config.get_value('control_system', 'datafile')
        self.time_of_measure_period = config.get_value('control_system', 'time_of_measure_period')

        self.measure_period = config.get_value('control_system', 'measure_time')
        self.sleep_between_calibrations = config.get_value('control_system', 'sleep_between_calibrations')
        self.sleep_after_calibrations = config.get_value('control_system', 'sleep_after_calibrations')
        self.pipe_mass = config.get_value('control_system', 'mass_of_pipe')
        self._session_id = config.get_value('session', 'session_id')
        self.worker_id = config.get_value('worker', 'worker_id')
        # add fields for our data tables
        self.data_fields = config.get_value('control_system', 'data_fields')
        # self.data_fields = [
        #     "date",
        #     "time",
        #     "Ired",
        #     "Iwhite",
        #     "temp",
        #     "humid",
        #     "CO2",
        #     "weight",
        #     "airflow",
        #     "K30CO2",
        #     "step",
        #     "point",
        #     "label"
        # ]
        data_data_path = data_path
        # add data_handler
        self.data_handler = DataHandler(
            worker=self.worker_id,
            session=self._session_id,
            fields=self.data_fields,
            data_path=data_data_path
        )

        # init search logger
        logger2.setLevel(logging.DEBUG)
        log2_path = os.path.join(data_path, 'search_{}.log'.format(self._session_id))
        fh = logging.FileHandler(log2_path)
        formatter = logging.Formatter('%(asctime)s;%(name)s;%(levelname)s;%(message)s',
                                      "%Y-%m-%d;%H:%M:%S;%z")
        fh.setFormatter(formatter)
        # add handler to logger object
        logger2.addHandler(fh)


        # default search parameters
        # skwargs = dict(config.items("SimpleGradientMethod"))
        # self.search_method = SimpleGradientMethod(**skwargs)
        # self.search_method = TableSearch()
        self.search_method = StaticSearch()

        # load current search step
        self.current_search_step = config.get_value('control_system', 'search_start_step')
        # TODO: in future we will add some image of search system last condition
        #  to automatically start with this parameters after power shutdown or smth unexpected
        # set current search point 0 as default, because we need to
        # restart measure in current step if smth broken
        self.current_search_point = 0

        # # find search_point_config and check it
        # try:
        #     with open(self.search_params_file) as f:
        #         # we have to read one number from this file
        #         raw_data = f.read()
        #         data = int(raw_data)
        #         self.current_search_step = data
        #         logger.info("Search_point_config file found, current_search_step loaded")
        # except Exception as e:
        #     logger.error("Error while reading search_point_config: {}".format(e))
        #     logger.error("Creating new default search_point_config")
        #     with open(self.search_params_file, "w") as f:
        #         f.write("{}".format(self.current_search_step))

        # find search table and check it
        self.search_method_log = config.get_value('control_system', 'search_logfile')
        self.search_log_fields = config.get_value('control_system', 'search_log_fields')
        # self.search_log_fields = [
        #     'date',
        #     'time',
        #     'x1',
        #     'x2',
        #     'Q',
        #     'F',
        #     'step',
        #     'label'
        # ]
        self.search_method_log_path = os.path.join(data_path,
                                                   self.search_method_log+'_{}.log'.format(self._session_id))
        try:
            with open(self.search_method_log_path) as f:
                pass  # TODO change to isfile construction
                logger.info("search_method_log file found")
        except Exception as e:
            logger.error("Error while reading search_method_log: {}".format(e))
            logger.error("Creating new default search_method_log")
            with open(self.search_method_log_path, "w") as f:
                writer = csv.DictWriter(f, delimiter=',', fieldnames=self.search_log_fields)
                writer.writeheader()
                # f.write('')

        # add table with search points of current step
        self.current_search_table = self.search_method.search_table
        self.search_step_done = False
        # self.search_lock = asyncio.Lock()
        self.datafile_lock = asyncio.Lock()
        self.calibration_lock = asyncio.Lock()
        self.current_comment = "loading"
        self.just_started = True

        # append units
        # read list list_of_available_units from units.py
        # go through it and find if some unit name is in config
        # then add it and create its object with parameters from config
        # then dynamically add it to self attributes
        units_units = units.list_of_available_units
        self.unitnames = []

        # here is dynamical loading units
        # its not simple to understand that painful thing
        for u in units_units:
            # we have to check all units from library if they in use
            if u[0] in config.sections() and config.get_value(u[0], 'use') is True:
                # u[0] is unit name in config
                # u[1] is real unit name
                self.unitnames.append(u[0])
                kwargs = config.get_section(u[0])  # get all params of unit as a dict
                kwargs.pop('use')  # we dont need that key as argument of unit
                unit_obj = getattr(units, u[1])  # units module has unit name (u[1]) as attribute
                setattr(self, u[0], unit_obj(**kwargs))  # we want to set that attribute to self
                logger.debug("{} added to control system".format(u[0]))

        # system unit not in config because we always use it
        # so we have to add it manually
        self.system_unit = units.SystemUnit(worker=worker)
        self.unitnames.append('system_unit')
        logger.debug("system_unit added to control system")

        # TODO fix that its stupid

        # self.system_unit = getattr(self, 'system_unit')  # we already add it
        self.led_unit = getattr(self, 'led_unit')
        self.co2_sensor_unit = getattr(self, 'co2_sensor_unit')
        self.gpio_unit = getattr(self, 'gpio_unit')
        self.weight_unit = getattr(self, 'weight_unit')
        self.k30_unit = getattr(self, 'k30_unit')
        self.temp_sensor_unit = getattr(self, 'temp_sensor_unit')

    async def start(self):
        self.just_started = True
        # start all things, those need to be done once
        await self.gpio_unit.start_coolers()
        # await self._gpio_unit.start_draining()
        await self.gpio_unit.stop_draining()
        await self.led_unit.set_current(red=self.start_red, white=self.start_white)
        # do async init for some units
        await self.co2_sensor_unit.init()  # for time
        # we really dont need measures until search started
        # await self.worker.measure_task.stop()

    async def stop(self):
        await self.gpio_unit.stop()
        # TODO: mb add stopping led driver?

    async def stop_ventilation(self):
        res = ""
        res += await self.gpio_unit.stop_ventilation()
        return res

    async def start_ventilation(self):
        res = ""
        res += await self.gpio_unit.start_ventilation()
        return res

    async def do_calibration(self):
        res = ""
        res += await self.gpio_unit.start_calibration()
        res += await self.co2_sensor_unit.do_calibration()
        await asyncio.sleep(self.calibration_time)
        res += await self.gpio_unit.stop_calibration()
        return res

    async def manual_reconfiguration(self):
        new_far = self.current_search_table[self.current_search_point].x1
        new_rw = self.current_search_table[self.current_search_point].x2
        # then lets convert them to Ired and Iwhite
        new_red, new_white = currents_from_newcoords(new_far, new_rw)
        # then create coro for measure new search point
        reconfiguration_coro = SingleCoro(
            self.reconfiguration,
            "reconfiguration_task",
            red=new_red,
            white=new_white,
            period=10  # TODO: fix that thing somehow but with beauty
        )
        await reconfiguration_coro.start()

    async def update_state(self):
        logger.debug("update_state coro started")
        if not self.calibration_lock.locked():
            # if it locked, it means that there is calibration now and
            # we do not need to do anything now
            t = time.localtime()
            if t.tm_min % self.measure_period == 0:
                if self.just_started:
                    # we have to wait until we got real measure data
                    logger.info("Avoid first data period, because it is unreliable")
                    self.just_started = False
                    # its time to do measures for first search point from table
                    # at first find new far and r/w coordinates
                    new_far = self.current_search_table[self.current_search_point].x1
                    new_rw = self.current_search_table[self.current_search_point].x2
                    # then lets convert them to Ired and Iwhite
                    new_red, new_white = currents_from_newcoords(new_far, new_rw)
                    # then create coro for measure new search point
                    reconfiguration_coro = SingleCoro(
                        self.reconfiguration,
                        "reconfiguration_task",
                        red=new_red,
                        white=new_white,
                        period=self.sleep_after_calibrations # TODO adadafgafgahgghb error111
                    )
                    await reconfiguration_coro.start()
                else:
                    # here we need to put result of finished previous
                    # measuring to appropriate point in self.current_search_table
                    logger.info("update_state trying to find current point data")
                    # firstly lets get current measured interval
                    point_data = self.data_handler.get_one_point(
                        self.current_search_step,
                        self.current_search_point
                    )
                    # then lets calculate Q on this data
                    try:
                        f, q, fe = differentiate_one_point(data=point_data,
                                                           mass_of_pipe=self.pipe_mass,
                                                           cut_number=100,
                                                           points_low_limit=100,
                                                           len_of_measure_period=self.time_of_measure_period
                                                           )
                        logger.info("F = {}, Q = {}, F/E = {}".format(
                            f, q, fe
                        ))
                        logger2.info("F = {}, Q = {}, F/E = {}".format(
                            f, q, fe
                        ))
                    except Exception as e:
                        logger.error("Error while fit: {}".format(e))
                        logger.error("The search is broken")
                        logger.error("We will use fake Q because "
                                      "of that error to keep plants alive")
                        logger2.error("Error while fit: {}".format(e))
                        logger2.error("The search is broken")
                        logger2.error("We will use fake Q because "
                                      "of that error to keep plants alive")
                        fake_q = -1000  # TODO fix that
                        q = fake_q
                        f = fake_q
                    # then put results to current_search_table
                    self.current_search_table[self.current_search_point].result = q
                    self.current_search_table[self.current_search_point].raw_f = f

                    # then check if we do all current table
                    if self.current_search_point + 1 >= len(self.current_search_table):
                        # it means that we have collected all data for current step
                        # and we can start new search step
                        logger.info("update_state found that we can start new search step")
                        logger2.info("update_state found that we can start new search step")

                        # we have to write all old search table to special csv
                        # for simplification of the search visualization process later
                        for p in self.current_search_table:
                            rowdict = {
                                'date': time.strftime("%x", time.localtime()),
                                'time': time.strftime("%X", time.localtime()),
                                'x1': p.x1,
                                'x2': p.x2,
                                'Q': p.result,
                                'F': p.raw_f,
                                'step': self.current_search_step,
                                'label': p.name
                            }
                            logger.info("update_state search p = {}, x1 = {}, x2= {}, q = {}".format(
                                p.name, p.x1, p.x2, p.result
                            ))
                            logger2.info("update_state search p = {}, x1 = {}, x2= {}, q = {}".format(
                                p.name, p.x1, p.x2, p.result
                            ))
                            with open(self.search_method_log_path, "a") as f:
                                # f.write("{}".format(self.current_search_step))
                                writer = csv.DictWriter(f, delimiter=',', fieldnames=self.search_log_fields)
                                writer.writerow(rowdict)

                        # lets do search step
                        x1, x2 = self.search_method.do_search_step()
                        logger.info("update_state new x1 = {}, new x2 = {}".format(x1, x2))
                        logger2.info("update_state new x1 = {}, new x2 = {}".format(x1, x2))
                        # then lets calculate new search table
                        self.current_search_table = self.search_method.search_table
                        logger.info("update_state creates new search table")
                        logger2.info("update_state creates new search table")
                        for p in self.current_search_table:
                            logger.info("name = {} x1 = {} x2 = {}".format(
                                p.name, p.x1, p.x2
                            ))
                            logger2.info("name = {} x1 = {} x2 = {}".format(
                                p.name, p.x1, p.x2
                            ))

                        # then lets update counters
                        self.current_search_point = 0
                        self.current_search_step += 1
                        logger.info("update_state new search_point = {}".format(
                            self.current_search_point
                        ))
                        logger.info("update_state new search_step = {}".format(
                            self.current_search_step
                        ))
                        logger2.info("update_state new search_point = {}".format(
                            self.current_search_point
                        ))
                        logger2.info("update_state new search_step = {}".format(
                            self.current_search_step
                        ))
                        # then write number of new step to file
                        # logger.info("update_state Writing data to search steps config")
                        # with open(self.search_params_file, "w") as f:
                        #     f.write("{}".format(self.current_search_step))

                    else:
                        self.current_search_point += 1
                        logger.info("update_state new search_point = {}".format(
                            self.current_search_point
                        ))
                        logger2.info("update_state new search_point = {}".format(
                            self.current_search_point
                        ))

                    # its time to do measures for next search point from table
                    # at first find new far and r/w coordinates
                    new_far = self.current_search_table[self.current_search_point].x1
                    new_rw = self.current_search_table[self.current_search_point].x2
                    # then lets convert them to Ired and Iwhite
                    new_red, new_white = currents_from_newcoords(new_far, new_rw)
                    logger.info("update_state new red and white".format(
                        new_red, new_white
                    ))
                    logger2.info("update_state new red and white".format(
                        new_red, new_white
                    ))
                    # then create coro for measure new search point
                    reconfiguration_coro = SingleCoro(
                        self.reconfiguration,
                        "reconfiguration_task",
                        red=new_red,
                        white=new_white,
                        period=self.sleep_after_calibrations  # TODO: fix that thing somehow but with beauty
                    )
                    await reconfiguration_coro.start()

    async def reconfiguration(
            self,
            red,
            white,
            period  # seconds
    ):
        # TODO add try-except here in unit calls
        await self.calibration_lock.acquire()
        logger.info("Airflow and calibration started")
        self.current_comment = "ventilation"
        res = ""
        logger.info(await self.led_unit.set_current(red=int(red), white=int(white)))
        logger.info("New red and white currents is {} and {}".format(int(red), int(white)))
        logger.info(await self.gpio_unit.start_draining())
        # logger.info(await self.gpio_unit.start_ventilation())
        # TODO remove all worker calls from control system

        await self.worker.measure_task.stop()
        logger.info("self.gpio_unit.start_calibration")
        logger.info(await self.gpio_unit.start_calibration())
        logger.info(await self.co2_sensor_unit.do_calibration())
        await asyncio.sleep(self.calibration_time)
        logger.info(await self.gpio_unit.stop_calibration())
        await self.worker.measure_task.start()
        await asyncio.sleep(self.sleep_between_calibrations)
        await self.worker.measure_task.stop()
        logger.info(await self.gpio_unit.start_calibration())
        logger.info(await self.co2_sensor_unit.do_calibration())
        await asyncio.sleep(self.calibration_time)
        logger.info(await self.gpio_unit.stop_calibration())
        await self.worker.measure_task.start()
        await asyncio.sleep(period)
        # logger.info(await self.gpio_unit.stop_ventilation())
        logger.info(await self.gpio_unit.stop_draining())
        self.calibration_lock.release()
        self.current_comment = "measure"
        return res

    async def measure(self):
        logger.debug("measure")
        # TODO rewrite this function using dinamical list of unit names,
        #  or some list units to measure, that must be read from config

        date_ = time.strftime("%x", time.localtime())
        time_ = time.strftime("%X", time.localtime())

        try:
            ired, iwhite = await self.led_unit.get_short_info()
        except Exception as e:
            logger.error("Error in led wrapper connection, {}".format(e))
            raise
        try:
            temp, hum = await self.temp_sensor_unit.get_data()
        except Exception as e:
            logger.error("Error in temp and hum sensor connection, {}".format(e))
            raise
        try:
            co2_raw = await self.co2_sensor_unit.do_measurement()
            co2 = co2_raw.split(' ')[3]

        except Exception as e:
            logger.error("Error in SBA5 co2 sensor connection, {}".format(e))
            raise
        try:
            k30_co2 = await self.k30_unit.get_data()
        except Exception as e:
            logger.error("Error in K30 co2 sensor connection, {}".format(e))
            raise
        try:
            weight = await self.weight_unit.get_data()
        except Exception as e:
            # TODO its warning until we fix that annoying error with rpi gpio
            logger.warning("Error in weight sensor connection, {}".format(e))
            raise
        # find if it is ventilation now
        ventilation_is_now = False
        try:
            # add to one list all pins, connected to ventilation system
            vent_pins = self.gpio_unit.vent_pins
            vent_pins.extend(self.gpio_unit.drain_pump_pins)
            vent_pins.extend(self.gpio_unit.drain_valve_pins)
            state_of_pins = await self.gpio_unit.get_info()
        except Exception as e:
            logger.error("Error in gpio connection, {}".format(e))
            raise
        for vp in vent_pins:
            if state_of_pins[vp] is False:
                ventilation_is_now = True
                break
        if ventilation_is_now:
            air = 1
        else:
            air = 0
        step = self.current_search_step
        point = self.current_search_point
        fieldnames = self.data_fields
        # TODO shame on me, fix that, its magic numbers in the code
        data = {
            "date": date_,
            "time": time_,
            "Ired": ired,
            "Iwhite": iwhite,
            "temp": temp,
            "humid": hum,
            "CO2": co2,
            "weight": weight,
            "airflow": air,
            "K30CO2": k30_co2,
            "step": step,
            "point": point,
            "label": self.current_comment
        }

        self.data_handler.add_measure(data)

        # async with self.datafile_lock:
        #     with open(self.datafile, "a", newline='') as out_file:
        #         writer = csv.DictWriter(out_file, delimiter=',', fieldnames=fieldnames)
        #         writer.writerow(data)

        return data
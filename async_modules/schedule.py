import time
import logging
import asyncio
from typing import Any
import localconfig
from async_modules.tasks import SingleTask, LongSingleTask, PeriodicCoro, SingleCoro
import csv

logger = logging.getLogger("Worker.Schedule")

class Schedule:
    """
    This is schedule object
    It rules all experimental things
    """
    def __init__(
            self,
            worker: Any = None, # TODO is this correct way or not
            config_path: str = "worker.config"
    ):
        self.loop = asyncio.get_event_loop()
        # read config
        config = localconfig.config
        config.read(config_path)
        self.worker = worker
        self.calibration_time = config.get('schedule', 'calibration_time')
        self.search_params_file = config.get('schedule', 'schedule_point_file')
        self.start_red = config.get('schedule', 'start_red')
        self.start_white = config.get('schedule', 'start_white')
        self.datafile = config.get('schedule', 'datafile')
        self.measure_period = config.get('schedule', 'measure_period')
        # default search parameters
        self.current_schedule_point = 0
        self.cycle = 0
        # find schedule_point_config and check it
        try:
            with open(self.search_params_file) as f:
                raw_data = f.read()
                data = raw_data.split(":")
                self.cycle = int(data[0])
                self.current_schedule_point = int(data[1])
                logger.info("Config file found, data loaded")
        except Exception as e:
            logger.error("Error while reading config: {}".format(e))
            logger.error("Creating new default config")
            with open(self.search_params_file, "w") as f:
                f.write("{}:{}".format(self.cycle, self.current_schedule_point))

        self.search_done = False
        self.search_lock = asyncio.Lock()
        self.datafile_lock = asyncio.Lock()
        self.calibration_lock = asyncio.Lock()

        # add units from worker
        self.system_unit = getattr(worker, 'system_unit')
        self.led_unit = getattr(worker, 'led_unit')
        self.co2_sensor_unit = getattr(worker, 'co2_sensor_unit')
        self.gpio_unit = getattr(worker, 'gpio_unit')
        self.weight_unit = getattr(worker, 'weight_unit')
        self.k30_unit = getattr(worker, 'k30_unit')
        self.temp_sensor_unit = getattr(worker, 'temp_sensor_unit')

    async def start(self):
        # start all things, those need to be done once
        await self.gpio_unit.start_coolers()
        # await self._gpio_unit.start_draining()
        await self.gpio_unit.stop_draining()
        await self.led_unit.set_current(red=self.start_red, white=self.start_white)
        # we have to start air pump 3 before all
        # pump3_pin = self._gpio_unit.measure_pins
        # for i in pump3_pin:
        #     await self._gpio_unit.set_pin(pin=i, state=False)

        # do async init for some units
        await self.co2_sensor_unit.init()  # for time

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

    async def check_schedule(self):
        logger.debug("check_schedule")
        # period = 30 # in mins
        period = self.measure_period  # in mins
        sched = [
            [10, 258, 10],  # 700, 0
            [10, 69, 10],  # 200, 0
            [10, 163, 10],  # 450, 0
            [166, 133, 10],  # 700, 1
            [46, 38, 10],  # 200, 1
            [106, 85, 10],  # 450, 1
            [199, 106, 10],  # 700, 1.5
            [56, 30, 10],  # 200, 1.5
            [128, 68, 10],  # 450, 1.5
            [166, 133, 10],  # 700, 1  ------------------- repeating
            [106, 85, 10],  # 450, 1
            [46, 38, 10],  # 200, 1
            [128, 68, 10],  # 450, 1.5
            [199, 106, 10],  # 700, 1.5
            [56, 30, 10],  # 200, 1.5
            [10, 258, 10],  # 700, 0
            [10, 163, 10],  # 450, 0
            [10, 69, 10]  # 200, 0
        ]
        # TODO: remove after end of transients research
        # sched = [
        #     [10, 258, 10],  # 700, 0
        #     [10, 163, 10],  # 450, 0
        #     [10, 258, 10],  # 700, 0
        #     [199, 106, 10],  # 700, 1.5
        #     [128, 68, 10],  # 450, 1.5
        #     [199, 106, 10],  # 700, 1.5
        #     [10, 258, 10],  # 700, 0
        #     [199, 106, 10],  # 700, 1.5
        #     [128, 68, 0],  # 450, 1.5
        #     [128, 68, 2],  # 450, 1.5
        #     [128, 68, 5],  # 450, 1.5
        #     [128, 68, 10],  # 450, 1.5
        #     [128, 68, 15],  # 450, 1.5
        #     [128, 68, 20]  # 450, 1.5
        # ]

        if not self.calibration_lock.locked():
            # TODO: find here the cause of mistake in numbering of data in csv file
            # mb it >=  ??? mb change to >
            if self.current_schedule_point >= len(sched):
                self.current_schedule_point = self.current_schedule_point % len(sched)
                self.cycle += 1
            t = time.localtime()
            if t.tm_min % period == 0:
                remake_coro = SingleCoro(
                    self.remake,
                    "recalibration_task",
                    red=sched[self.current_schedule_point][0],
                    white=sched[self.current_schedule_point][1],
                    period=sched[self.current_schedule_point][2]
                )
                await remake_coro.start()
                self.current_schedule_point += 1
                logger.info("Writing data to config")
                with open("current.config", "w") as f:
                    f.write("{}:{}".format(self.cycle, self.current_schedule_point))

            # TODO: remove after end of transients research
            # if t.tm_hour % 1 == 0 and t.tm_min == 11:
            #     remake_coro = SingleCoro(
            #         self.remake,
            #         "recalibration_task",
            #         red=sched[self.current_schedule_point][0],
            #         white=sched[self.current_schedule_point][1],
            #         period=sched[self.current_schedule_point][2]
            #     )
            #     await remake_coro.start()
            #     self.current_schedule_point += 1
            #     logger.info("Writing data to config")
            #     with open("current.config", "w") as f:
            #         f.write("{}:{}".format(self.cycle, self.current_schedule_point))
            # # TODO: remove after end of transients research
            # else:
            #     if t.tm_min % 20 == 0:
            #         simple_calibration_coro = SingleCoro(
            #             self.simple_calibration,
            #             "simple_calibration_task"
            #         )
            #         await simple_calibration_coro.start()

        # if self._search_lock.locked():
        #     self._search_lock.release()
        # self._search_done = True
        # # TODO: set max optimal current here

    async def simple_calibration(self):
        await self.calibration_lock.acquire()
        logger.info("Simple calibration started")
        res = ""
        await self.worker.measure_task.stop()
        res += await self.gpio_unit.start_calibration()
        res += await self.co2_sensor_unit.do_calibration()
        await asyncio.sleep(self.calibration_time)
        res += await self.gpio_unit.stop_calibration()
        await self.worker.measure_task.start()
        self.calibration_lock.release()
        return res

    async def remake(self, red: int, white: int, period: int):
        await self.calibration_lock.acquire()
        logger.info("Airflow and calibration started")
        res = ""
        res += await self.gpio_unit.start_draining()
        res += await self.led_unit.set_current(red=red, white=white)
        logger.info("New red and white currents is {} and {}".format(red, white))
        res += await self.gpio_unit.start_ventilation()
        await self.worker.measure_task.stop()
        res += await self.gpio_unit.start_calibration()
        res += await self.co2_sensor_unit.do_calibration()
        await asyncio.sleep(self.calibration_time)
        res += await self.gpio_unit.stop_calibration()
        await self.worker.measure_task.start()
        await asyncio.sleep(400)
        await self.worker.measure_task.stop()
        res += await self.gpio_unit.start_calibration()
        res += await self.co2_sensor_unit.do_calibration()
        await asyncio.sleep(self.calibration_time)
        res += await self.gpio_unit.stop_calibration()
        await self.worker.measure_task.start()
        await asyncio.sleep(period*60)
        res += await self.gpio_unit.stop_ventilation()

        # TODO: remove after end of transients research
        # res += await self._led_unit.set_current(red=red, white=white)
        res += await self.gpio_unit.stop_draining()
        logger.debug("Result of calibration coro : " + res)
        self.calibration_lock.release()
        return res

    async def measure(self):
        logger.debug("measure")
        # TODO: try to do this function with tickets and handle mechanism
        date_ = time.strftime("%x", time.localtime())
        time_ = time.strftime("%X", time.localtime())
        ired, iwhite = await self.led_unit.get_short_info()
        temp, hum = await self.temp_sensor_unit.get_data()
        co2_raw = await self.co2_sensor_unit.do_measurement()
        co2 = co2_raw.split(' ')[3]
        k30_co2 = await self.k30_unit.get_data()
        weight = await self.weight_unit.get_data()
        # TODO: fix that crutch - air might be set manually
        if self.calibration_lock.locked():
            air = 1
        else:
            air = 0
        cyc = self.cycle
        fieldnames = ["date", "time", "Ired", "Iwhite", "temp", "humid",
                      "CO2", "weight", "airflow", "cycle", "K30CO2"]
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
            "cycle": cyc,
            "K30CO2": k30_co2
        }
        async with self.datafile_lock:
            with open(self.datafile, "a", newline='') as out_file:
                writer = csv.DictWriter(out_file, delimiter=',', fieldnames=fieldnames)
                writer.writerow(data)

        return data
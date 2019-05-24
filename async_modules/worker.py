import time
import asyncio
import json
import csv
from uuid import uuid4
from contextlib import suppress
from network_modules.command import Command, Ticket
from async_modules.tasks import SingleTask, LongSingleTask, PeriodicCoro, SingleCoro
from network_modules.raw_client import command_request_ticket\
    , command_set_ticket_result
from colorama import init
from async_modules.units import SystemUnit, LedUnit, CO2SensorUnit, WeightUnit, TempSensorUnit, GpioUnit, K30Unit
import logging

logger = logging.getLogger("Worker._Worker")


class Schedule:
    # TODO: mb remove it or what
    """
    This is schedule object
    It must read config from disc and every time be able to put out
    current tasks for all units
    """
    def __init__(self, path: str = "/etc/farmer_schedule"):
        pass

    def get_current_tasks(self):
        pass

    def get_tasks(self, time_: time.struct_time):
        pass

    def add_commands(self, commands):
        pass

    def delete_commands(self, commands):
        pass

    def _read_config(self):
        pass

    def _write_config(self):
        pass


class Worker:
    """
    This is async manager for RPi
    It must communicate with local and remote servers
    And work with schedule object
    """
    def __init__(self, wid: int = None, host: str = '127.0.0.1', port: int = 8888):
        # do some init things
        # init units, test  connection with server and some other things
        self._id = wid if wid is not None else uuid4().int
        self._host = host
        self._port = port
        self._schedule = Schedule()
        self._main_loop_task = None
        self._started = False
        self._search_done = False
        self._tasks = []  # list with objects from tasks.py module
        self._tasks_lock = asyncio.Lock()
        self._new_tickets = []  # list with Ticket objects (or not?)
        self._new_tickets_lock = asyncio.Lock()
        self._at_work_tickets = []  # list with Ticket objects, those in work at some task
        self._at_work_tickets_lock = asyncio.Lock()
        self._done_tickets = []  # list with Ticket objects, those already done
        self._done_tickets_lock = asyncio.Lock()
        self._datafile = "data.csv"
        self._datafile_lock = asyncio.Lock()
        self._calibration_lock = asyncio.Lock()
        self._search_lock = asyncio.Lock()
        self.current_schedule_point = 0
        self.cycle = 0
        self._calibration_time = 45  # medium time of calibration, it simply hardcoded
        # append units
        self._units = [
            "system_unit",
            "led_unit",
            "gpio_unit",
            "weight_unit",
            "co2_sensor_unit",
            "temp_sensor_unit",
            "k30_unit"
        ]
        # create units
        self._system_unit = SystemUnit(worker=self)
        self._led_unit = LedUnit(
            devname="/dev/ttyUSB1"
        )
        self._k30_unit = K30Unit(
            devname="/dev/ttyUSB2"
        )
        self._gpio_unit = GpioUnit()
        self._co2_sensor_unit = CO2SensorUnit(devname="/dev/ttyUSB0")
        self._weight_unit = WeightUnit()
        self._temp_sensor_unit = TempSensorUnit()
        # create stubs for periodic tasks
        self.measure_task = None
        self.schedule_task = None
        self.request_task = None
        self.send_results_task = None

    async def start(self):
        logger.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        logger.info("New epoch started!")
        logger.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        # find config and check it
        try:
            with open("current.config") as f:
                raw_data = f.read()
                data = raw_data.split(":")
                self.cycle = int(data[0])
                self.current_schedule_point = int(data[1])
                logger.info("Config file found, data loaded")
        except Exception as e:
            logger.error("Error while reading config: {}".format(e))
            logger.error("Creating new default config")
            with open("current.config", "w") as f:
                f.write("{}:{}".format(self.cycle, self.current_schedule_point))

        # start all things, those need to be done once
        await self._gpio_unit.start_coolers()
        await self._gpio_unit.start_draining()
        await self._led_unit.set_current(red=10, white=10)
        # do async init for some units
        await self._co2_sensor_unit.init() # for time
        # that tasks is not user`s, so they not in self._tasks
        self._main_loop_task = asyncio.ensure_future(self._run_main_loop())
        # self.schedule_task = PeriodicCoro(self.check_schedule, 3, name="schedule_task")
        # # TODO: remove it in future
        # self.schedule_task = PeriodicCoro(self.passive_schedule, 3, name="schedule_task")
        self.schedule_task = PeriodicCoro(self.one_shot_schedule, 3, name="schedule_task")

        self.request_task = PeriodicCoro(self.check_server, 3, name="request_task")
        self.send_results_task = PeriodicCoro(self.send_results, 3, name="send_results_task")
        self.measure_task = PeriodicCoro(self.measure, 1, name="measure_task")
        await self.schedule_task.start()
        await self.request_task.start()
        await self.send_results_task.start()
        await self.measure_task.start()
        self._started = True
        logger.info("worker started")

    # manual commands
    # it crashes all architecture, but i dont know how to do without it

    async def stop(self):
        # stop all units and event loop
        await self._gpio_unit.stop()
        await self.schedule_task.stop()
        await self.request_task.stop()
        await self.send_results_task.stop()
        await self.measure_task.stop()
        self._main_loop_task.cancel()
        # TODO: mb add stopping led driver?
        self._started = False
        logger.info("MANUAL COMMAND: worker stopped")
        with suppress(asyncio.CancelledError):
            await self._main_loop_task


    async def pause(self):
        # stop scheduling and measurements
        if self._started:
            logger.info("MANUAL COMMAND: worker auto regime paused")
            await self.schedule_task.stop()
            await self.measure_task.stop()
            self._started = False

    async def continue_(self):
        # start scheduling and measurements
        if not self._started:
            logger.info("MANUAL COMMAND: worker auto regime continued")
            await self.schedule_task.start()
            await self.measure_task.start()
            self._started = True

    async def start_ventilation(self):
        # start ventilation forever
        logger.info("MANUAL COMMAND: start ventilation")
        res = ""
        res += await self._gpio_unit.start_ventilation()
        return res

    async def stop_ventilation(self):
        # stop ventilation
        logger.info("MANUAL COMMAND: stop ventilation")
        res = ""
        res += await self._gpio_unit.stop_ventilation()
        return res

    async def do_calibration(self):
        # do calibration once
        logger.info("MANUAL COMMAND: do calibration once")
        res = ""
        res += await self._gpio_unit.start_calibration()
        res += await self._co2_sensor_unit.do_calibration()
        await asyncio.sleep(self._calibration_time)
        res += await self._gpio_unit.stop_calibration()
        return res

    async def _run_main_loop(self):
        # TODO: mb here must be nothing, and we should put all things to another PeriodicCoro?
        while True:
            logger.debug("run_main_loop_task started!")
            # do main things in loop
            await asyncio.sleep(1)  # ???
            # create tasks for new tickets
            async with self._new_tickets_lock:
                for t in self._new_tickets:
                    # for some case put NOTDONEERROR to every new ticket
                    t.result = {"Error": "NotDoneReallyError"}
                    try:
                        await self.parse_ticket(t)
                    except Exception as e:
                        t.result = {"Error": e}
                        self._new_tickets.remove(t)
                        # TODO: check if it really works
                        logger.debug("Worker._run_main_loop_task is awaiting _done_tickets_lock!")
                        async with self._done_tickets_lock:
                            self._done_tickets.append(t)
                        logger.debug("Error {} while handling command in ticket {}".format(e, t.id))

            # start newly added tasks and remove done tasks
            async with self._tasks_lock:
                for nt in self._tasks:
                    if not nt.is_started:
                        await nt.start()
                    if isinstance(nt, (SingleTask, LongSingleTask, SingleCoro)):
                        if nt.done:
                            # do we need any logging for done tasks?
                            self._tasks.remove(nt)

            # check _at_work_tickets and if they have result - push them to _done_tickets
            async with self._at_work_tickets_lock:
                for t in self._at_work_tickets:
                    if t.result != {"Error": "NotDoneReallyError"}:
                        self._at_work_tickets.remove(t)
                        async with self._done_tickets_lock:
                            self._done_tickets.append(t)
            logger.debug("run_main_loop_task done")

    async def parse_ticket(self, tick: Ticket):
        # parse command and create task objects for them
        # and put ticket to self._at_work_tickets list
        new_task = None
        logger.debug("parse_ticket started!")
        com = Command(**tick.command)
        if com.unit not in self._units:
            raise ValueError("No such unit {}".format(com.unit))

        elif com.unit == "system_unit":
            new_task = await self._system_unit.handle_ticket(tick)

        elif com.unit == "led_unit":
            new_task = await self._led_unit.handle_ticket(tick)

        elif com.unit == "gpio_unit":
            new_task = await self._gpio_unit.handle_ticket(tick)

        elif com.unit == "weight_unit":
            new_task = await self._weight_unit.handle_ticket(tick)

        elif com.unit == "co2_sensor_unit":
            new_task = await self._co2_sensor_unit.handle_ticket(tick)

        elif com.unit == "temp_sensor_unit":
            new_task = await self._temp_sensor_unit.handle_ticket(tick)

        if new_task:
            logger.debug("parse_ticket is awaiting _tasks_lock!")
            async with self._tasks_lock:
                self._tasks.append(new_task)
            logger.debug("parse_ticket is awaiting _at_work_tickets_lock!")
            async with self._at_work_tickets_lock:
                self._at_work_tickets.append(tick)
            logger.debug("parse_ticket is not awaiting _new_tickets_lock!")
            # async with self._new_tickets_lock:
            self._new_tickets.remove(tick)
        logger.debug("parse_ticket done!")

    async def send_results(self):
        """
        read _done_tickets and send their data to server
        then remove them to archive
        :return:
        """
        # TODO: mb we have to send only N of available tickets, not all?
        logger.debug("send_results started")
        async with self._done_tickets_lock:
            for dt in self._done_tickets:
                # send request to server
                res = None
                try:
                    res = await command_set_ticket_result(
                        ticket_id=dt.id,
                        result=dt.result,
                        host=self._host,
                        port=self._port
                    )
                    logger.debug("send_results sending results for server")
                except Exception as e:
                    # TODO: what we have to do with this type errors? How to handle
                    logger.debug("send_results: Error while sending request to server: {}".format(e))

                if res:
                    # parse answer
                    answer = res # it is already Message object
                    if answer.header == "SUCCESS":
                        logger.debug("send_results: Answer header is: {}".format(answer.header))
                        # its ok, remove ticket and archive it
                        await self.archive_ticket(dt)
                        self._done_tickets.remove(dt)
                    else:
                        # something went wrong in server side
                        # for now we will remove tickets whatever
                        logger.debug("send_results: error on server{}".format(
                            answer.header+answer.body))
                        self._done_tickets.remove(dt)
                else:
                    # something went wrong in server side
                    # try to send this result again after
                    logger.debug("send_results: error on server")
                    # TODO: dont simple remove, fix that
                    self._done_tickets.remove(dt)
        logger.debug("send_results: done")

    async def archive_ticket(self, ticket: Ticket):
        """
        Put ticket to some log
        :return:
        """
        # TODO: do real archiving
        pass

    async def passive_schedule(self):
        """
        simple schedule with constant parameter
        :return:
        """
        logger.debug("Passive_schedule")
        # constant point [500, 1.5]
        red = 115
        white = 58

        period = 30 # mins

        if not self._calibration_lock.locked():
            t = time.localtime()
            if t.tm_min % period == 0:
                remake_coro = SingleCoro(
                    self.remake,
                    "recalibration_task",
                    red=red,
                    white=white
                )
                await remake_coro.start()

    async def check_schedule(self):
        """
        do read schedule
        and then put tasks to self.tickets[] (with lock)
        hehe, nope
        :return:
        """
        logger.debug("check_schedule")
        # period = 30 # in mins
        period = 45  # in mins
        sched = [
            [10, 258],  # 700, 0
            [10, 69],  # 200, 0
            [10, 163],  # 450, 0
            [166, 133],  # 700, 1
            [46, 38],  # 200, 1
            [106, 85],  # 450, 1
            [199, 106],  # 700, 1.5
            [56, 30],  # 200, 1.5
            [128, 68],  # 450, 1.5
            [166, 133],  # 700, 1  ------------------- repeating
            [106, 85],  # 450, 1
            [46, 38],  # 200, 1
            [128, 68],  # 450, 1.5
            [199, 106],  # 700, 1.5
            [56, 30],  # 200, 1.5
            [10, 258],  # 700, 0
            [10, 163],  # 450, 0
            [10, 69]  # 200, 0
        ]

        if not self._calibration_lock.locked():
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
                    period=15
                )
                await remake_coro.start()
                self.current_schedule_point += 1
                logger.info("Writing data to config")
                with open("current.config", "w") as f:
                    f.write("{}:{}".format(self.cycle, self.current_schedule_point))
        if self._search_lock.locked():
            self._search_lock.release()
        self._search_done = True

    async def one_shot_schedule(self):
        t = time.localtime()
        if not self._search_lock.locked():
            if t.tm_min == 0 and t.tm_hour == 1 or not self._search_done:
                self._search_lock.locked()
                one_shot_sched_coro = SingleCoro(
                    self.check_schedule,
                    "one_shot_sched_task"
                )
                await one_shot_sched_coro.start()

    async def remake(self, red: int, white: int, period: int):
        await self._calibration_lock.acquire()
        logger.info("Airflow and calibration started")
        res = ""
        res += await self._led_unit.set_current(red=red, white=white)
        logger.info("New red and white currents is {} and {}".format(red, white))
        res += await self._gpio_unit.start_ventilation()
        await self.measure_task.stop()
        res += await self._gpio_unit.start_calibration()
        res += await self._co2_sensor_unit.do_calibration()
        await asyncio.sleep(self._calibration_time)
        res += await self._gpio_unit.stop_calibration()
        await self.measure_task.start()
        await asyncio.sleep(400)
        await self.measure_task.stop()
        res += await self._gpio_unit.start_calibration()
        res += await self._co2_sensor_unit.do_calibration()
        await asyncio.sleep(self._calibration_time)
        res += await self._gpio_unit.stop_calibration()
        await self.measure_task.start()
        # TODO fix that please
        await asyncio.sleep(period*60)
        res += await self._gpio_unit.stop_ventilation()
        logger.debug("Result of calibration coro : " + res)

        self._calibration_lock.release()
        return res

    async def measure(self):
        """
        Get info from all sensors and write it to file
        :return: dict
        """
        logger.debug("measure")
        # TODO: try to do this function with tickets and handle mechanism
        date_ = time.strftime("%x", time.localtime())
        time_ = time.strftime("%X", time.localtime())
        ired, iwhite = await self._led_unit.get_short_info()
        temp, hum = await self._temp_sensor_unit.get_data()
        co2_raw = await self._co2_sensor_unit.do_measurement()
        co2 = co2_raw.split(' ')[3]
        k30_co2 = await self._k30_unit.get_data()
        weight = await self._weight_unit.get_data()
        if self._calibration_lock.locked():
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
        async with self._datafile_lock:
            with open(self._datafile, "a", newline='') as out_file:
                writer = csv.DictWriter(out_file, delimiter=',', fieldnames=fieldnames)
                writer.writerow(data)

        return data

    async def check_server(self):
        """
        do send request to server, parse answer and put tasks to self.tickets
        (with lock just in case)
        :return:
        """
        # send request to server
        logger.debug("check_server: started")
        res = None
        try:
            res = await command_request_ticket(
                worker_id=self._id,
                host=self._host,
                port=self._port
            )
            logger.debug("check_server: sent request")
        except Exception as e:
            # TODO: what we have to do with this type errors? How to handle
            logger.debug("check_server: Error while sending request to server: {}".format(e))

        if res:
            logger.debug("check_server: parsing answer")
            # parse answer
            answer = res # its already Message object
            dicts_list = json.loads(answer.body)
            # TODO: remove useless print and do something useful
            # print(answer.header)
            tickets_list = [Ticket(**t_dict) for t_dict in dicts_list]
            # add tickets from answer to list
            async with self._new_tickets_lock:
                for t in tickets_list:
                    # TODO: remove useless print and do something useful
                    logger.debug(t.id, t.to, t.tfrom)
                    self._new_tickets.append(t)
            logger.debug("check_server: done")


async def non_rpi_main(
        wid=155167253286217647024261323245457212920,
        host="83.220.174.247",
        port=8888
):
    init(autoreset=True)
    # example uuid wid=155167253286217647024261323245457212920
    # server host 83.220.174.247:8888
    worker = Worker(wid=wid, host=host, port=port)
    await worker.start()

if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.run_until_complete(non_rpi_main())
    loop.run_forever()


async def main(
        wid=155167253286217647024261323245457212920,
        host="83.220.174.247",
        port=8888
):
    init(autoreset=True)
    # example uuid wid=155167253286217647024261323245457212920
    # server host 83.220.174.247:8888
    worker = Worker(wid=wid, host=host, port=port)
    await worker.start()
import asyncio
import json

from network_modules.command import Command, Ticket
from async_modules.tasks import SingleTask, LongSingleTask, PeriodicCoro, SingleCoro
from network_modules.raw_client import command_request_ticket\
    , command_set_ticket_result
import async_modules.units as units
import logging
import sys
import localconfig
from async_modules.control_system import ControlSystem

logger = None


class Worker:
    """
    This is async manager for RPi
    It must communicate with local and remote servers
    And work with schedule object
    """
    def __init__(
            self,
            config_path: str = "worker.conf"
    ):
        # do some init things
        # init units, test  connection with server and some other things

        # at first parse config

        config = localconfig.config
        config.read(config_path)

        # create logger
        global logger
        self.debug_mode = config.get('worker', 'debug_mode')
        logger = logging.getLogger("Worker")
        if self.debug_mode:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
        # create the logging file handler
        fh = logging.FileHandler("worker.log")
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        # add handler to logger object
        logger.addHandler(fh)

        # worker parameters
        self._id = config.get('worker', 'worker_id')
        self._host = config.get('network', 'host')
        self._port = config.get('network', 'port')

        # parameters for db session
        self._session_id = config.get('session', 'session_id')
        self._session_descr = config.get('session', 'session_description')
        self._main_loop_task = None
        self._started = False
        # time parameters for tasks
        self.schedule_period = config.get('worker', 'schedule_period')
        self.request_period = config.get('worker', 'request_period')
        self.send_period = config.get('worker', 'send_period')
        self.measure_period = config.get('worker', 'measure_period')
        # tasks and locks
        self._tasks = []  # list with objects from tasks.py module
        self._tasks_lock = asyncio.Lock()
        self._new_tickets = []  # list with Ticket objects (or not?)
        self._new_tickets_lock = asyncio.Lock()
        self._at_work_tickets = []  # list with Ticket objects, those in work at some task
        self._at_work_tickets_lock = asyncio.Lock()
        self._done_tickets = []  # list with Ticket objects, those already done
        self._done_tickets_lock = asyncio.Lock()

        # append units
        # read list list_of_available_units from units.py
        # go through it and find if some unit name is in config
        # then add it and create its object with parameters from config
        # then dynamically add it to self attributes
        units_units = units.list_of_available_units
        self._unitnames = []
        logger.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        logger.info("New epoch started!")
        logger.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

        # here is dynamical loading loading units
        # its not simple to understand that painful thing
        for u in units_units:
            if u[0] in config and config.get(u[0], 'use') is True:
                self._unitnames.append(u[0])
                kwargs = dict(config.items(u[0]))
                kwargs.pop('use')  # we dont need that key as argument of unit
                unit_obj = getattr(units, u[1])
                setattr(self, u[0], unit_obj(**kwargs))
                logger.debug("{} added to worker".format(u[0]))

        # system unit not in config because we always use it
        # so we have to add it manually
        self.system_unit = units.SystemUnit(worker=self)
        self._unitnames.append('system_unit')
        logger.debug("system_unit added to worker")

        # create stubs for periodic tasks
        self.measure_task = None
        self.schedule_task = None
        self.request_task = None
        self.send_results_task = None

        # add ControlSystem
        self._search_system = ControlSystem(
            worker=self,
            config_path=config_path
        )

    async def start(self):
        logger.debug("start worker coroutine")
        # all unit things must be handled by schedule object
        await self._search_system.start()
        # then create periodic tasks
        self._main_loop_task = asyncio.ensure_future(self._run_main_loop())
        self.schedule_task = PeriodicCoro(
            self.check_search_system,
            self.schedule_period,
            name="schedule_task"
        )
        self.request_task = PeriodicCoro(
            self.check_server,
            self.request_period,
            name="request_task"
        )
        self.send_results_task = PeriodicCoro(
            self.send_results,
            self.send_period,
            name="send_results_task"
        )
        self.measure_task = PeriodicCoro(
            self.measure,
            self.measure_period,
            name="measure_task"
        )
        await self.schedule_task.start()
        await self.request_task.start()
        await self.send_results_task.start()
        await self.measure_task.start()
        self._started = True
        logger.info("worker totally started")

    # manual commands
    # it crashes all architecture, but i dont know how to do without it

    async def stop(self):
        # stop all units and event loop
        # shedule object must handle it
        await self._search_system.stop()
        # then stop tasks
        await self.schedule_task.stop()
        await self.request_task.stop()
        await self.send_results_task.stop()
        await self.measure_task.stop()
        self._main_loop_task.cancel()
        self._started = False
        logger.info("MANUAL COMMAND: worker stopped")
        # TODO: its too rude
        sys.exit()
        # with suppress(asyncio.CancelledError):
        #     await self._main_loop_task

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
        return await self._search_system.start_ventilation()

    async def stop_ventilation(self):
        # stop ventilation
        logger.info("MANUAL COMMAND: stop ventilation")
        return await self._search_system.stop_ventilation()

    async def do_calibration(self):
        # do calibration once
        logger.info("MANUAL COMMAND: do calibration once")
        return await self._search_system.do_calibration()

    async def do_reconfiguration(self):
        logger.info("MANUAL COMMAND: do reconfiguration")
        return await self._search_system.manual_reconfiguration()

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
        if com.unit not in self._unitnames:
            raise ValueError("No such unit {}".format(com.unit))
        # checking what unit it is
        for u in self._unitnames:
            if u == com.unit:
                unit_obj = getattr(self, u)
                new_task = await unit_obj.handle_ticket(tick)
        # add new task in list to handle
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
                    answer = res  # it is already Message object
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

    async def check_search_system(self):
        """
        do read schedule
        and then put tasks to self.tickets[] (with lock)
        hehe, nope
        :return:
        """
        await self._search_system.update_state()

    async def measure(self):
        """
        Get info from all sensors and write it to file
        """
        await self._search_system.measure()

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
                    logger.debug(t.id, t.to, t.tfrom)
                    self._new_tickets.append(t)
            logger.debug("check_server: done")


async def main():
    # example uuid wid=155167253286217647024261323245457212920
    # server host 83.220.174.247:8888
    worker = Worker(config_path='worker.conf')
    await worker.start()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()
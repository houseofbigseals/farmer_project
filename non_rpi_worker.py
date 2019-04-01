# This is async manager for RPi, that should do following things:
#
# Receive data:
# - read T and H from DHT11
# - read CO2 concentration from SBA5
# - read weight from weight sensor
# - read data from some other sensor
# - read data from schedule file on the drive
#
# Send data:
# - send uart commands to GIC for control LED lamp
# - send uart commands to SBA5
# - set GPIO on and off to control valves, pumps and other relay things
# - send heartbeat http requests to remote internet server and parse answers to
# provide the opportunity of remove control through internet
# - send heartbeat http requests to local server and parse answers to
# provide the opportunity of remove control in local network
# - write logs to file in a disk
#
# The main idea of realization is to use asyncio, because processes,
# that we need to control, are very slow, but we need to control them with very
# high stability and noise immunity. Also we need to remotely control them.
#
# All periphery should be wrapped as a unit object
# Basically - unit is a async wrapper for a bunch of low-level methods, those
# have to work together by some logic
# Unit is async and should be able to async wrap all appropriate periphery methods
#
# What is the schedule
# Schedule is a class that keep commands for units for each time moment
# It can be modified in work, for example if we get appropriate command from server
# Schedule has as file on a drive, in which it saves all modifications
#
# How it will work:
# - We send request to remote server and parse output
# output is a command that we have to write to a schedule
# - We send request to local server and parse output
# output is a command that we have to write to a schedule
# - We read current commands from schedule
# - We asynchronously start to do that commands
# - And with all commands we do "await 1 sec command" that is our time quantum
# If something not done after one second, i dont know to waht to do
#
# What is the format of the communication with the server:
# 1. RPi request - heartbeat once a second
# 2. Server response with command (or list of commands)
# Command is a json, parsed from response body
# It has four fields
# Unit: <Some_unit>
# Task: <Some_task_for_this_unit>
# Time: <Time_interval_to_start_that_task>
# Priority: <1 is the highest, 5 is the lowest>
#
# A task can take a long time to complete.
# When unit says to manager that task is done (or there is some error with taht task)
# Manager sends that request
#
# 3. RPi request with result of execution of command
# Its json too and it has five fields
# Unit: <Some_unit>
# Task: <Some_task_for_this_unit>
# Time: <Time_when_that_task_was_finished>
# Priority: <1 is the highest, 5 is the lowest>
# Result: <Result or error state>
#
# 4. Server response with command (or list of commands) again
#
# List of units with their tasks
#
# All units have following methods:
# - get_last_task_status - result of last done operation
# - get_list_of_methods - send list of all available methods for this unit
# - get_unit_status - there might be some info about current unit state
# All units can override this methods according with their essence
#
# 1. system_unit
# - reset_RPi - carefully stop all systems and reset RPi through systemctl
# - do_nothind - its server answer if server doesnt need anything from RPi
# - list_of_units - send list of units to server
# - get_log - send log to server
# - get_schedule - send schedule file to server
#
# 2. LED_unit
# - set Red and White currents
# - start GIC
# - stop GIC
# - set_new_profile
# - get_current_profile
#
# 3. ventilation_unit
# - set_relay_N_on
# - set_relay_N_off
# - passively_open_system
# - passively_close_system
# - start_ventilation
# - stop_ventilation
#
# 4. weight_unit
# - get_current_mass
#
# 5. GA_unit
# - get_current_CO2_concentration
# - get_current_settings
# - set_new_settings
# - start_adjustment
#
# 6. temp_sensor_unit
# - get_temp_and_humidity
#
#

import time
import asyncio
import json
from led_uart_wrapper import UartWrapper
# from dht_wrapper import DHTWrapper  # it works only on raspberry
from uuid import uuid4, UUID
from typing import Any
from contextlib import suppress
from command import Message, Command, Ticket
from tasks import PeriodicTask, SingleTask, LongSingleTask, PeriodicCoro, SingleCoro
from pseudo_client import command_get_server_info, command_request_ticket\
    , command_set_ticket_result
from colorama import Back, init


class Unit(object):
    """
    Simple prototype for unit object
    """
    def __init__(self):
        # self.last_operation_status = None
        self.status = None
        pass

    def get_unit_status(self) -> None:
        """
        There must be that logic:
        firstly check how it is
        and then return state, as example OK or SOME_ERROR
        """
        pass

    def get_list_of_methods(self) -> None:
        """
        We have to return a list of public methods
        Do not use dir() or hasattr(module_name, "attr_name") or inspect.getmembers
        Only hand-written list of safe public methods to use remotely
        """
        pass

    # def get_last_task_status(self) -> None:
    #     """
    #     Returns status of last operation
    #     """
    #     pass


class LedUnit(Unit):
    """
    Unit for control led through Impulse Current Generator methods wrapping
    """
    def __init__(self):
        super(LedUnit, self).__init__()
        self._list_of_methods = ["get_info"]
        pass

    async def _get_info(self):
        return await asyncio.create_subprocess_shell("uname -a")

    async def handle_ticket(self, tick: Ticket):
        command = Command(**tick.command)
        if command in self._list_of_methods:
            if command == "get_info":
                return await self._get_info()
        else:
            raise ValueError("LedUnitError: No such command - {}".format(command.func))


class CO2SensorUnit(Unit):
    """
    Unit for CO2Sensor methods wrapping
    """
    def __init__(self):
        super(CO2SensorUnit, self).__init__()
        self._list_of_methods = ["get_info"]
        pass

    async def _get_info(self):
        return await asyncio.create_subprocess_shell("uname -a")

    async def handle_ticket(self, tick: Ticket):
        command = Command(**tick.command)
        if command in self._list_of_methods:
            if command == "get_info":
                return await self._get_info()
        else:
            raise ValueError("CO2SensorUnitError: No such command - {}".format(command.func))


class VentilationUnit(Unit):
    """
    Unit for correct gpio calls wrapping
    """
    def __init__(self):
        super(VentilationUnit, self).__init__()
        self._list_of_methods = ["get_info"]
        pass

    async def _get_info(self):
        return await asyncio.create_subprocess_shell("uname -a")

    async def handle_ticket(self, tick: Ticket):
        command = Command(**tick.command)
        if command in self._list_of_methods:
            if command == "get_info":
                return await self._get_info()
        else:
            raise ValueError("VentilationUnitError: No such command - {}".format(command.func))


class WeightUnit(Unit):
    """
    Unit for wrapping weight sensor (HX711 ?) methods
    """
    def __init__(self):
        super(WeightUnit, self).__init__()
        self._list_of_methods = ["get_info"]
        pass

    async def _get_info(self):
        return await asyncio.create_subprocess_shell("uname -a")

    async def handle_ticket(self, tick: Ticket):
        command = Command(**tick.command)
        if command in self._list_of_methods:
            if command == "get_info":
                return await self._get_info()
        else:
            raise ValueError("WeightUnitError: No such command - {}".format(command.func))


class TempSensorUnit(Unit):
    """
    Unit for wrapping temp sensor methods - dht11 for now
    """
    def __init__(self):
        super(TempSensorUnit, self).__init__()
        self._list_of_methods = ["get_info"]
        pass

    async def _get_info(self):
        return await asyncio.create_subprocess_shell("uname -a")

    async def handle_ticket(self, tick: Ticket):
        command = Command(**tick.command)
        if command.func in self._list_of_methods:
            if command.func == "get_info":
                return await self._get_info()
        else:
            raise ValueError("TempSensorUnitError: No such command - {}".format(command.func))


class SystemUnit(Unit):
    """
    Unit for all needs, that are not related with real fitostand objects like valves
    pumps, leds and other
    """
    def __init__(self):
        super(SystemUnit, self).__init__()
        self._list_of_methods = ["get_info"]

    async def _get_info(self, tick: Ticket):
        print(Back.CYAN+ "SystemUnit.SystemUnit.get_info_task started!")
        proc = await asyncio.create_subprocess_shell("uname -a", stdout=asyncio.subprocess.PIPE)

        def strip(x):
            return x.strip()
        stdout, stderr = await proc.communicate()
        content = stdout.decode().strip()
        tick.result = content
        print(Back.CYAN+"SystemUnit.SystemUnit.get_info_task done!")

    async def handle_ticket(self, tick: Ticket):
        print(Back.CYAN+"SystemUnit.handle_ticket started!")
        command = Command(**tick.command)
        if command.func in self._list_of_methods:
            print(Back.CYAN + "SystemUnit.handle_ticket command.func in self._list_of_methods!")
            if command.func == "get_info":
                new_single_coro = SingleCoro(self._get_info, "SystemUnit.get_info_task", tick)
                print(Back.CYAN + "SystemUnit.handle_ticket created coro!")
                return new_single_coro
        else:
            raise ValueError("SystemUnitError: No such command - {}".format(command.func))
        print(Back.CYAN+"SystemUnit.handle_ticket done!")


class Schedule:
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
    def __init__(self, wid: int = uuid4().int, host: str = '127.0.0.1', port: int = 8888):
        # do some init things
        # init units, test  connection with server and some other things
        self._id = wid
        self._host = host
        self._port = port
        self._schedule = Schedule()
        self._main_loop_task = None
        self._tasks = []  # list with objects from tasks.py module
        self._tasks_lock = asyncio.Lock()
        self._new_tickets = []  # list with Ticket objects (or not?)
        self._new_tickets_lock = asyncio.Lock()
        self._at_work_tickets = [] # list with Ticket objects, those in work at some task
        self._at_work_tickets_lock = asyncio.Lock()
        self._done_tickets = [] # list with Ticket objects, those already done
        self._done_tickets_lock = asyncio.Lock()
        # append units
        self._units = [
            "system_unit",
            "led_unit",
            "ventilation_unit",
            "weight_unit",
            "co2_sensor_unit",
            "temp_sensor_unit"
        ]
        self._system_unit = SystemUnit()
        self._led_unit = LedUnit()
        self._ventilation_unit = VentilationUnit()
        self._co2_sensor_unit = CO2SensorUnit()
        self._weight_unit = WeightUnit()
        self._temp_sensor_unit = TempSensorUnit()

    async def start(self):
        # that tasks is not user`s, so they not in self._tasks
        self._main_loop_task = asyncio.ensure_future(self._run_main_loop())
        schedule_task = PeriodicCoro(self.check_schedule, 5, name="schedule_task")
        request_task = PeriodicCoro(self.check_server, 5, name="request_task")
        send_results_task = PeriodicCoro(self.send_results, 5, name="send_results_task")
        await schedule_task.start()
        await request_task.start()
        await send_results_task.start()

    async def stop(self):
        self._main_loop_task.cancel()
        with suppress(asyncio.CancelledError):
            await self._main_loop_task

    async def _run_main_loop(self):
        # TODO: mb here must be nothing, and we should put all things to another PeriodicCoro?
        while True:
            print(Back.RED+"{} at work !".format("Worker._run_main_loop_task"))
            print(Back.RED+"Worker._run_main_loop_task started!")
            # do main things in loop
            await asyncio.sleep(1)  # ???
            print(Back.RED+"Worker._run_main_loop_task is awaiting _new_tickets_lock!")
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
                        print(Back.RED+"Worker._run_main_loop_task is awaiting _done_tickets_lock!")
                        async with self._done_tickets_lock:
                            self._done_tickets.append(t)
                        print(Back.RED+"Error {} while handling command in ticket {}".format(e, t.id))

            # start newly added tasks and remove done tasks
            print(Back.RED+"Worker._run_main_loop_task is awaiting _tasks_lock!")
            async with self._tasks_lock:
                for nt in self._tasks:
                    if not nt.is_started:
                        await nt.start()
                    if isinstance(nt, (SingleTask, LongSingleTask, SingleCoro)):
                        if nt.done:
                            # do we need any logging for done tasks?
                            self._tasks.remove(nt)

            # check _at_work_tickets and if they have result - push them to _done_tickets
            print(Back.RED+"Worker._run_main_loop_task is awaiting _at_work_tickets_lock!")
            async with self._at_work_tickets_lock:
                for t in self._at_work_tickets:
                    if t.result != {"Error": "NotDoneReallyError"}:
                        self._at_work_tickets.remove(t)
                        async with self._done_tickets_lock:
                            self._done_tickets.append(t)

    async def parse_ticket(self, tick: Ticket):
        # parse command and create task objects for them
        # and put ticket to self._at_work_tickets list
        new_task = None
        print(Back.GREEN+"parse_ticket started!")
        com = Command(**tick.command)
        if com.unit not in self._units:
            raise ValueError("No such unit {}".format(com.unit))

        elif com.unit == "system_unit":
            new_task = await self._system_unit.handle_ticket(tick)

        elif com.unit == "led_unit":
            new_task = await self._led_unit.handle_ticket(tick)

        elif com.unit == "ventilation_unit":
            new_task = await self._ventilation_unit.handle_ticket(tick)

        elif com.unit == "weight_unit":
            new_task = await self._weight_unit.handle_ticket(tick)

        elif com.unit == "co2_sensor_unit":
            new_task = await self._co2_sensor_unit.handle_ticket(tick)

        elif com.unit == "temp_sensor_unit":
            new_task = await self._temp_sensor_unit.handle_ticket(tick)

        if new_task:
            print(Back.GREEN+"parse_ticket is awaiting _tasks_lock!")
            async with self._tasks_lock:
                self._tasks.append(new_task)
            print(Back.GREEN+"parse_ticket is awaiting _at_work_tickets_lock!")
            async with self._at_work_tickets_lock:
                self._at_work_tickets.append(tick)
            print(Back.GREEN+"parse_ticket is not awaiting _new_tickets_lock!")
            # async with self._new_tickets_lock:
            self._new_tickets.remove(tick)
        print(Back.GREEN+"parse_ticket done!")

    async def send_results(self):
        """
        read _done_tickets and send their data to server
        then remove them to archive
        :return:
        """
        # TODO: mb we have to send only N of available tickets, not all?
        print(Back.MAGENTA + "send_results started")
        print(Back.MAGENTA + "send_results is awaiting _done_tickets_lock")
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
                    print(Back.MAGENTA + "send_results sending results for server")
                except Exception as e:
                    # TODO: what we have to do with this type errors? How to handle
                    print(Back.MAGENTA + "Error while sending request to server: {}".format(e))

                if res:
                    # parse answer
                    answer = res # it is already Message object
                    if answer.header == "SUCCESS":
                        print(Back.MAGENTA + "send_results parsing answer")
                        print("Answer header is: ", answer.header)
                        # its ok, remove ticket and archive it
                        await self.archive_ticket(dt)
                        print(Back.MAGENTA + "send_results removing sent ticket")
                        self._done_tickets.remove(dt)
                else:
                    # something went wrong in server side
                    # try to send this result again after
                    # so do nothing (or not?)
                    print(Back.MAGENTA + "send_results not removing ticket")
                    pass
        print(Back.MAGENTA + "send_results done")

    async def archive_ticket(self, ticket: Ticket):
        """
        Put ticket to some log
        :return:
        """
        # TODO: do real logging
        pass

    async def check_schedule(self):
        """
        do read schedule
        and then put tasks to self.tickets[] (with lock)
        :return:
        """
        # TODO: do real schedule reading
        pass

    async def check_server(self):
        """
        do send request to server, parse answer and put tasks to self.tickets
        (with lock just in case)
        :return:
        """
        # send request to server
        print(Back.BLUE+"check_server started!")
        res = None
        try:
            res = await command_request_ticket(
                worker_id=self._id,
                host=self._host,
                port=self._port
            )
            print(Back.BLUE+"check_server send reqv!")
        except Exception as e:
            # TODO: what we have to do with this type errors? How to handle
            print(Back.BLUE+"Error while sending request to server: {}".format(e))

        if res:
            print(Back.BLUE+"check_server parsing answer!")
            # parse answer
            answer = res # its already Message object
            dicts_list = json.loads(answer.body)
            # TODO: remove useless print and do something useful
            print(answer.header)
            tickets_list = [Ticket(**t_dict) for t_dict in dicts_list]
            # add tickets from answer to list
            print(Back.BLUE+"check_server waiting for _new_tickets_lock!")
            async with self._new_tickets_lock:
                for t in tickets_list:
                    # TODO: remove useless print and do something useful
                    print(t.id, t.to, t.tfrom)
                    self._new_tickets.append(t)
            print(Back.BLUE+"check_server done!")


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
    # BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET
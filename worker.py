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
from dht_wrapper import DHTWrapper
from uuid import uuid4, UUID
from typing import Any
from contextlib import suppress
from command import Message, Command, Ticket
from tasks import PeriodicTask, SingleTask, LongSingleTask, PeriodicCoro
from pseudo_client import command_get_server_info, command_request_ticket\
    , command_set_ticket_result


class Unit:
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


class LEDUnit(Unit):
    pass


class SystemUnit(Unit):
    """
    Unit for all needs, that are not related with real fitostand objects like valves
    pumps and leds
    """
    def __init__(self):
        super(SystemUnit, self).__init__()
        self._list_of_methods = ["get_info"]
        pass

    async def _get_info(self):
        return await asyncio.create_subprocess_shell("uname -a")

    async def handle_command(self, command: str):
        if command in self._list_of_methods:
            if command == "get_info":
                return await self._get_info()


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
    def __init__(self, wid: int = uuid4().int, host: str = '127.0.0.1', port : int = 8888):
        # do some init things
        # init units, test  connection with server and some other things
        self._id = wid
        self._host = host
        self._port = port
        self._system_unit = SystemUnit()
        self._led_unit = LEDUnit()
        self._schedule = Schedule()
        self._main_loop_task = None
        self._tasks = []  # list with objects from tasks.py module
        self._tickets = []  # list with Ticket objects (or not?)
        self._tickets_lock = asyncio.Lock()

    async def start(self):
        self._main_loop_task = asyncio.ensure_future(self._run_main_loop())
        schedule_task = PeriodicCoro(self.check_schedule, 5)
        request_task = PeriodicCoro(self.check_server, 5)
        await schedule_task.start()
        await request_task.start()

    async def stop(self):
        self._main_loop_task.cancel()
        with suppress(asyncio.CancelledError):
            await self._main_loop_task

    async def _run_main_loop(self):

        while True:
            # do main things in loop
            #
            # read self._tickets and if there no "in_work" or some data
            # create new task for correct unit and put str "in_work" to result
            await asyncio.sleep(0.5)
            async with self._tickets_lock:
                for t in self._tickets:
                    # find newly added tickets
                    if not t.result:
                        try:
                            com = Command(**t.command)
                            self.parse_command(com)
                        except Exception as e:
                            # TODO: continue from here
                            pass
                pass

    def check_schedule(self):
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
        res = None
        try:
            res = await command_request_ticket(
                worker_id=self._id,
                host=self._host,
                port=self._port
            )
        except Exception as e:
            # TODO: what we have to do with this type errors? How to handle
            print("Error while sending request to server: {}".format(e))

        if res:
            # parse answer
            answer = Message(**json.loads(res))
            dicts_list = json.loads(answer.body)
            # TODO: remove useless print and do something useful
            print(answer.header)
            tickets_list = [Ticket(**t_dict) for t_dict in dicts_list]
            # TODO: check what will happen if answer contains empty list
            # add tickes from answer to list
            async with self._tickets_lock:
                for t in tickets_list:
                    # TODO: remove useless print and do something useful
                    print(t.id, t.to, t.tfrom)
                    self._tickets.append(t)
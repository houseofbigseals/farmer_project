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
# - send uart commands to GIS for control LED lamp
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
# 1. system_unit
# - reset_RPi - carefully stop all systems and reset RPi through systemctl
# - do_nothind - its server answer if server doesnt need anything from RPi
# - list_of_units - send list of units to server
# - get_log - send log to server
# - get_schedule - send schedule file to server

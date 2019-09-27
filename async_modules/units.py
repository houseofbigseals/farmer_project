# units - async wrappers for low-level objects

import asyncio
from low_level_modules.led_uart_wrapper import UartWrapper
from network_modules.command import Command, Ticket
from async_modules.tasks import SingleCoro
from low_level_modules.sba5_wrapper import SBAWrapper
from low_level_modules.k30_wrapper import K30
from low_level_modules.ard_wrapper import ArdWrapper
from typing import Any
import logging

logger = logging.getLogger("Worker.Units")
platf = None
try:
    # platform dependent modules
    # they work correctly only on raspberry
    from low_level_modules.dht_wrapper import DHTWrapper
    from low_level_modules.gpio_wrapper import GPIOWrapper
    from low_level_modules.hx_wrapper import HX711Wrapper
    platf = "RPi"
except ImportError:
    logger.info("Looks like we are not on RPi")
    platf = "PC"


# list with pairs of real class names and their names in worker
list_of_available_units = [
    ('led_unit', 'LedUnit'),
    ('ard_unit', 'ArdUnit'),
    ('co2_sensor_unit', 'CO2SensorUnit'),
    ('gpio_unit', 'GpioUnit'),
    ('weight_unit', 'WeightUnit'),
    ('k30_unit', 'K30Unit'),
    ('temp_sensor_unit', 'TempSensorUnit'),
    ('system_unit', 'SystemUnit')
]

class Unit(object):
    """
    Simple prototype for unit object
    """

    def __init__(self, name: str = None):
        self._name = name
        pass

    def get_list_of_methods(self) -> None:
        """
        We have to return a list of public methods
        Do not use dir() or hasattr(module_name, "attr_name") or inspect.getmembers
        Only hand-written list of safe public methods to use remotely
        """
        pass

    @property
    def name(self):
        return self._name


class LedUnit(Unit):
    """
    Unit for control led through Impulse Current Generator methods wrapping
    """

    def __init__(
            self,
            devname: str = '/dev/ttyUSB0',  # in rpi and ubunty ttyUSB0 or ttyUSBn
            baudrate: int = 19200,
            timeout: int = 10
    ):

        super(LedUnit, self).__init__(name="led_unit")
        self._list_of_methods = [
            "get_info",
            "start",
            "stop",
            "set_current"
        ]
        self.devname = devname
        self.baudrate = baudrate
        self.timeout = timeout

        self.uart_wrapper = UartWrapper(
            devname=self.devname,
            baudrate=self.baudrate,
            timeout=self.timeout
        )
        self._started = False
        self._red = 10
        self._white = 10
        self.logger = logging.getLogger("Worker.Units.Led_wrapper")

    async def get_short_info(self):
        return self._red, self._white

    async def get_info(self, tick: Ticket = None):
        self.logger.info(
            "Info. Unit {}, red current = {}, white current = {}".format(
                "started" if self._started else "stopped", self._red, self._white)
        )
        res = self.uart_wrapper.GET_STATUS()[1]
        self.logger.debug(res)
        if tick:
            tick.result = res
        else:
            return res

    async def start(self, tick: Ticket = None):
        self._started = True
        self.logger.info("Started")
        res = self.uart_wrapper.START()[1]
        self.logger.debug(res)
        if tick:
            tick.result = res
        else:
            return res

    async def stop(self, tick: Ticket = None):
        self._started = False
        self.logger.info("Stopped")
        res = self.uart_wrapper.STOP()[1]
        self.logger.debug(res)
        if tick:
            tick.result = res
        else:
            return res

    async def set_current(self, tick: Ticket = None, red = 10, white = 10):
        self._red = int(red)
        self._white = int(white)
        # TODO: handle incorrect current values such as (10000, 0) or smth
        self.logger.info("Trying to set red current to {}, white - to {}".format(red, white))
        res = "sorry, results in log"
        # TODO : think about what send back to user as result
        self.logger.info(self.uart_wrapper.STOP()[1])
        self.logger.info(self.uart_wrapper.START_CONFIGURE()[1])
        self.logger.info(self.uart_wrapper.SET_CURRENT(0, self._red)[1])
        self.logger.info(self.uart_wrapper.SET_CURRENT(1, self._white)[1])
        self.logger.info(self.uart_wrapper.FINISH_CONFIGURE_WITH_SAVING()[1])
        self.logger.info(self.uart_wrapper.START()[1])
        self.logger.debug(res)
        self._started = True
        if tick:
            tick.result = res
        else:
            return res

    async def handle_ticket(self, tick: Ticket):
        com = Command(**tick.command)
        command = com.func
        if command in self._list_of_methods:
            if command == "get_info":
                new_single_coro = SingleCoro(
                    self.get_info,
                    "SystemUnit.get_info_task",
                    tick
                )
                return new_single_coro

            elif command == "start":
                new_single_coro = SingleCoro(
                    self.start,
                    "SystemUnit.get_info_task",
                    tick
                )
                return new_single_coro

            elif command == "stop":
                new_single_coro = SingleCoro(
                    self.stop, "SystemUnit.get_info_task", tick)
                return new_single_coro

            elif command == "set_current":
                red = com.args["red"]
                white = com.args["white"]
                new_single_coro = SingleCoro(
                    self.set_current,
                    "SystemUnit.get_info_task",
                    red=red,
                    white=white,
                    tick=tick
                )
                return new_single_coro
        else:
            raise ValueError("LedUnitError: No such command - {}".format(command.func))


class ArdUnit(Unit):
    """
    Unit for simple arduino module, that controls simple greenhouse
    through usb-rs485 adapter
    Look for description of protocol in ard_wrapper.py
    """
    def __init__(
            self,
            devname: str = '/dev/ttyUSB0',
            baudrate: int = 9600,
            timeout: float = 0.5,
            devices: list = None
    ):
        super(ArdUnit, self).__init__(name="ard_unit")
        self.sensor = ArdWrapper(
            devname=devname,
            baudrate=baudrate,
            timeout=timeout
        )
        self._list_of_methods = [
            "get_info",
            "set_led",
            "do_measurement",
            "do_command"
        ]
        if devices is None:
            self.devices = [b'\x05']  # list of hex ids of current devices
        else:
            self.devices = devices
        self.logger = logging.getLogger("Worker.Units.ArdUnit")
        self.logger.info("ArdUnit init")



class CO2SensorUnit(Unit):
    """
    Unit for CO2Sensor methods wrapping
    """
    """
    Short list of commands for SBA5:
    
    Fxxx<CR> Measurement string format. 0 to 255 to enable individual outputs
    M Display a measurement.
    Z Perform a zero operation.
    ! Turns measurement display off.
    @ Turns measurement display on.
    ? Display the SBA-5 configuration currently in use.
    Axxx<CR> Time [minutes] between zero operations. range: 0-10000 (integer, but can be
        negative). Recommended maximum setting is 20 minutes. A0 - turns auto zero operations off. 
    Pxxx<CR> Turns the onboard pump from on or off, if one is installed.
        Sending “P0” turns pump off. Sending “P1” turns pump on.
    """

    def __init__(
            self,
            devname: str = '/dev/ttyUSB0',
            baudrate: int = 19200,
            timeout: float = 0.1
    ):
        super(CO2SensorUnit, self).__init__(name="co2_sensor_unit")
        self.sensor = SBAWrapper(
            devname=devname,
            baudrate=baudrate,
            timeout=timeout
        )
        self._list_of_methods = [
            "get_info",
            "do_calibration",
            "do_measurement",
            "do_command"
        ]
        self.logger = logging.getLogger("Worker.Units.CO2Sensor")
        self.logger.info("First part of CO2Sensor init")

    async def init(self):
        # TODO: mb we need protection from calling that method twice?
        # async part of init
        # we have to send some commands before start regular work of unit
        self.logger.info("Second part of CO2Sensor init")
        # ans = await self.sensor.send_command("?\r\n")
        # self.logger.info("Command ?, answer: {}".format(ans))
        # if not "OK" in ans:
        #     self.logger.info("CO2SensorError: {}".format(ans))
        #     return "CO2SensorError: {}".format(ans)
        # we need to shut down auto measurements
        ans = await self.sensor.send_command("!\r\n")
        self.logger.info("Command !, answer: {}".format(ans)[:-1])
        # we need to shut down auto zero operations
        ans = await self.sensor.send_command("A0\r\n")
        self.logger.info("Command A0, answer: {}".format(ans)[:-1])
        # we need to set format of output
        ans = await self.sensor.send_command("F252\r\n")
        self.logger.info("Command F252, answer: {}".format(ans)[:-1])
        # we need to start pump
        ans = await self.sensor.send_command("P1\r\n")
        self.logger.info("Command P1, answer: {}".format(ans)[:-1])
        # set medium time of calibration
        ans = await self.sensor.send_command("EM\r\n")
        self.logger.info("Command EM, answer: {}".format(ans)[:-1])

    async def get_info(self, tick: Ticket = None):
        ans = await self.sensor.send_command("?\r\n")
        self.logger.debug("Getting info from SBA5")
        if tick:
            tick.result = ans
        else:
            return ans

    async def do_calibration(self, tick: Ticket = None):
        ans = await self.sensor.send_command("Z\r\n")
        self.logger.info("Starting calibration of SBA5")
        if tick:
            tick.result = ans
        else:
            return ans

    async def do_measurement(self, tick: Ticket = None):
        ans = await self.sensor.send_command("M\r\n")
        self.logger.debug("Do measure SBA5")
        self.logger.debug(("SBA5 result is {}".format(ans))[:-1])  #its try to remove last \n from here
        if tick:
            tick.result = ans
        else:
            return ans

    async def do_command(self, tick: Ticket, com: str):
        ans = await self.sensor.send_command(com)
        self.logger.info("send {} command to SBA5".format(com))
        tick.result = ans

    async def handle_ticket(self, tick: Ticket):
        com = Command(**tick.command)
        command = com.func
        if command in self._list_of_methods:
            if command == "get_info":
                new_single_coro = SingleCoro(
                    self.get_info,
                    "CO2SensorUnit.get_info_task",
                    tick
                )
                return new_single_coro
            elif command == "do_calibration":
                new_single_coro = SingleCoro(
                    self.do_calibration,
                    "CO2SensorUnit.get_info_task",
                    tick
                )
                return new_single_coro
            elif command == "do_measurement":
                new_single_coro = SingleCoro(
                    self.do_measurement,
                    "CO2SensorUnit.do_measurement_task",
                    tick
                )
                return new_single_coro
            elif command == "do_command":
                new_single_coro = SingleCoro(
                    self.do_command,
                    "CO2SensorUnit.do_command_task",
                    tick=tick,
                    com=com.args["com"]
                )
                return new_single_coro
        else:
            raise ValueError("CO2SensorError: No such command - {}".format(command.func))


class GpioUnit(Unit):
    """
    Unit for correct gpio calls wrapping
    """

    def __init__(self):
        # TODO: move all magic consts from here to config
        super(GpioUnit, self).__init__(name="gpio_unit")
        self.logger = logging.getLogger("Worker.Units.Gpio")
        self.logger.info("Gpio init")
        # pins and devices, connected to them

        # map of pins connected to channels and their states
        self.pins = {
            10: True,
            9: True,
            11: True,
            17: True,
            27: True,
            13: True,
            19: True,
            26: True,
            16: True,
            20: True
        }
        # dirty
        self.vent_pins = [10, 9, 11, 17]
        self.cooler_pin = [19]
        self.calibration_pins = [13]
        self.drain_pump_pins = [26, 27]
        self.drain_valve_pins = [16, 20]
        self.measure_pins = []
        # very dirty
        self.drain_valve_time = 15  # sec
        # platform-dependent unit, so we need to check
        if platf != "RPi":
            self.logger.error("We are not on RPi, so this unit will be only a stub")
            # self._list_of_methods = []
        else:
            self.gpio = GPIOWrapper()
            self._list_of_methods = [
                "get_info",
                "start_ventilation",
                "stop_ventilation",
                "start_calibration",
                "stop_calibration",
                "start_coolers",
                "stop_coolers",
                "start_draining",
                "stop_draining",
                "set_pin"
            ]
            # set pins as output
            for i in self.pins.keys():
                self.gpio.set_mode(i, "output")
                # set initial value to True, to shut down relays
                self.gpio.write(i, True)

    async def get_info(self, tick: Ticket = None):
        self.logger.debug("Gpio get_info")
        res = self.pins
        if tick:
            tick.result = res
        else:
            return res

    async def stop(self, tick: Ticket = None):
        self.logger.info("Gpio stop")
        self.gpio.deleter()
        res = "Gpio cleaned up"
        self.logger.debug(res)
        if tick:
            tick.result = res
        else:
            return res

    async def start_draining(self, tick: Ticket = None):
        self.logger.info("Gpio start_draining")
        res = ""
        # at first open valves
        for pin in self.drain_valve_pins:
            res += self.gpio.write(pin, False)
            # false - because our relay is low level trigger
            self.pins[pin] = False
        self.logger.info("Start opening drain valves")
        # then wait magic time
        await asyncio.sleep(self.drain_valve_time)
        self.logger.info("Drain valves should be open now")
        # then set up air pumps
        for pin in self.drain_pump_pins:
            res += self.gpio.write(pin, False)
            # false - because our relay is low level trigger
            self.pins[pin] = False
        self.logger.info("Start drain pumps")

        # results
        self.logger.debug(res)
        if tick:
            tick.result = res
        else:
            return res

    async def stop_draining(self, tick: Ticket = None):
        self.logger.info("Gpio stop_draining")
        res = ""
        # set off air pumps
        for pin in self.drain_pump_pins:
            res += self.gpio.write(pin, True)
            # false - because our relay is low level trigger
            self.pins[pin] = True
        self.logger.info("Stop drain pumps")

        # then close valves
        for pin in self.drain_valve_pins:
            res += self.gpio.write(pin, True)
            # false - because our relay is low level trigger
            self.pins[pin] = True
        self.logger.info("Close drain valves")

        self.logger.debug(res)
        if tick:
            tick.result = res
        else:
            return res

    async def start_ventilation(self, tick: Ticket = None):
        self.logger.info("Gpio start_ventilation")
        res = ""
        for i in self.vent_pins:
            res += self.gpio.write(i, False)
            # false - because our relay is low level trigger
            self.pins[i] = False
        self.logger.debug(res)
        if tick:
            tick.result = res
        else:
            return res

    async def stop_ventilation(self, tick: Ticket= None):
        self.logger.info("Gpio stop_ventilation")
        res = ""
        for i in self.vent_pins:
            res = self.gpio.write(i, True)
            self.pins[i] = True
        self.logger.debug(res)
        if tick:
            tick.result = res
        else:
            return res

    async def start_calibration(self, tick: Ticket = None):
        self.logger.info("Gpio start_calibration")
        for i in self.calibration_pins:
            res = self.gpio.write(i, False)
            # false - because our relay is low level trigger
            self.pins[i] = False
        # then we need to stop pump3
        for i in self.measure_pins:
            res = self.gpio.write(i, True)
            # false - because our relay is low level trigger
            self.pins[i] = True
        self.logger.debug(res)
        if tick:
            tick.result = res
        else:
            return res

    async def stop_calibration(self, tick: Ticket = None):
        self.logger.info("Gpio stop_calibration")
        for i in self.calibration_pins:
            res = self.gpio.write(i, True)
            # false - because our relay is low level trigger
            self.pins[i] = True
        # then we need to start pump3
        for i in self.measure_pins:
            res = self.gpio.write(i, False)
            # false - because our relay is low level trigger
            self.pins[i] = False
        self.logger.debug(res)
        if tick:
            tick.result = res
        else:
            return res

    async def start_coolers(self, tick: Ticket = None):
        self.logger.info("Gpio start coolers")
        for i in self.cooler_pin:
            res = self.gpio.write(i, False)
            # false - because our relay is low level trigger
            self.pins[i] = False
        self.logger.debug(res)
        if tick:
            tick.result = res
        else:
            return res

    async def stop_coolers(self, tick: Ticket = None):
        self.logger.info("Gpio stop coolers")
        for i in self.cooler_pin:
            res = self.gpio.write(i, True)
            # false - because our relay is low level trigger
            self.pins[i] = True
        self.logger.debug(res)
        if tick:
            tick.result = res
        else:
            return res

    async def set_pin(self, pin: int, state: bool, tick: Ticket = None):
        self.logger.info("Gpio manually set pin")
        res = self.gpio.write(pin, state)
        self.pins[pin] = state
        self.logger.debug(res)
        if tick:
            tick.result = res
        else:
            return res

    async def handle_ticket(self, tick: Ticket):
        if platf != "RPi":
            # TODO : we have to send error message to user, not only die here
            raise ValueError("GpioUnitError: cannot work on not-RPi platform")
        else:
            com = Command(**tick.command)
            command = com.func

            if command in self._list_of_methods:
                if command == "get_info":
                    new_single_coro = SingleCoro(
                        self.get_info,
                        "GpioUnit.get_info_task",
                        tick
                    )
                    return new_single_coro
                elif command == "start_ventilation":
                    new_single_coro = SingleCoro(
                        self.start_ventilation,
                        "GpioUnit.start_ventilation_task",
                        tick
                    )
                    return new_single_coro
                elif command == "stop_ventilation":
                    new_single_coro = SingleCoro(
                        self.stop_ventilation,
                        "GpioUnit.stop_ventilation_task",
                        tick
                    )
                    return new_single_coro
                elif command == "start_calibration":
                    new_single_coro = SingleCoro(
                        self.start_calibration,
                        "GpioUnit.start_calibration_task",
                        tick
                    )
                    return new_single_coro
                elif command == "stop_calibration":
                    new_single_coro = SingleCoro(
                        self.stop_calibration,
                        "GpioUnit.stop_calibration_task",
                        tick
                    )
                    return new_single_coro
                elif command == "start_coolers":
                    new_single_coro = SingleCoro(
                        self.start_coolers,
                        "GpioUnit.start_coolers_task",
                        tick
                    )
                    return new_single_coro
                elif command == "stop_coolers":
                    new_single_coro = SingleCoro(
                        self.stop_coolers,
                        "GpioUnit.stop_coolers_task",
                        tick
                    )
                    return new_single_coro

                elif command == "start_draining":
                    new_single_coro = SingleCoro(
                        self.start_draining,
                        "GpioUnit.start_draining_task",
                        tick
                    )
                    return new_single_coro

                elif command == "stop_draining":
                    new_single_coro = SingleCoro(
                        self.stop_draining,
                        "GpioUnit.stop_draining_task",
                        tick
                    )
                    return new_single_coro

                elif command == "set_pin":
                    pin = com.args["pin"]
                    state = com.args["state"]
                    new_single_coro = SingleCoro(
                        self.set_pin,
                        "GpioUnit.set_pin_task",
                        tick=tick,
                        pin=pin,
                        state=state
                    )
                    return new_single_coro
            else:
                raise ValueError("GpioUnitError: No such command - {}".format(command.func))


class WeightUnit(Unit):
    """
    Unit for wrapping weight sensor (HX711) methods
    """

    def __init__(
            self,
            dout_pin: int = 5,
            pd_sck_pin: int = 6,
            scale: float = -1142.2754,
            tare: int = 608
    ):
        super(WeightUnit, self).__init__(name="weight_unit")
        self.logger = logging.getLogger("Worker.Units.Weight")
        self.logger.info("WeightUnit init")
        if platf != "RPi":
            self.logger.error("WeightUnitError: We are not on RPi, so this unit will be only a stub")
        else:
            self.hx = HX711Wrapper(
                dout_pin=dout_pin,
                pd_sck_pin=pd_sck_pin,
                scale=scale,
                tare=tare
            )
            self._list_of_methods = [
                "get_data"
            ]

    async def get_data(self, tick : Ticket = None):
        res = self.hx.get_data()
        self.logger.debug("Weight unit get data: {}".format(res))
        if tick:
            tick.result = res
        else:
            return res

    async def handle_ticket(self, tick: Ticket):
        if platf != "RPi":
            self.logger.error("WeightUnitError: We are not on RPi, so this unit is a stub only")
            # TODO : we have to send error message to user, not only die here
        else:
            command = Command(**tick.command)
            if command in self._list_of_methods:
                if command == "get_data":
                    new_single_coro = SingleCoro(
                        self.get_data(),
                        "WeightUnit.get_data",
                        tick
                    )
                    return new_single_coro
            else:
                raise ValueError("WeightUnitError: No such command - {}".format(command.func))


class K30Unit(Unit):
    """
    Unit for wrapping k30 methods
    """
    def __init__(self,
                 devname="/dev/ttyUSB0",
                 baudrate=9600,
                 timeout=1
                 ):

        super(K30Unit, self).__init__(name="k30_unit")
        self.devname = devname
        self.baudrate = baudrate
        self.timeout = timeout
        self.logger = logging.getLogger("Worker.Units.K30")
        self.sensor = K30(
            devname=self.devname,
            baudrate=self.baudrate,
            timeout=self.timeout
        )
        self.logger.info("K30 CO2 sensor started")
        self._list_of_methods = [
            #  "get_info",   -- mb later
            "get_data"
        ]

    async def get_data(self, tick: Ticket = None):
        co2, logs = self.sensor.get_data()
        self.logger.debug("K30 CO2 got results: {}".format(logs))
        if tick:
            tick.result = co2
        else:
            return co2

    async def handle_ticket(self, tick: Ticket):
        command = Command(**tick.command)
        if command.func in self._list_of_methods:
            if command.func == "get_data":
                new_single_coro = SingleCoro(
                    self.get_data,
                    "K30Unit: get_data task",
                    tick
                )
                return new_single_coro
        else:
            raise ValueError("K30UnitError: No such command - {}".format(command.func))


class TempSensorUnit(Unit):
    """
    Unit for wrapping temp sensor methods - dht11 for now
    """

    def __init__(self, pin: int = 14, dhttype: int = 22):
        super(TempSensorUnit, self).__init__(name="temp_sensor_unit")
        self.logger = logging.getLogger("Worker.Units.TempSensor")
        self.logger.info("TempSensor init")
        # platform-dependent unit, so we need to check
        if platf != "RPi":
            self.logger.error("We are not on RPi, so this unit will be only a stub")
        else:
            self._list_of_methods = [
                "get_info",
                "get_data"
            ]
            self.pin = pin
            self.dhttype = dhttype
            self.sensor = DHTWrapper(pin=self.pin, DHTTYPE=self.dhttype)

    async def get_data(self, tick: Ticket = None):
        self.logger.debug("Dht get data function")
        if platf != "RPi":
            self.logger.error("We are not on RPi, so this unit will be only a stub")
        else:
            h, t = self.sensor.get_data()
            self.logger.debug((t, h))
            if tick:
                tick.result = (t, h)
            else:
                return t, h

    async def get_info(self, tick: Ticket = None):
        self.logger.debug("Dht get info function")
        if platf != "RPi":
            self.logger.error("We are not on RPi, so this unit will be only a stub")
        else:
            self.logger.debug((self.pin, self.dhttype))
            if tick:
                tick.result = (self.pin, self.dhttype)
            else:
                return self.pin, self.dhttype

    async def handle_ticket(self, tick: Ticket):
        # TODO : fix taht it doesnt works
        command = Command(**tick.command)
        if platf != "RPi":
            self.logger.error("We are not on RPi, so this unit will be only a stub")
        else:
            if command.func in self._list_of_methods:
                if command.func == "get_info":
                    return await self.get_info()
            else:
                raise ValueError("TempSensorUnitError: No such command - {}".format(command.func))


class SystemUnit(Unit):
    """
    Unit for all needs, that are not related with real fitostand objects like valves
    pumps, leds and other
    Methods assigned with linux commands and commands for worker
    """

    def __init__(self, worker: Any):
        super(SystemUnit, self).__init__(name="system_unit")
        self.worker = worker
        self.logger = logging.getLogger("Worker.Units.System")
        self.logger.info("System unit init")
        self.list_of_methods = [
            "get_info",
            "create_tunnel",
            "pause",
            "continue",
            "stop",
            "start_ventilation",
            "stop_ventilation",
            "do_calibration",
            "do_measure"
        ]

    async def get_info(self, tick: Ticket):
        self.logger.info("get info")
        proc = await asyncio.create_subprocess_shell("uname -a", stdout=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        content = stdout.decode().strip()
        if tick:
            tick.result = content
        else:
            return content

    async def start_ventilation(self, tick: Ticket = None):
        self.logger.info("manual start ventilation")
        result = await self.worker.start_ventilation()
        if tick:
            tick.result = result
        else:
            return result

    async def stop_ventilation(self, tick: Ticket = None):
        self.logger.info("manual stop ventilation")
        result = await self.worker.stop_ventilation()
        if tick:
            tick.result = result
        else:
            return result

    async def do_calibration(self, tick: Ticket = None):
        self.logger.info("manual do calibration")
        result = await self.worker.do_calibration()
        if tick:
            tick.result = result
        else:
            return result

    async def do_measure(self, tick: Ticket = None):
        self.logger.info("manual do measure")
        result = await self.worker.measure()
        if tick:
            tick.result = result
        else:
            return result

    async def pause(self, tick: Ticket = None):
        self.logger.info("manual pause")
        await self.worker.pause()
        result = "worker paused"
        if tick:
            tick.result = result
        else:
            return result

    async def do_reconfiguration(self, tick: Ticket = None):
        self.logger.info("manual do_reconfiguration")
        await self.worker.do_reconfiguration()
        result = "worker do_reconfiguration"
        if tick:
            tick.result = result
        else:
            return result

    async def continue_(self, tick: Ticket = None):
        self.logger.info("manual continue")
        await self.worker.continue_()
        result = "worker continued"
        if tick:
            tick.result = result
        else:
            return result

    async def stop(self, tick: Ticket = None):
        self.logger.info("manual kill worker")
        # TODO: check if it really works
        await self.worker.stop()
        result = "worker killed"
        if tick:
            tick.result = result
        else:
            return result

    async def create_tunnel(self, tick: Ticket):
        self.logger.info("manual create tunnel")
        # TODO: mb remove it ? It is dangerous
        cmd = 'autossh -M 10984 -N -f -o "PubkeyAuthentication=yes" -o "PasswordAuthentication=no" -i /home/pi/.ssh/id_rsa -R 6666:localhost:22 slonik@83.220.174.247 &'

        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        content = stdout.decode().strip()
        if tick:
            tick.result = content
        else:
            return content

    async def handle_ticket(self, tick: Ticket):
        command = Command(**tick.command)

        if command.func in self.list_of_methods:
            if command.func == "get_info":
                new_single_coro = SingleCoro(
                    self.get_info,
                    "SystemUnit.get_info_task",
                    tick
                )
                return new_single_coro

            elif command.func == "create_tunnel":
                new_single_coro = SingleCoro(
                    self.create_tunnel,
                    "SystemUnit.create_tunnel_task",
                    tick
                )
                return new_single_coro

            elif command.func == "pause":
                new_single_coro = SingleCoro(
                    self.pause,
                    "SystemUnit.pause_task",
                    tick
                )
                return new_single_coro

            elif command.func == "continue":
                new_single_coro = SingleCoro(
                    self.continue_,
                    "SystemUnit.continue_task",
                    tick
                )
                return new_single_coro

            elif command.func == "stop":
                new_single_coro = SingleCoro(
                    self.stop,
                    "SystemUnit.stop_task",
                    tick
                )
                return new_single_coro

            elif command.func == "start_ventilation":
                new_single_coro = SingleCoro(
                    self.start_ventilation,
                    "SystemUnit.start_ventilation_task",
                    tick
                )
                return new_single_coro

            elif command.func == "stop_ventilation":
                new_single_coro = SingleCoro(
                    self.stop_ventilation,
                    "SystemUnit.stop_ventilation_task",
                    tick
                )
                return new_single_coro

            elif command.func == "do_calibration":
                new_single_coro = SingleCoro(
                    self.do_calibration,
                    "SystemUnit.do_calibration_task",
                    tick
                )
                return new_single_coro

            elif command.func == "do_measure":
                new_single_coro = SingleCoro(
                    self.do_measure,
                    "SystemUnit.do_measure_task",
                    tick
                )
                return new_single_coro

            elif command.func == "do_reconfiguration":
                new_single_coro = SingleCoro(
                    self.do_reconfiguration,
                    "SystemUnit.do_reconfiguration",
                    tick
                )
                return new_single_coro
        else:
            raise ValueError("SystemUnitError: No such command - {}".format(command.func))

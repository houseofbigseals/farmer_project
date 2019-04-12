# units - async wrappers for low-level objects

import asyncio
from led_uart_wrapper import UartWrapper
from command import Message, Command, Ticket
from tasks import PeriodicTask, SingleTask, LongSingleTask, PeriodicCoro, SingleCoro
from colorama import Back
from sba5_wrapper import SBAWrapper
import logging

logger = logging.getLogger("Worker.Units")
platf = None
try:
    # platform dependent modules
    # they work correctly only on raspberry
    from dht_wrapper import DHTWrapper
    from gpio_wrapper import GPIOWrapper
    from hx_wrapper import HX711Wrapper
    platf = "RPi"
except ImportError:
    logger.info("Looks like we are not on RPi")
    platf = "PC"


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

        super(LedUnit, self).__init__(name="LedUnit")
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

    async def set_current(self, tick: Ticket = None, red: int = 10, white: int = 10):
        self._red = red
        self._white = white
        # TODO: handle incorrect current values such as (10000, 0) or smth
        self.logger.info("Trying to set red current to {}, white - to {}".format(red, white))
        res = ""
        res += self.uart_wrapper.STOP()[1]
        res += self.uart_wrapper.START_CONFIGURE()[1]
        res += self.uart_wrapper.SET_CURRENT(0, red)[1]
        res += self.uart_wrapper.SET_CURRENT(1, white)[1]
        res += self.uart_wrapper.FINISH_CONFIGURE_WITH_SAVING()[1]
        res += self.uart_wrapper.START()[1]
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
        super(CO2SensorUnit, self).__init__(name="CO2SensorUnit")
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
        self.logger.info("Command !, answer: {}".format(ans))
        # we need to shut down auto zero operations
        ans = await self.sensor.send_command("A0\r\n")
        self.logger.info("Command A0, answer: {}".format(ans))
        # we need to set format of output
        ans = await self.sensor.send_command("F252\r\n")
        self.logger.info("Command F252, answer: {}".format(ans))
        # we need to start pump
        ans = await self.sensor.send_command("P1\r\n")
        self.logger.info("Command P1, answer: {}".format(ans))

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
        # self.logger.debug("Do measure SBA5")
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
        super(GpioUnit, self).__init__(name="GpioUnit")
        self.logger = logging.getLogger("Worker.Units.Gpio")
        self.logger.info("Gpio init")
        # pins and devices, connected to them
        # 2 - pump1
        # 3 - valve1
        # 4 - pump2
        # 17 - valve2
        # 27 - pump3
        # 13 - valve3
        # 19 - 12VDC coolers
        # 26 - none for now

        # map of pins connected to channels and their states
        self.pins = {
            2: True,
            3: True,
            4: True,
            17: True,
            27: True,
            13: True,
            19: True,
            26: True
        }
        # dirty
        self.vent_pins = [2, 3, 4, 17]
        self.cooler_pin = [19]
        self.calibration_pins = [13]
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
                "set_pin"
            ]
            # set pins as output
            for i in self.pins.keys():
                self.gpio.set_mode(i, "output")
                # set initial value to True, to shut down relays
                self.gpio.write(i, True)

    async def get_info(self, tick: Ticket = None):
        self.logger.info("Gpio get_info")
        res = "Version : " + self.gpio.info()
        res += "\nState of outputs: "
        for i in self.pins.keys():
            res += "\n Gpio pin {} is {}".format(i, self.pins[i])
        self.logger.debug(res)
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
                elif command == "set_pin":
                    pin = com.args["pin"]
                    state = com.args["state"]
                    new_single_coro = SingleCoro(
                        self.set_pin,
                        "GpioUnit.start_coolers_task",
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

    def __init__(self, pin: int = 14, dhttype: int = 11 ):
        super(TempSensorUnit, self).__init__(name="TempSensorUnit")
        self.logger = logging.getLogger("Worker.Units.Gpio")
        self.logger.info("Gpio init")
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
            h, t, log = self.sensor.get_data()
            self.logger.debug((t, h, log))
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
    """

    def __init__(self):
        super(SystemUnit, self).__init__()
        self._list_of_methods = [
            "get_info",
            "create_tunnel"
        ]

    async def _get_info(self, tick: Ticket):
        # print(Back.CYAN + "SystemUnit.SystemUnit.get_info_task started!")
        proc = await asyncio.create_subprocess_shell("uname -a", stdout=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        content = stdout.decode().strip()
        tick.result = content
        # print(Back.CYAN + "SystemUnit.SystemUnit.get_info_task done!")

    async def _create_tunnel(self, tick: Ticket):
        cmd = 'autossh -M 10984 -N -f -o "PubkeyAuthentication=yes" -o "PasswordAuthentication=no" -i /home/pi/.ssh/id_rsa -R 6666:localhost:22 slonik@83.220.174.247 &'

        # print(Back.CYAN + "SystemUnit.SystemUnit.create_tunnel_task started!")
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        # if stdout:
        #     content = '[stdout]\n{}'.format(stdout.decode()).strip()
        # if stderr:
        #     content = '[stderr]\n{}'.format(stderr.decode()).strip()
        content = stdout.decode().strip()
        tick.result = content
        # print(Back.CYAN + "SystemUnit.SystemUnit.create_tunnel_task done!")

    async def handle_ticket(self, tick: Ticket):
        # print(Back.CYAN + "SystemUnit.handle_ticket started!")
        command = Command(**tick.command)

        if command.func in self._list_of_methods:
            # print(Back.CYAN + "SystemUnit.handle_ticket command.func in self._list_of_methods!")
            if command.func == "get_info":
                new_single_coro = SingleCoro(self._get_info, "SystemUnit.get_info_task", tick)
                # print(Back.CYAN + "SystemUnit.handle_ticket created coro!")
                return new_single_coro
            elif command.func == "create_tunnel":
                new_single_coro = SingleCoro(self._create_tunnel, "SystemUnit.create_tunnel_task", tick)
                # print(Back.CYAN + "SystemUnit.handle_ticket created coro!")
                return new_single_coro
        else:
            raise ValueError("SystemUnitError: No such command - {}".format(command.func))
        # print(Back.CYAN + "SystemUnit.handle_ticket done!")

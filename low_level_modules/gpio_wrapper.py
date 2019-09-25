# there is a GPIO wrapper object class for RaspberryPi
# we want to not carry about how it works and want to get functional
# like this:
# set_mode(PIN, MODE) - input or output
# write(PIN, STATE) - high or low, like in wiring
# read(PIN)
# in future version we will use gpiozero library
# but now it is RPi.GPIO for compatibility

from typing import Any, Optional
from RPi import GPIO
from time import sleep
import logging
import argparse

logger = logging.getLogger("Worker.Units.Gpio.GpioWrapper")


class GPIOWrapper(object):
    """
    Simple gpio wrapper wit three functions:
    # set_mode(PIN, MODE) - input or output
    # write(PIN, STATE) - high or low, like in wiring
    # read(PIN)
    """

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        # GPIO.setmode(GPIO.BOARD)

    def set_mode(self, pin: int, mode: str) -> None:
        if mode == "input":
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            # or
            # GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        elif mode == "output":
            GPIO.setup(pin, GPIO.OUT)

    def read(self, pin: int) -> Optional[Any]:
        try:
            return GPIO.input(pin)
        except Exception as e:
            return "There is GPIO error: {}".format(e)

    def write(self, pin: int, state: bool) -> str:
        logger.debug("Trying to set pin {} to state {}".format(pin, str(state)))
        res = ""
        try:
            GPIO.output(pin, state)
            logger.debug("OK")
            res = "OK"
        except Exception as e:
            logger.debug("There is GPIO error: {}".format(e))
            res = str(e)
        return res

    def info(self) -> str:
        return str(GPIO.RPI_INFO) + " " + str(GPIO.VERSION)

    def __del__(self):
        GPIO.cleanup()

    def deleter(self):
        GPIO.cleanup()


def all_test():
    g = GPIOWrapper()
    pins = {
        "ch1": 10,
        "ch2": 9,
        "ch3": 11,
        "ch4": 17,
        "ch5": 27,
        "ch6": 13,
        "ch7": 19,
        "ch8": 26,
        "ch9": 16,
        "ch10": 20
    }
    for i in pins.values():
        g.set_mode(i, "output")
    while(True):
        for i in pins.values():
            g.write(i, False)
        sleep(20)
        for i in pins.values():
            g.write(i, True)
        sleep(20)


def one_test():
    # parser = argparse.ArgumentParser(
    #     description="Gpio test",
    #     epilog="UIUIUIUIUIUIUIUI"
    # )
    # parser.add_argument('-M', '--mode', type=str, default="1", help='1 - on, 0 - off')
    # parser.add_argument('-P', '--pin', type=int, default=13, help='rpi pin')
    # ns = parser.parse_args()
    # print(ns.pin)
    # print(ns.mode)
    # pin = ns.pin
    pin = 13
    g = GPIOWrapper()
    g.set_mode(pin, "output")
    while True:
        g.write(pin, True)
        sleep(2)
        g.write(pin, False)
        sleep(2)

if __name__ == "__main__":
    all_test()

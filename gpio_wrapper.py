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
import argparse


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
        res = "Trying to set pin {} to state {} \n".format(pin, str(state))
        try:
            GPIO.output(pin, state)
            res += "OK \n"
        except Exception as e:
            res += "\nThere is GPIO error: {}".format(e)
        return res

    def info(self) -> str:
        return str(GPIO.RPI_INFO) + "\n" + str(GPIO.VERSION) + "\n"

    def __del__(self):
        GPIO.cleanup()


def all_test():
    g = GPIOWrapper()
    pins = {
        "ch1": 2,
        "ch2": 3,
        "ch3": 4,
        "ch4": 17,
        "ch5": 27,
        "ch6": 13,
        "ch7": 19,
        "ch8": 26,
    }
    for i in pins.values():
        g.set_mode(i, "output")
    while(True):
        for i in pins.values():
            g.write(i, False)
        sleep(2)
        for i in pins.values():
            g.write(i, True)
        sleep(2)


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
    pin = 2
    g = GPIOWrapper()
    g.set_mode(pin, "output")
    while True:
        g.write(pin, True)
        sleep(2)
        g.write(pin, False)
        sleep(2)

if __name__ == "__main__":
    one_test()

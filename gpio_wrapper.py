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
            print("There is GPIO error: {}".format(e))

    def write(self, pin: int, state: bool) -> None:
        try:
            GPIO.output(pin, state)
        except Exception as e:
            print("There is GPIO error: {}".format(e))

    def info(self) -> Any:
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Gpio test",
        epilog="UIUIUIUIUIUIUIUI"
    )
    parser.add_argument('-M', '--mode', type=str, default="1", help='1 - on, 0 - off')
    parser.add_argument('-P', '--pin', type=int, default=13, help='rpi pin')
    ns = parser.parse_args()
    g = GPIOWrapper()
    g.set_mode(ns.pin, "output")
    if ns.mode:
        g.write(ns.pin, True)
    else:
        g.write(ns.pin, False)

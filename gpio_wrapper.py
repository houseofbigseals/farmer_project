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

if __name__ == "__main__":
    g = GPIOWrapper()
    g.write()
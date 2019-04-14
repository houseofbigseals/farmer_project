# Just install by pip3 install HX711. A basic usage example is given below:

from hx711 import HX711
from RPi import GPIO


class HX711Wrapper(object):
    # TODO: do your work, you, lazy piglet
    pass


def perev_test():

    hx = HX711(
        dout_pin=5,
        pd_sck_pin=6,
        channel='A',
        gain=64
    )
    hx.reset()   # Before we start, reset the HX711 (not obligate)
    hx.set_gain_A(gain=64)
    hx.select_channel(channel='A')
    data = hx.get_raw_data_mean(times=1)
    measures = hx.get_raw_data(num_measures=3)
    print("\n".join(measures)) # not scaled data
    TARA = 608  # 642
    KOEFF = -1142.2754  # 1057.8985
    if data == False:   # always check if you get correct value or only False
        print('invalid data')
    hx.set_scale_ratio(scale_ratio=KOEFF)   # set ratio for current channel
    res = hx.get_weight_mean(5) - TARA # main formula of scaled data
    print("\n".join(res))

def hx_test():
    try:
        hx711 = HX711(
            dout_pin=5,
            pd_sck_pin=6,
            channel='A',
            gain=64
        )
        hx711.reset()   # Before we start, reset the HX711 (not obligate)
        measures = hx711.get_raw_data(num_measures=3)
    finally:
        # GPIO.cleanup()  # always do a GPIO cleanup in your scripts!

    print("\n".join(measures))

if __name__ == "__main__":
    hx_test()
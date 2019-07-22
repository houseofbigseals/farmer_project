# Just install by pip3 install HX711. A basic usage example is given below:
try:
    from low_level_modules.hx711 import HX711
except:
    from .hx711 import HX711

from RPi import GPIO


class HX711Wrapper(object):
    """
    Stupid wrapper for hx711
    It is a wrapper around wrapper and it will be wrapped
    Whats problem with me
    """

    def __init__(
            self,
            dout_pin=5,
            pd_sck_pin=6,
            scale: float = -1142.2754,
            tare: int = 608
    ):
        GPIO.setmode(GPIO.BCM)
        self.scale = scale
        self.tare = tare
        self.dout_pin = dout_pin
        self.pd_sck_pin = pd_sck_pin

        self.hx = HX711(
            dout_pin=dout_pin,
            pd_sck_pin=pd_sck_pin,
            gain_channel_A=64,
            select_channel='A'
        )
        self.hx.reset()
        self.hx.set_gain_A(gain=64)
        self.hx.select_channel(channel='A')
        data = self.hx.get_raw_data_mean()
        if data == False:
            raise ValueError("hx_wrapper_error: not data from hx711")
        self.hx.set_scale_ratio(scale_ratio=self.scale)

    def get_data(self):
        data = self.hx.get_weight_mean(5) - self.tare
        return data


def new_test():
    GPIO.setmode(GPIO.BCM)
    TARA = 608  # 642
    KOEFF = -1142.2754  # 1057.8985
    hx = HX711(dout_pin=5, pd_sck_pin=6, gain_channel_A=64, select_channel='A')
    result = hx.reset()  # Before we start, reset the hx711 ( not necessary)
    if result:  # you can check if the reset was successful
        print('Ready to use')
    else:
        print('Weight not ready')
    hx.set_gain_A(gain=64)
    hx.select_channel(channel='A')
    data = hx.get_raw_data_mean()

    if data == False:  # always check if you get correct value or only False
        print('invalid data')
        GPIO.cleanup()
        exit(1)

    hx.set_scale_ratio(scale_ratio=KOEFF)  # set ratio for current channel
    ws = []
    ws.append(hx.get_weight_mean(5) - TARA)
    ws.append(hx.get_weight_mean(5) - TARA)
    ws.append(hx.get_weight_mean(5) - TARA)
    print(ws)
    # rw = sps.medfilt(ws)
    # weight = rw[1]


if __name__ == "__main__":
    new_test()
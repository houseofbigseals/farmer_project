#
#
#
# # correct on 22. 07. 19
#
# # at start
#
# full_tube_weight = 405 # 405 - 410
# full_plants = 35 # 40
#
#
# # with weight parameters
# # dout_pin = 5,
# # pd_sck_pin = 6,
# # scale: float = -1142.2754,
# # tare: int = 608
# # gain_channel_A = 64,
# # select_channel = 'A'
#
# # calibration curve
# loads = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100,
#          120, 140, 160, 180, 200, 220, 240, 260, 280, 300
#          ]
# # it is loads added to current tube with plants at zero day
# raw_results = [371, 381, 390, 399, 408.5, 416.5, 426, 438, 448, 457.5, 467,
#                486, 506, 523, 542.5, 562, 581, 600.5, 620.5, 639.5, 660
#                ]
#
#
#
# # correct on 12.08.19
#
# # at start
# full_tube_weight = 405 # 405 - 410
# full_plants = 13
#
# # with weight parameters
# # dout_pin = 5,
# # pd_sck_pin = 6,
# # scale: float = -1142.2754,
# # tare: int = 608
# # gain_channel_A = 64,
# # select_channel = 'A'
#
# # calibration curve
# loads = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100,
#          120, 140, 160, 180, 200, 220, 240, 260
#          ]
# # it is loads added to current tube with plants at zero day
# raw_results = [432, 444, 452, 464, 475, 486,
#                493, 502, 511, 522, 532, 554, 574, 595, 618,
#                636, 661, 681, 700, 712
#                ]
#
# # d_weight = +- 1 gramm at each point


# Just install by pip3 install HX711. A basic usage example is given below:
import numpy as np
try:
    from low_level_modules.hx711 import HX711
except:
    from hx711 import HX711

from RPi import GPIO


def measure_test():
    GPIO.setmode(GPIO.BCM)
    # TARA = 608  # 642
    # KOEFF = -1142.2754  # 1057.8985
    hx = HX711(dout_pin=5, pd_sck_pin=6, gain_channel_A=64, select_channel='A')
    result = hx.reset()  # Before we start, reset the hx711 ( not necessary)
    if result:  # you can check if the reset was successful
        print('Ready to use')
    else:
        print('Weight not ready')
    hx.set_gain_A(gain=64)
    hx.select_channel(channel='A')
    # hx.set_debug_mode(True)
    data = hx.get_raw_data_mean()

    if data == False:  # always check if you get correct value or only False
        print('invalid data')
        GPIO.cleanup()
        exit(1)

    # hx.set_scale_ratio(scale_ratio=KOEFF)  # set ratio for current channel
    ws = []
    ws.append(hx.get_weight_mean(5))
    ws.append(hx.get_weight_mean(5))
    ws.append(hx.get_weight_mean(5))
    print(ws)
    print(np.mean(ws))
    # rw = sps.medfilt(ws)
    # weight = rw[1]


def recalibration():
    GPIO.setmode(GPIO.BCM)
    # TARA = 608  # 642
    # KOEFF = -1142.2754  # 1057.8985
    hx = HX711(dout_pin=5, pd_sck_pin=6, gain_channel_A=64, select_channel='A')
    print("set gain A 64")
    hx.set_gain_A(gain=64)
    print("set channel A")
    hx.select_channel(channel='A')
    print("some info:")
    print("get_current_scale_ratio {}".format(hx.get_current_scale_ratio()))
    print("get_current_offset {}".format(hx.get_current_offset()))
    print("lets get some raw data")
    data = hx.get_raw_data_mean(50)
    print("raw data mean is {}".format(data))

    if data == False:  # always check if you get correct value or only False
        print('invalid raw data, exit')
        GPIO.cleanup()
        exit(1)

    print("lets try commit zero operation ")
    hx.zero()

    print("some new info:")
    print("get_current_scale_ratio {}".format(hx.get_current_scale_ratio()))
    print("get_current_offset {}".format(hx.get_current_offset()))
    print("lets get some raw data")
    data = hx.get_raw_data_mean(50)
    print("raw data mean is {}".format(data))

    ws = list()
    ws.append(hx.get_weight_mean(15))
    ws.append(hx.get_weight_mean(15))
    ws.append(hx.get_weight_mean(15))
    print("mean (of 15 measures) weights are {}".format(ws))
    print("mean meanweight  is {}".format(np.mean(ws)))


if __name__ == "__main__":
    _ = input("We start recalibration, press any key ")
    recalibration()
    known_weight = float(input("Print weight: "))
    measure_test()

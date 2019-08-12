


# correct on 22. 07. 19

# at start

full_tube_weight = 405 # 405 - 410
full_plants = 35 # 40


# with weight parameters
# dout_pin = 5,
# pd_sck_pin = 6,
# scale: float = -1142.2754,
# tare: int = 608
# gain_channel_A = 64,
# select_channel = 'A'

# calibration curve
loads = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100,
         120, 140, 160, 180, 200, 220, 240, 260, 280, 300
         ]
# it is loads added to current tube with plants at zero day
raw_results = [371, 381, 390, 399, 408.5, 416.5, 426, 438, 448, 457.5, 467,
               486, 506, 523, 542.5, 562, 581, 600.5, 620.5, 639.5, 660
               ]



# correct on 12.08.19

# at start
full_tube_weight = 405 # 405 - 410
full_plants = 35 # 40

# with weight parameters
# dout_pin = 5,
# pd_sck_pin = 6,
# scale: float = -1142.2754,
# tare: int = 608
# gain_channel_A = 64,
# select_channel = 'A'

# calibration curve
loads = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100,
         120, 140, 160, 180, 200, 220, 240, 260
         ]
# it is loads added to current tube with plants at zero day
raw_results = [432, 444, 452, 464, 475, 486,
               493, 502, 511, 522, 532, 554, 574, 595, 618,
               636, 661, 681, 700, 712
               ]
# d_weight = +- 1 gramm at each point
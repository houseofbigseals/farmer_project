from low_level_modules.rs_device_wrapper import UartWrapper
import time

def relay_test_baudrate(num = 32, baudrate=57600):

    uw = UartWrapper(baudrate=baudrate, devname='/dev/ttyUSB1', timeout=0.5)

    # get_temp = uw.simple_command(
    #     NET_ADDR_1_=b'\x01',
    #     DEV_ADDR_2_=b'\x26',
    #     COMMAND_=b'\x03',
    #     REG_ADDR_1_=b'\x00',
    #     REG_ADDR_2_=b'\x20',
    #     value=0x00000001,
    #     name="get_temp"
    # )

    errors = 0
    t1 = time.time()
    state = False
    for i in range(0, num):
        t2 = time.time()
        state = not state
        if(state):
            value = 0x00000001
        else:
            value = 0x00000000
        set_relay = uw.simple_command(
            NET_ADDR_1_=b'\x01',
            DEV_ADDR_2_=b'\x25',
            COMMAND_=b'\x03',
            REG_ADDR_1_=b'\x00',
            REG_ADDR_2_=b'\x30',
            value=value,
            name="set_relay"
        )
        erflag = False
        try:
            ans = uw.send_command(set_relay)
            if not ans:
                errors += 1
                erflag = True
        except Exception:
            errors += 1
            erflag = True
        dt2 = time.time() - t2
        if(erflag):
            print("Error in iteration {} dt = {:5.4f}".format(i, dt2))
        else:
            print("Success in iteration {} dt = {:5.4f}".format(i, dt2))

    dt = time.time() - t1
    print(" baudrate is {}".format(baudrate))
    print("we spent {} sec to do {} reqv and got {} errors".format(dt, num, errors))


def temp_test_baudrate(num = 32, baudrate=57600):

    uw = UartWrapper(baudrate=baudrate, devname='/dev/ttyUSB1', timeout=0.5)

    # get_temp = uw.simple_command(
    #     NET_ADDR_1_=b'\x01',
    #     DEV_ADDR_2_=b'\x26',
    #     COMMAND_=b'\x03',
    #     REG_ADDR_1_=b'\x00',
    #     REG_ADDR_2_=b'\x20',
    #     value=0x00000001,
    #     name="get_temp"
    # )

    errors = 0
    t1 = time.time()
    state = False
    for i in range(0, num):
        t2 = time.time()
        state = not state
        if(state):
            value = 0x00000001
        else:
            value = 0x00000000
        get_temp = uw.simple_command(
            NET_ADDR_1_=b'\x01',
            DEV_ADDR_2_=b'\x26',
            COMMAND_=b'\x03',
            REG_ADDR_1_=b'\x00',
            REG_ADDR_2_=b'\x20',
            value=value,
            name="set_relay"
        )
        erflag = False
        ftemp = -100
        try:
            ans = uw.send_command(get_temp)
            ftemp = uw.get_float_from_slave_message(ans)
            if not ans:
                errors += 1
                erflag = True
        except Exception:
            errors += 1
            erflag = True
        dt2 = time.time() - t2
        if(erflag):
            print("Error in iteration {} dt = {:5.4f}".format(i, dt2))
        else:
            print("Success in iteration {} dt = {:5.4f} ftemp = {:5.2f}".format(i, dt2, ftemp))

    dt = time.time() - t1
    print(" baudrate is {}".format(baudrate))
    print("we spent {} sec to do {} reqv and got {} errors".format(dt, num, errors))


def get_uid_test_baudrate(num = 32, baudrate=57600):

    uw = UartWrapper(baudrate=baudrate, devname='/dev/ttyUSB1', timeout=0.5)

    # get_temp = uw.simple_command(
    #     NET_ADDR_1_=b'\x01',
    #     DEV_ADDR_2_=b'\x26',
    #     COMMAND_=b'\x03',
    #     REG_ADDR_1_=b'\x00',
    #     REG_ADDR_2_=b'\x20',
    #     value=0x00000001,
    #     name="get_temp"
    # )

    errors = 0
    t1 = time.time()
    state = False
    for i in range(0, num):
        t2 = time.time()
        state = not state
        if(state):
            value = 0x00000001
        else:
            value = 0x00000000
        get_temp = uw.simple_command(
            NET_ADDR_1_=b'\x01',
            DEV_ADDR_2_=b'\x22',
            COMMAND_=b'\x01',
            REG_ADDR_1_=b'\x00',
            REG_ADDR_2_=b'\x10',
            value=value,
            name=" "
        )
        erflag = False
        try:
            ans = uw.send_command(get_temp)
            if not ans:
                errors += 1
                erflag = True
        except Exception:
            errors += 1
            erflag = True
        dt2 = time.time() - t2
        if(erflag):
            print("Error in iteration {} dt = {:5.4f}".format(i, dt2))
        else:
            print("Success in iteration {} dt = {:5.4f}".format(i, dt2))

    dt = time.time() - t1
    print(" baudrate is {}".format(baudrate))
    print("we spent {} sec to do {} reqv and got {} errors".format(dt, num, errors))


if __name__ == "__main__":
    #relay_test_baudrate(255)
    temp_test_baudrate(32)
    #get_uid_test_baudrate(32)
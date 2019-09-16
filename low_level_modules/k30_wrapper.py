
import serial
import time
import logging
from asyncio import sleep as asleep

logger = logging.getLogger('Worker.Units.K30.K30Wrapper')

class K30(object):
    """
    Simple wrapper for k30 co2 sensor
    https://www.co2meter.com/products/k-30-co2-sensor-module
    """
    def __init__(self,
                 devname="/dev/ttyUSB0",
                 baudrate=9600,
                 timeout=1
                 ):
        self.devname = devname
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = serial.Serial(
            port=self.devname,
            baudrate=self.baudrate,
            timeout=self.timeout
        )
        self.ser.flushInput()

    def get_data(self):
        """
        Returns co2 in ppm and str description of operation
        :return:
        """
        read_co2_modbus = (b"\x68\x04\x00\x03\x00\x01\xC8\xF3")

        logger.debug("Get data from K-30 via UART")
        self.ser.write(read_co2_modbus)
        logger.debug("Sent: {}".format(read_co2_modbus.hex()))
        # asleep(1)
        resp = self.ser.read(7)
        logger.debug("This is resp : {}".format(resp.hex()))
        high = resp[3]
        low = resp[4]
        co2 = (high * 256) + low
        logger.debug("CO2 = {}".format(co2))
        res = "co2 = {}".format(co2)
        return co2, res


def old_main():

    ser = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=1)  # serial port may vary from pi to pi
    print("Get data from K-30 via UART\n")
    ser.flushInput()
    time.sleep(1)
    cutoff_ppm = 1000  # readings above this will cause the led to turn red

    read_co2 = (b"\xFE\x44\x00\x08\x02\x9F\x25")
    read_temp = (b"\xFE\x44\x00\x12\x02\x94\x45")  # dont work really
    read_rh = (b"\xFE\x44\x00\x14\x02\x97\xE5")
    cmd_init = (b"\xFE\x41\x00\x60\x01\x35\xE8\x53")
    read_co2_modbus = (b"\x68\x04\x00\x03\x00\x01\xC8\xF3")

    for i in range(1, 10):
        ser.flushInput()

        ser.write(read_co2_modbus)
        time.sleep(1)
        resp = ser.read(7)
        # print (type(resp)) #used for testing and debugging
        # print (len(resp))
        # print (resp)
        print ("This is resp : {}".format(resp.hex()))
        high = resp[3]
        low = resp[4]
        # print(high)
        # print(low)
        co2 = (high * 256) + low
        print("i = ", i, " CO2 = " + str(co2))


if __name__ == "__main__":
    old_main()



import sys
import Adafruit_DHT

# We are using DHT11 sensor and Adafruit_DHT library with only one function read_retry

# example how to use
# while True:
#
#     humidity, temperature = Adafruit_DHT.read_retry(11, 4)
#
#     print('Temp: {0:0.1f} C  Humidity: {1:0.1f} %'.format(temperature, humidity))
#

#  read_retry function description from library:
#
# def read_retry(sensor, pin, retries=15, delay_seconds=2, platform=None):
#     """Read DHT sensor of specified sensor type (DHT11, DHT22, or AM2302) on
#     specified pin and return a tuple of humidity (as a floating point value
#     in percent) and temperature (as a floating point value in Celsius).
#     Unlike the read function, this read_retry function will attempt to read
#     multiple times (up to the specified max retries) until a good reading can be
#     found. If a good reading cannot be found after the amount of retries, a tuple
#     of (None, None) is returned. The delay between retries is by default 2
#     seconds, but can be overridden.
#     """
#     for i in range(retries):
#         humidity, temperature = read(sensor, pin, platform)
#         if humidity is not None and temperature is not None:
#             return (humidity, temperature)
#         time.sleep(delay_seconds)
# return (None, None)

# there might be a problem with time.sleep(delay_seconds) in function read_retry
# may be we need to use read function instead

# def read(sensor, pin, platform=None):
#     """Read DHT sensor of specified sensor type (DHT11, DHT22, or AM2302) on
#     specified pin and return a tuple of humidity (as a floating point value
#     in percent) and temperature (as a floating point value in Celsius). Note that
#     because the sensor requires strict timing to read and Linux is not a real
#     time OS, a result is not guaranteed to be returned!  In some cases this will
#     return the tuple (None, None) which indicates the function should be retried.
#     Also note the DHT sensor cannot be read faster than about once every 2 seconds.
#     Platform is an optional parameter which allows you to override the detected
#     platform interface--ignore this parameter unless you receive unknown platform
#     errors and want to override the detection.
#     """
#     if sensor not in SENSORS:
#         raise ValueError('Expected DHT11, DHT22, or AM2302 sensor value.')
#     if platform is None:
#         platform = get_platform()
# return platform.read(sensor, pin)


class DHTWrapper:
    """
    Simple wrapper class for our tasks
    """
    # TODO: we should do retries, because dht can return None instead data sometimes
    def __init__(self, pin: int = 14, DHTTYPE: int = 22):
        self.pin = pin
        self.DHTTYPE = DHTTYPE

    def get_data(self):
        """simple try to read DHT data and if not - write error in log"""
        log = ""
        humidity = None
        temperature = None
        try:
            humidity, temperature = Adafruit_DHT.read_retry(
                sensor=self.DHTTYPE, pin=self.pin, retries=10, delay_seconds=0.05
            )
        except Exception as e:
            log = "We got error {} \n when read DHT{} from pin {} \n"\
                .format(e, self.DHTTYPE, self.pin)
        if not humidity or not temperature:
            log += "We got some trouble - no humidity or no temperature in sensor`s answer\n"
        else:
            log += "We successfully got humidity and temperature from sensor"
        return humidity, temperature, log

if __name__=="__main__":
    d = DHTWrapper()
    data = d.get_data()
    print(data[0], data[1], data[2])

# this module contains methods to get data
# and send commands to SBA-5 CO2 Gas Analyzer
# from PP systems


import serial
import asyncio
# TODO: add logging, its important

class SBAWrapper(object):
    """
    This class wraps all sba commands as a class methods or fields
    """
    def __init__(
            self,
            devname: str = '/dev/ttyUSB0',
            baudrate: int = 19200,
            timeout: float = 10
    ):
        self.dev = devname
        self.baud = baudrate
        self.timeout = timeout

    async def send_command(self, command: str):
        """
        Command must ends with \r\n !
        Its important
        :param command:
        :return:
        """
        """
        To initiate a command, the USB port or RS232 port sends an ASCII character or string.
        A single character command is acted on immediately when the character is received.
        A string command is acted on after the command string terminator <CR> is received. 
        The command can be sent with or without a checksum. If a checksum is sent, a “C” follows 
        the checksum value.
        For example,
        Device sends command without checksum: S,11,1<CR>
        Device sends command with checksum: S,11,1,043C<CR>
        On successfully receiving a command string, the SBA5+ sends an acknowledgement by 
        echoing back to all the ports the Command String and “OK”, each terminated with a <CR> 
        and<linefeed>.
        """
        # \r\n
        try:
            ser = serial.Serial(
                port=self.dev,
                baudrate=self.baud,
                timeout=self.timeout
            )
            bcom = command.encode('utf-8')
            ser.write(bcom)
        except Exception as e:
            print("SBAWrapper error while send command: {}".format(e))
        # then try to read answer
        # it must be two messages, ended with \r\n
        try:
            ser = serial.Serial(
                port=self.dev,
                baudrate=self.baud,
                timeout=self.timeout
            )
            echo = (ser.readline()).decode('utf-8')
            status = (ser.readline()).decode('utf-8')
            return echo+status
        except Exception as e:
            print("SBAWrapper error while read answer from command: {}".format(e))

    async def get_periodic_data(self):
        try:
            ser = serial.Serial(
                port=self.dev,
                baudrate=self.baud,
                timeout=self.timeout
            )
            ans = (ser.readline()).decode('utf-8')
            return ans
        except Exception as e:
            print("SBAWrapper error while read: {}".format(e))


def read():
    ser = serial.Serial(
        port='/dev/ttyUSB0',
        baudrate=19200,
        timeout=10
    )
    while True:
        ans = (ser.readline()).decode('utf-8')
        print(ans)

def send_command(c):
    ser = serial.Serial(
        port='/dev/ttyUSB0',
        baudrate=19200,
        timeout=10
    )
    ser.write(c)
    ans = (ser.readline()).decode('utf-8')
    print(ans)
    ans = (ser.readline()).decode('utf-8')
    print(ans)
    while True:
        ans = (ser.readline()).decode('utf-8')
        print(ans)


async def main():
    s = SBAWrapper()
    res = await s.send_command('!\r\n')
    print(res)

if __name__=="__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
# this module contains methods to get data
# and send commands to SBA-5 CO2 Gas Analyzer
# from PP systems


import serial
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
        self.ser = serial.Serial(
            devname=self.dev,
            baudrate = self.baud,
            timeout=self.timeout
        )

    async def send_command_char(self, command: str):
        """
        It must be one character command, such as "V" - version
        :param command:
        :return:
        """
        """
        To initiate a command, the USB port or RS232 port sends an ASCII character or string.
        A single character command is acted on immediately when the character is received.
        """
        try:
            await self.ser.write(command)
        except Exception as e:
            print("SBAWrapper error while send command: {}".format(e))
        # then try to read answer
        # it must be two messages, ended with \r\n
        try:
            ans = await (self.ser.readline()).decode('utf-8')
            return ans
        except Exception as e:
            print("SBAWrapper error while read answer from command: {}".format(e))


    async def send_command_string(self, command: str):
        """
        Command must ends with \n\r !
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
        # TODO: checks if \n\r will works or \r\n,  i dont know
        try:
            await self.ser.write(command)
        except Exception as e:
            print("SBAWrapper error while send command: {}".format(e))
        # then try to read answer
        # it must be two messages, ended with \r\n
        try:
            echo = await (self.ser.readline()).decode('utf-8')
            status = await (self.ser.readline()).decode('utf-8')
            return status
        except Exception as e:
            print("SBAWrapper error while read answer from command: {}".format(e))

    async def get_periodic_data(self):
        # TODO: check if it really works
        try:
            ans = await (self.ser.readline()).decode('utf-8')
            return ans
        except Exception as e:
            print("SBAWrapper error while read: {}".format(e))


if __name__=="__main__":
    ser = serial.Serial(
        port='/dev/ttyUSB0',
        baudrate=19200,
        timeout=10
    )
    while True:
        ans = (ser.readline()).decode('utf-8')
        print(ans)
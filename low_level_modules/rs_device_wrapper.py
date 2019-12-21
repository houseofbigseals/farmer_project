from typing import Tuple, Optional
import serial
import logging
import six
import sys
import struct
from time import sleep

# there must be uart wrapper object that realizes all
# methods for communication with our rs devices

# Table driver crc16 algorithm.  The table is well-documented and was
# generated in this case by using pycrc (https://github.com/tpircher/pycrc)
# using the following command-line:
#
# ./pycrc.py --model=ccitt --generate table




logger = logging.getLogger('Worker.Units.RS_device_wrapper')
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.CRITICAL)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


CRC16_CCITT_TAB = \
    [
        0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
        0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
        0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
        0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
        0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
        0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
        0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
        0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
        0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
        0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
        0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12,
        0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
        0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41,
        0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
        0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,
        0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
        0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
        0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
        0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
        0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
        0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
        0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
        0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
        0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
        0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
        0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3,
        0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
        0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92,
        0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
        0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,
        0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
        0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0
    ]


class UartWrapper:
    """
    taht class realizes all commands from IGC (Impulse Current Generator)
    documentation as its own methods
    must generate CRC and should be able to parse all commands
    it works as c-style structure - collects everything about uart
    in a big bunch

    # package from master to device - 12 bytes
    #
    # | START_BYTE | DEV_ADDR_LOW | DEV_ADDR_HIGH | COMMAND | REG_ADDR_LOW | REG_ADDR_HIGH |
    # VALUE_1 | VALUE_2 | VALUE_3 | VALUE_4 | CRC16_LOW | CRC16_HIGH |
    #
    # START_BYTE - 1 byte - everytime is 0xCA
    # DEV_ADDR - 2 bytes - to what device
    # COMMAND - 1 byte - what to do
    # REG_ADDR - 2 bytes - to what register
    # VALUE - 4 bytes - what to write in that register
    # CRC16 - 2 bytes - crc16 sum of package
    #
    # package from device to master - 11 bytes
    #
    # | START_BYTE | DEV_ADDR_LOW | DEV_ADDR_HIGH | STATUS_LOW | STATUS_HIGH |
    # VALUE_1 | VALUE_2 | VALUE_3 | VALUE_4 | CRC16_LOW | CRC16_HIGH |
    #
    # START_BYTE - 1 byte - everytime is 0xCA
    # DEV_ADDR - 2 bytes - to what device
    # STATUS - 2 bytes - status of command execution
    # VALUE - 4 bytes - result of command execution
    # CRC16 - 2 bytes - crc16 sum of package

    """
    def __init__(self,
                 devname: str = '/dev/ttyUSB0',
                 baudrate: int = 9600,
                 timeout: float = 10
                 ):
        self.dev = devname
        self.baud = baudrate
        self.timeout = timeout
        self.master_command_len = 12
        self.slave_command_len = 11



    def send_command(self,
                     com: bytearray,
                     log_comment: str = None
                     ) -> Optional[bytearray]:
        ans = None
        logger.debug("-------------------------------")
        if(log_comment):
            logger.debug("Sending mm {}".format(log_comment))
        else:
            logger.debug("We want to send this:")
        logger.debug(self.parse_master_message(com))
        try:
            ser = serial.Serial(port=self.dev, baudrate=self.baud, timeout=self.timeout)
            ser.write(com)
        except Exception as e:
            logger.debug("Error happened while write: {}".format(e))
            logger.debug("-------------------------------")
            return ans

        try:
            ans = ser.read(self.slave_command_len)
        except Exception as e:
            logger.debug("Error happened while read: {}".format(e))
            logger.debug("-------------------------------")
            return ans

        if(not ans or (len(ans) != self.slave_command_len)):
            logger.debug("Broken answer from GIC: {}".format(ans))
            logger.debug("-------------------------------")
        else:
            logger.debug("Succesfully got answer from rs_device:")
            logger.debug(self.parse_slave_message(ans))
        return ans

    def parse_slave_message(self, com: bytearray) -> None:
        # parse content of slave message
        length = len(com)
        logger.debug("-------------------------------")
        logger.debug("Parsed slave message {} ".format(com.hex()))
        logger.debug("{} - START_BYTE ".format(hex(com[0])))
        logger.debug("{} - DEV_ADDR_1 ".format(hex(com[1])))
        logger.debug("{} - DEV_ADDR_2 ".format(hex(com[2])))
        logger.debug("{} - STATUS_1".format(hex(com[3])))
        logger.debug("{} - STATUS_2".format(hex(com[4])))
        logger.debug("{} - VALUE_1".format(hex(com[5])))
        logger.debug("{} - VALUE_2".format(hex(com[6])))
        logger.debug("{} - VALUE_3".format(hex(com[7])))
        logger.debug("{} - VALUE_4".format(hex(com[8])))
        logger.debug("{} - CRC16_1".format(hex(com[9])))
        logger.debug("{} - CRC16_2".format(hex(com[10])))
        logger.debug("-------------------------------")

    def parse_master_message(self, com: bytearray) -> None:
        # parse content of master message
        length = len(com)
        logger.debug("-------------------------------")
        logger.debug("Parsed master message {} ".format(com.hex()))
        logger.debug("{} - START_BYTE ".format(hex(com[0])))
        logger.debug("{} - DEV_ADDR_1 ".format(hex(com[1])))
        logger.debug("{} - DEV_ADDR_2 ".format(hex(com[2])))
        logger.debug("{} - COMMAND".format(hex(com[3])))
        logger.debug("{} - REG_ADDR_1".format(hex(com[4])))
        logger.debug("{} - REG_ADDR_2".format(hex(com[5])))
        logger.debug("{} - VALUE_1".format(hex(com[6])))
        logger.debug("{} - VALUE_2".format(hex(com[7])))
        logger.debug("{} - VALUE_3".format(hex(com[8])))
        logger.debug("{} - VALUE_4".format(hex(com[9])))
        logger.debug("{} - CRC16_1".format(hex(com[10])))
        logger.debug("{} - CRC16_2".format(hex(com[11])))
        logger.debug("-------------------------------")

    # uint8_t START_BYTE;
    # uint8_t NET_ADDR_1;
    # uint8_t DEV_ADDR_2;
    # uint8_t VALUE_1;
    # uint8_t VALUE_2;
    # uint8_t VALUE_3;
    # uint8_t VALUE_4;
    # uint8_t REG_ADDR_1;
    # uint8_t REG_ADDR_2;
    # uint8_t COMMAND;
    # uint8_t CRC_16_1;
    # uint8_t CRC_16_2;

    def create_master_command(self,
                                START_BYTE: bytes = b'\xCA',
                                NET_ADDR_1: bytes = None,
                                DEV_ADDR_2: bytes = None,
                                COMMAND: bytes = None,
                                REG_ADDR_1: bytes = None,
                                REG_ADDR_2: bytes = None,
                                VALUE_1: bytes = None,
                                VALUE_2: bytes = None,
                                VALUE_3: bytes = None,
                                VALUE_4: bytes = None,
                                CRC_16_1: bytes = None,
                                CRC_16_2: bytes = None,


                       ) -> bytearray:
        command = bytearray()
        # print("preamble ", preamble)
        command.extend(START_BYTE)
        # print("direction ", direction)
        command.extend(NET_ADDR_1)
        command.extend(DEV_ADDR_2)
        command.extend(COMMAND)
        command.extend(REG_ADDR_1)
        command.extend(REG_ADDR_2)
        command.extend(VALUE_1)
        command.extend(VALUE_2)
        command.extend(VALUE_3)
        command.extend(VALUE_4)
        if CRC_16_1 and CRC_16_2:
            command.extend(CRC_16_1)
            command.extend(CRC_16_2)
        else:
            crc_raw = self.crc16_ccitt(command)
            # print("crc_raw ", hex(crc_raw))
            crc_bytes = crc_raw.to_bytes(2, byteorder='big')  # byteorder='little'
            # its important
            # print("crc_bytes ", crc_bytes)
            command.extend(crc_bytes)
        return command

    def crc16_ccitt(self, data_, crc=0xffff) -> int:
        """Calculate the crc16 ccitt checksum of some data
        A starting crc value may be specified if desired.  The input data
        is expected to be a sequence of bytes (string) and the output
        is an integer in the range (0, 0xFFFF).  No packing is done to the
        resultant crc value.  To check the value a checksum, just pass in
        the data byes and checksum value.  If the data matches the checksum,
        then the resultant checksum from this function should be 0.
        """
        tab = CRC16_CCITT_TAB  # minor optimization (now in locals)
        for byte in six.iterbytes(data_):
            crc = (((crc << 8) & 0xff00) ^ tab[((crc >> 8) & 0xff) ^ byte])
        return crc & 0xffff

    def simple_command(self,
                       NET_ADDR_1_: bytes,
                       DEV_ADDR_2_: bytes,
                       COMMAND_: bytes,
                       REG_ADDR_1_: bytes,
                       REG_ADDR_2_: bytes,
                       value: int,
                       name: str = None
                       ) -> Optional[bytearray]:
        # there is a simple command template
        # lets split value to 4 bytes
        value_bytes = value.to_bytes(4, byteorder='big')
        command = self.create_master_command(
            NET_ADDR_1 = NET_ADDR_1_,
            DEV_ADDR_2 = DEV_ADDR_2_,
            COMMAND = COMMAND_,
            REG_ADDR_1 = REG_ADDR_1_,
            REG_ADDR_2 = REG_ADDR_2_,
            VALUE_1 = (value_bytes[0]).to_bytes(1, 'big'),
            VALUE_2 = (value_bytes[1]).to_bytes(1, 'big'),
            VALUE_3 = (value_bytes[2]).to_bytes(1, 'big'),
            VALUE_4 = (value_bytes[3]).to_bytes(1, 'big'),
        )
        #ans = self.send_command(command, log_comment=name)
        return command

    def four_bytes_to_float(self,
                       values : bytearray
                       ) -> float:

        return struct.unpack('>f', values)[0]

    def get_float_from_slave_message(self,
                       sm : bytearray
                       ) -> float:
        values = sm[5:9]
        return struct.unpack('>f', values)[0]

if __name__ == "__main__":
    # Droot = logging.getLogger()


    uw = UartWrapper(baudrate=115200, devname='/dev/ttyUSB1')

    set_relay = uw.simple_command(
        NET_ADDR_1_= b'\x01',
        DEV_ADDR_2_= b'\x24',
        COMMAND_= b'\x03',
        REG_ADDR_1_= b'\x00',
        REG_ADDR_2_= b'\x30',
        value= 0x00000000,
        name="set_relay"
    )

    get_uid = uw.simple_command(
        NET_ADDR_1_=b'\x01',
        DEV_ADDR_2_=b'\x24',
        COMMAND_=b'\x01',
        REG_ADDR_1_=b'\x00',
        REG_ADDR_2_=b'\x10',
        value=0x00000001,
        name="get_uid"
    )

    get_temp = uw.simple_command(
        NET_ADDR_1_= b'\x01',
        DEV_ADDR_2_= b'\x26',
        COMMAND_= b'\x03',
        REG_ADDR_1_= b'\x00',
        REG_ADDR_2_= b'\x20',
        value= 0x00000001,
        name="get_temp"
    )

    get_hum = uw.simple_command(
        NET_ADDR_1_=b'\x01',
        DEV_ADDR_2_=b'\x26',
        COMMAND_=b'\x03',
        REG_ADDR_1_=b'\x00',
        REG_ADDR_2_=b'\x21',
        value=0x00000001,
        name="get_hum "
    )
    #uw.parse_master_message(get_uid)
    #uw.send_command(get_uid, "get_uid")
    #uw.send_command(set_relay, "get_uid")
    #uw.send_command(get_hum, "get_uid")
    #uw.send_command(get_temp, "get_uid")
    #uw.parse_slave_message(answer)

    # example of converting 4 bytes to float
    # 3.141566 =  0x40 , 0x49, 0x0F , 0x6A

    command = bytearray()
    # print("preamble ", preamble)
    command.extend(b'\x40')
    # print("direction ", direction)
    command.extend(b'\x49')
    command.extend(b'\x0F')
    command.extend(b'\x6A')
    float_res = uw.four_bytes_to_float(command)
    print(command, float_res)



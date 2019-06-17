
import serial
from typing import Tuple, Optional
import six
import time
from time import sleep

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


class ArdWrapper(object):
    """
    Wrapper for custom bbb protocol

    Format of message from pc to ard

    | COMMON_SIGN | START_BYTE | ADDR | COMMAND | ARGS ... | STOP_BYTE | CRC_LOW | CRC_HIGH |
    --------------------------------------------------------------------------------------------------

    Format of answer from ard to pc
    | COMMON_SIGN | START_BYTE | ADDR | COMMAND | ANS OR ERR | STOP_BYTE | CRC_LOW | CRC_HIGH |
    --------------------------------------------------------------------------------------------------

    max length of message is 32 bytes

    COMMON_SIGN - common for all commands and answers - 0xAA - 1 byte
    START_BYTE - 0x45 for message and 0x54 for answer - 1 byte
    ADDR - address of unit to which the instruction is directed (from which) 0x01 - 0xFE - 1 byte
        0xFF - broadcasting
        0x00 - reserved
    COMMAND - command name - 0x00 - 0xFF - 1 byte
        0x00 - start normal work with schedule
            answer - OK
        0x01 - stop work with schedule and wait for commands
            answer - OK
        0x02 - send back list of all available methods as bytestring
            answer - OK - bytes of all available methods as bytestring
        0x03 - set lamp on
            answer - OK
        0x04 - set lamp
            answer - OK
        0x05 - set pump on
            answer - OK
        0x06 - set pump off
            answer - OK
        0x07 - set ventilation on
            answer - OK
        0x08 - set ventilation off
            answer - OK
        0x09 - get time from RTC
            answer - | OK | year_low | year_high | month | day | hour | min | sec |
        0x10 - set RTC time
            args - ?
            answer - ?
            (for future)
        0x11 - get temp and humidity
            answer - | OK | temp_low | temp_high | hum_low | hum_high |
        0x12 - get temp from ds18b20
            answer - | OK | temp in four bytes - as it is positive float |
        0x13 - get ping
            answer - OK
        0x14 - get firmware and system info
            answer - | OK | firmware version | smth else |
        0x15 - get schedule
            answer - | OK | type of schedule | pump work time | pump sleep time |
                    | lamp work time | lamp sleep time | vent work time | vent sleep time |
        0x16 - set schedule
            args - | number of schedule | pump work time | pump sleep time |
                    | lamp work time | lamp sleep time | vent work time | vent sleep time |
            answer - OK

    STOP_BYTE - common for messages and answers - 0xFA - 1 byte
    CRC_LOW and CRC_HIGH  - low and high bytes of CRC 16 CCITT, counted
                            for all message, with using fast crc table - 2 bytes
    ANS_OR_ERR - answer body or error code
        0x01 - OK
            and then goes bytes of answer
        0x02 - ERROR_INDICATOR - all err messages start with it
            0x00 - invalid data error, problem with broken format of message
            0x01 - invalid crc summ
            0x02 - invalid command - not from available list
            0x03 - invalid argument for correct command
            0x04 - error during command execution
            0xBB - unknown error, something went wrong




    """
    def __init__(self,
                 devname: str = '/dev/ttyUSB0',
                 baudrate: int = 9600,
                 timeout: float = 1
                 ):
        self.dev = devname
        self.baud = baudrate
        self.timeout = timeout
        self.max_len = 32

    def send_command(self,
                     com: bytearray,
                     log_comment: str = None
                     ) -> Tuple[Optional[bytearray], str]:
        ans = None
        logstring = "-------------------------------\n"
        if(log_comment):
            logstring += "Sending {}\n".format(log_comment)
        else:
            logstring += "We want to send this:\n"
            print("We want to send {}".format(com.hex()))
        logstring += self.parse_command(com)
        try:
            ser = serial.Serial(port=self.dev, baudrate=self.baud, timeout=self.timeout)
            ser.flushInput()
            ser.flushOutput()
            ser.write(com)
        except Exception as e:
            logstring += "Error happened while write: {}\n".format(e)
            logstring += "-------------------------------\n"
            return ans, logstring

        try:
            # we dont know whats len of answer, so we wait for
            # message with maximum length
            ans = ser.read(self.max_len)

        except Exception as e:
            logstring += "Error happened while read: {}\n".format(e)
            logstring += "-------------------------------\n"
            return ans, logstring

        if not ans:
            logstring += "Broken answer from ard: {}\n".format(ans)
            logstring += "-------------------------------\n"
        else:
            logstring += "Succesfully got answer from ard:\n"
            logstring += self.parse_command(ans)
        print("send command done")
        return ans, logstring

    def parse_command(self, com: bytearray) -> str:
        print("parse command started")
        # parse content of command
        length = len(com)
        print("len of com is {}".format(length))
        print("com in hex {}".format(com.hex()))
        print(type(com[2]))
        parsed_output = ""
        parsed_output += "-------------------------------\n"
        parsed_output += "Parsed command {} \n".format(com.hex())
        parsed_output += "{} - common sign byte \n".format(hex(com[0]))
        parsed_output += "{} - start byte\n".format(hex(com[1]))
        parsed_output += "{} - address of unit\n".format(hex(com[2]))
        parsed_output += "{} - type of command\n".format(hex(com[3]))
        if com[4] != 0xFA:
            i = 4
            while com[i] != 0xFA:
                # parse args of command
                parsed_output += "{} - data byte\n".format(hex(com[i]))
                i += 1
            parsed_output += "{} - stop byte\n".format(hex(com[i]))
        else:
            parsed_output += "{} - stop byte\n".format(hex(com[4]))
        parsed_output += "{} - last byte of CRC16 ccitt control sum\n".format(hex(com[length - 2]))
        parsed_output += "{} - first byte of CRC16 ccitt control sum\n".format(hex(com[length - 1]))
        parsed_output += "-------------------------------\n"
        print("parse command done")
        return parsed_output

    def create_command(self,
                       common_sign: bytes = b'\xAA',
                       start_byte: bytes = b'\x45',
                       address: bytes = b'\xFF',
                       commandt: bytes = b'\x14', # get info for example
                       data: bytes = None,
                       stop_byte: bytes = b'\xFA'
                       ) -> bytearray:
        command = bytearray()
        command.extend(common_sign)
        command.extend(start_byte)
        command.extend(address)
        command.extend(commandt)
        if data:
            command.extend(data)
        command.extend(stop_byte)
        # crc should be calculated after all
        crc_raw = self.crc16_ccitt(command)
        crc_bytes = crc_raw.to_bytes(2, byteorder='little')  # byteorder='little'
        # its important
        command.extend(crc_bytes)
        print("create command done")
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
                       address: bytes = b'\xFF',
                       commandt: bytes = b'\x14',
                       data: bytes = None,
                       name: str = "get firmware info"
                       ) -> Tuple[Optional[bytearray], str]:
        # this is a simple command template
        print("simple command started")
        command = self.create_command(
            address=address,
            commandt=commandt,
            data=data)
        ans, log = self.send_command(command, log_comment=name)
        print("ans in hex {}".format(ans.hex()))
        print(log)
        if ans:
            answer = bytearray(ans)
            flag = answer[4]
            if flag == 0x01:
                log += "There is OK flag in answer \n"
                log += "-------------------------------\n"
            if flag == 0x02:
                log += "There is ERROR flag in answer \n"
                log += "Something went wrong in ard \n"
                if answer[5] == 0x00:
                    log += "0x00 - invalid data error, problem with broken format of message \n"
                elif answer[5] == 0x01:
                    log += "0x01 - invalid crc summ\n"
                elif answer[5] == 0x02:
                    log += "0x02 - invalid command - not from available list\n"
                elif answer[5] == 0x03:
                    log += "0x03 - invalid argument for correct command\n"
                elif answer[5] == 0x04:
                    log += "0x04 - error during command execution\n"
                elif answer[5] == 0xAA:
                    log += "0xAA - unknown error, something went wrong\n"
                else:
                    log += "0x{} - unknown code of error\n".format(hex(answer[5]))
                log += "-------------------------------\n"
            print("simple command done")
            return ans, log
        else:
            log += "Something went wrong, we got no answer at all\n"
            log += "-------------------------------\n"
            print("simple command done")
            return ans, log

    def start(self, addr: bytes = b'\x05') -> Tuple[Optional[bytearray], str]:
        return self.simple_command(
                        address=addr,
                        commandt=b'\x00',
                        data=None,
                        name="start auto mode"
                       )

    def stop(self, addr: bytes = b'\x05') -> Tuple[Optional[bytearray], str]:
        return self.simple_command(
                        address=addr,
                        commandt=b'\x01',
                        data=None,
                        name="stop auto mode"
                       )

    def set_lamp_on(self, addr: bytes = b'\x05') \
            -> Tuple[Optional[bytearray], str]:
        return self.simple_command(
                        address=addr,
                        commandt=b'\x03',
                        data=None,
                        name="set lamp on"
                       )

    def set_lamp_off(self, addr: bytes = b'\x05') \
            -> Tuple[Optional[bytearray], str]:
        return self.simple_command(
                        address=addr,
                        commandt=b'\x04',
                        data=None,
                        name="set lamp off"
                       )

    def set_pump_on(self, addr: bytes = b'\x05') \
            -> Tuple[Optional[bytearray], str]:
        return self.simple_command(
                        address=addr,
                        commandt=b'\x05',
                        data=None,
                        name="set pump on"
                       )

    def set_pump_off(self, addr: bytes = b'\x05') \
            -> Tuple[Optional[bytearray], str]:
        return self.simple_command(
                        address=addr,
                        commandt=b'\x06',
                        data=None,
                        name="set pump off"
                       )

    def set_vent_on(self, addr: bytes = b'\x05') \
            -> Tuple[Optional[bytearray], str]:
        return self.simple_command(
            address=addr,
            commandt=b'\x07',
            data=None,
            name="set vent on"
        )

    def set_vent_off(self, addr: bytes = b'\x05') \
            -> Tuple[Optional[bytearray], str]:
        return self.simple_command(
            address=addr,
            commandt=b'\x08',
            data=None,
            name="set vent off"
        )


def main():
    ard = ArdWrapper()
    # print(ard.stop()[0])
    # print(ard.set_lamp_on()[0])
    while True:
        print(ard.stop()[0])
        print(ard.set_pump_on()[0])
        print(ard.set_lamp_on()[0])

        print(ard.set_vent_on()[0])
    # print(ard.set_lamp_on()[1])
        time.sleep(1)
        print(ard.set_pump_off()[0])
        print(ard.set_lamp_off()[0])

        print(ard.set_vent_off()[0])
    # print(ard.set_lamp_on()[1])


if __name__ == "__main__":
    main()


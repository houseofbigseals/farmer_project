
# file to find correct version of worker - for rpi or for x86_64
# you should start worker from here

from platform import uname
from non_rpi_worker import non_rpi_main
from rpi_worker import rpi_main
import asyncio


async def start_check():
    system_info = uname()
    if system_info[0] != 'Linux':
        print("The program should be run on Linux system strictly")
    elif 'arm' not in system_info[4]:
        print("The program should be run on raspberry platform")
        print("Run x86_64 compatible version")
        await non_rpi_main()
    elif 'arm' in system_info[4]:
        print("Run raspberry compatible version")
        await non_rpi_main()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_check())
    loop.run_forever()

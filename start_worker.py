
# file to find correct version of worker - for rpi or for x86_64
# you should start worker from here

from platform import uname
from non_rpi_worker import non_rpi_main
from rpi_worker import rpi_main
import asyncio
import argparse


async def start_check():

    parser = argparse.ArgumentParser(
        description="Worker, that can parse tickets from server",
        epilog="Do not forget to print &, to start process in the background."
    )
    parser.add_argument('-H', '--host', type=str, default="83.220.174.247", help='server host ipv4 such as 127.0.0.1')
    parser.add_argument('-P', '--port', type=int, default=8888, help='server port number such as 8888')
    parser.add_argument('-I', '--id', type=int, default=155167253286217647024261323245457212920
                        , help='int UUID number for worker')
    ns = parser.parse_args()

    system_info = uname()
    if system_info[0] != 'Linux':
        print("The program should be run on Linux system strictly")
    elif 'arm' not in system_info[4]:
        print("The program should be run on raspberry platform")
        print("Run x86_64 compatible version")
        await non_rpi_main(
            host=ns.host,
            port=ns.port,
            wid=ns.id
        )
    elif 'arm' in system_info[4]:
        print("Run raspberry compatible version")
        await rpi_main()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_check())
    loop.run_forever()

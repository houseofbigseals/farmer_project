
# wrapper for correct server starting

import asyncio
from raw_server import Server
import argparse
import logging


async def main():
    parser = argparse.ArgumentParser(
        description="Simple server for fitostand remote control. It "
                    "contains list of tickets, that should be done "
                    "by worker. Worker and user client both send commands "
                    "to server to get and set tickets",
        epilog="Do not forget to print &, to start process in the background."
    )
    parser.add_argument('-H', '--host', type=str, default="83.220.174.247", help='host ipv4 such as 127.0.0.1')
    parser.add_argument('-P', '--port', type=int, default=8888, help='port number such as 8888')
    parser.add_argument('-D', '--debug', action='store_true', help='set debug output to server.log')
    ns = parser.parse_args()
    # create logger
    logger = logging.getLogger("Server")
    if ns.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # create the logging file handler
    fh = logging.FileHandler("server.log")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    # add handler to logger object
    logger.addHandler(fh)


    server = Server(
        host=ns.host,
        port=ns.port
    )
    logger.info("Server started\n=============================================================")
    await server.serve_forever()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()
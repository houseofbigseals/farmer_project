
# file to find correct version of worker - for rpi or for x86_64
# you should start worker from here

from async_modules.ard_worker import main
import asyncio
import argparse
import logging


async def start_check():

    parser = argparse.ArgumentParser(
        description="Worker, that can parse tickets from server",
        epilog="Do not forget to print &, to start process in the background."
    )
    parser.add_argument('-H', '--host', type=str, default="83.220.174.247", help='server host ipv4 such as 127.0.0.1')
    parser.add_argument('-P', '--port', type=int, default=8888, help='server port number such as 8888')
    parser.add_argument('-I', '--id', type=int, default=155167253286217647024261323245457212940
                        , help='int UUID number for worker')
    parser.add_argument('-D', '--debug', action='store_true', help='set debug output to worker.log')
    ns = parser.parse_args()

    # create logger
    logger = logging.getLogger("Worker")
    if ns.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # create the logging file handler
    fh = logging.FileHandler("worker.log")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    # add handler to logger object
    logger.addHandler(fh)

    # system_info = uname()
    # if system_info[0] != 'Linux':
    #     logger.info("The program should be run on Linux system strictly")
    # elif 'arm' not in system_info[4]:
    #     logger.info("The program should be run on raspberry platform")
    #     logger.info("Run x86_64 compatible version")
    #     await non_rpi_main(
    #         host=ns.host,
    #         port=ns.port,
    #         wid=ns.id
    #     )
    # elif 'arm' in system_info[4]:
    #     logger.info("Run raspberry compatible version")
    #     try:
    #         # TODO: fix that crutch
    #         await rpi_main()
    #     except Exception as e:
    #         print(e)
    #         logger.error(e)
    await main(
        host=ns.host,
        port=ns.port,
        wid=ns.id
    )



if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_check())
    loop.run_forever()

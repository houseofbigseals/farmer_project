# simple wrapper for user client


from network_modules.raw_client import command_get_server_info\
    , command_get_ticket_result, command_add_ticket\
    , command_delete_ticket

from network_modules.command import Command, Ticket
import asyncio
import json
import time


async def user_main():
    print("\n-----------------------------------------------------")
    tasks_list = []
    # example uuid for worker =155167253286217647024261323245457212920
    # 155167253286217647024261323245457212926
    ans = await command_get_server_info(host="83.220.174.247", port=8888)
    print(ans.header)
    print(ans.body)
    print("Now we have {} tickets on server".format(json.loads(ans.body)["tickets_number"]))

    tasks_list = json.loads(ans.body)["tickets_ids"]

    for tid in tasks_list:
        res = await command_get_ticket_result(tid, host="83.220.174.247", port=8888)
        print(res.header)
        print(res.body)
        # if res.body and "Linux" in res.body:
        #     ans = await command_delete_ticket(tid)
        # print(ans.header)
        # print(ans.body)


async def user_main2():
    ans = await command_get_server_info(host="83.220.174.247", port=8888)
    print(ans.header)
    print(ans.body)
    print("Now we have {} tickets on server".format(json.loads(ans.body)["tickets_number"]))
    # com = Command(
    #     cunit="led_unit",
    #     cfunc="set_current",
    #     cargs={"red":10, "white":100},
    #     ctype="single"
    # )
    com = Command(
        cunit="led_unit",
        cfunc="stop",
        cargs=None,
        ctype="single"
    )
    # com = Command(
    #     cunit="system_unit",
    #     cfunc="get_info",
    #     cargs=None,
    #     ctype="single"
    #)
    tick = Ticket(
        tfrom=10,
        tto=155167253286217647024261323245457212920,
        tid=None,
        tcommand=com.cdict,
        tresult=None
    )
    ans = await command_add_ticket(tick, host="83.220.174.247", port=8888)
    print(ans.header)
    print(ans.body)


async def user_main3(n=1000):
    start_time = time.time()
    tasks_list = []
    # example uuid for worker =155167253286217647024261323245457212920
    # 155167253286217647024261323245457212926
    for i in range(0, n):
        ans = await command_get_server_info(host="83.220.174.247", port=8888)
        #ans = await command_get_server_info()
    end_time = time.time()
    print("we did {} requests, it spent {} sec".format(n, end_time-start_time))


async def test_co2():
    ans = await command_get_server_info(host="83.220.174.247", port=8888)
    print(ans.header)
    print(ans.body)
    print("Now we have {} tickets on server".format(json.loads(ans.body)["tickets_number"]))
    # com = Command(
    #     cunit="led_unit",
    #     cfunc="set_current",
    #     cargs={"red":10, "white":100},
    #     ctype="single"
    # )
    com = Command(
        cunit="co2_sensor_unit",
        cfunc="do_command",
        cargs={"com": "M\r\n"},
        ctype="single"
    )
    # com = Command(
    #     cunit="system_unit",
    #     cfunc="get_info",
    #     cargs=None,
    #     ctype="single"
    # )
    tick = Ticket(
        tfrom=10,
        tto=155167253286217647024261323245457212920,
        tid=None,
        tcommand=com.cdict,
        tresult=None
    )
    ans = await command_add_ticket(tick, host="83.220.174.247", port=8888)
    print(ans.header)
    print(ans.body)

    while True:
        ans = await command_get_ticket_result(tick.id, host="83.220.174.247", port=8888)
        print(ans.header)
        print(ans.body)
        if not ans.body or ans.body == "at_work":
            time.sleep(1)
        else:
            break
    ans = await command_delete_ticket(tick.id, host="83.220.174.247", port=8888)
    print(ans.header)
    print(ans.body)

async def test_gpio():
    ans = await command_get_server_info(host="83.220.174.247", port=8888)
    print(ans.header)
    print(ans.body)
    print("Now we have {} tickets on server".format(json.loads(ans.body)["tickets_number"]))
    com = Command(
        cunit="gpio_unit",
        cfunc="start_ventilation",
        cargs=None,
        ctype="single"
    )
    # com = Command(
    #     cunit="gpio_unit",
    #     cfunc="set_pin",
    #     cargs={"pin": 17, "state": True},
    #     ctype="single"
    # )
    tick = Ticket(
        tfrom=10,
        tto=155167253286217647024261323245457212920,
        tid=None,
        tcommand=com.cdict,
        tresult=None
    )
    ans = await command_add_ticket(tick, host="83.220.174.247", port=8888)
    print(ans.header)
    print(ans.body)
    time.sleep(10)
    ans = await command_get_ticket_result(tick.id, host="83.220.174.247", port=8888)
    print(ans.header)
    print(ans.body)
    ans = await command_delete_ticket(tick.id, host="83.220.174.247", port=8888)
    print(ans.header)
    print(ans.body)

async def test_tunnel():
    ans = await command_get_server_info(host="83.220.174.247", port=8888)
    print(ans.header)
    print(ans.body)
    print("Now we have {} tickets on server".format(json.loads(ans.body)["tickets_number"]))
    com = Command(
        cunit="system_unit",
        cfunc="get_info",
        cargs=None,
        ctype="single"
    )
    tick = Ticket(
        tfrom=10,
        tto=155167253286217647024261323245457212920,
        tid=None,
        tcommand=com.cdict,
        tresult=None
    )
    ans = await command_add_ticket(tick, host="83.220.174.247", port=8888)
    print(ans.header)
    print(ans.body)
    time.sleep(20)
    ans = await command_get_ticket_result(tick.id, host="83.220.174.247", port=8888)
    print(ans.header)
    print(ans.body)
    ans = await command_delete_ticket(tick.id, host="83.220.174.247", port=8888)
    print(ans.header)
    print(ans.body)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    # loop.run_until_complete(test_tunnel())
    loop.run_until_complete(test_gpio())
    # loop.run_until_complete(test_co2())

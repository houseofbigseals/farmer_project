# simple wrapper for user client


from pseudo_client import command_get_server_info\
    , command_set_ticket_result, command_get_ticket_result, command_add_ticket\
    , command_delete_ticket

from command import Message, Command, Ticket
from tasks import PeriodicTask, SingleTask, LongSingleTask, PeriodicCoro
import asyncio
import json


async def user_main():
    print("\n-----------------------------------------------------")
    tasks_list = []
    # example uuid for worker =155167253286217647024261323245457212920
    # 155167253286217647024261323245457212926
    ans = await command_get_server_info()
    print(ans.header)
    print(ans.body)
    print("Now we have {} tickets on server".format(json.loads(ans.body)["tickets_number"]))

    tasks_list = json.loads(ans.body)["tickets_ids"]

    for tid in tasks_list:
        res = await command_get_ticket_result(tid)
        print(res.header)
        print(res.body)
        if res.body and "Linux" in res.body:
            ans = await command_delete_ticket(tid)
            print(ans.header)
            print(ans.body)


async def user_main2():
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

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(user_main2())
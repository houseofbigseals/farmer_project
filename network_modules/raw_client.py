import asyncio
import json
from network_modules.command import Command, Ticket, Message
from typing import Any
import logging

logger = logging.getLogger("Worker.RawClient")


class ClientProtocol(asyncio.Protocol):
    def __init__(self, on_con_lost, placeholder):
        # self.message = message
        self.result = None
        self.placeholder = placeholder
        self.on_con_lost = on_con_lost
        self.transport = None
        self.address = None

    def connection_made(self, transport):
        self.transport = transport
        self.address = transport.get_extra_info('peername')
        logger.debug('Accepted connection from {}'.format(self.address))

    def send_message(self, message):
        # transport.write(self.message.encode())
        message = message.encode()
        self.transport.write(message)
        logger.debug('Data sent: {!r}'.format(message))

    def data_received(self, data):
        asyncio.ensure_future(self.handle_incoming(data))

    async def handle_incoming(self, data):
        self.result = data
        # TODO: fix that ugly crutch
        self.placeholder[0] = data.decode()
        logger.debug('Data received: {!r}'.format(data.decode()))
        return self.result

    def connection_lost(self, exc):
        if exc:
            logger.debug('Client {} error: {}'.format(self.address, exc))
        logger.debug('The server closed the connection')
        self.on_con_lost.set_result(True)


async def send_command_to_server(
        message: Message = Message(),
        host: str = '127.0.0.1',
        port: int = 8888
        ):
    """
    wrapper-constructor for create commands and send them to server
    in format of Message object

    :param message: Message = Message()
    :param host: str = '127.0.0.1'
    :param port: str = "ADD_TICKET"
    :param data: Any
    :return: result : Any
    """
    loop = asyncio.get_event_loop()
    on_con_lost = loop.create_future()
    message_str = json.dumps(message.mdict)
    result = [None]
    transport, protocol = await loop.create_connection(
        lambda: ClientProtocol(on_con_lost, result),
        host, port)
    #, local_addr = ("localhost39000", 39000)
    # Wait until the protocol signals that the connection
    # is lost and close the transport.
    try:
        protocol.send_message(message_str)
        await on_con_lost
    finally:
        transport.close()
        return result[0]


# async def main_test_GET_SERVER_INFO():
#     # com = Command()
#     # tick = Ticket(tfrom=1, tto=2, tcommand=com)
#     res = await send_command_to_server()
#     # print("we really got {} from server".format(res))
#     answer = Message(**json.loads(res))
#     print(answer.header)
#     print(answer.body)
#
#
# async def main_test_ADD_TICKET(tick):
#     message = Message(header="ADD_TICKET", body=tick.tdict)
#     res = await send_command_to_server(message=message)
#     # print("we really got {} from server".format(res))
#     answer = Message(**json.loads(res))
#     print(answer.header)
#     print(answer.body)
#
#
# async def main_test_DELETE_TICKET(tick):
#     message = Message(header="DELETE_TICKET", body={"id": tick.tdict["tid"]})
#     res = await send_command_to_server(message=message)
#     # print("we really got {} from server".format(res))
#     answer = Message(**json.loads(res))
#     print(answer.header)
#     print(answer.body)
#
#
# async def main_test_REQUEST_TICKETS(worker_id):
#     message = Message(header="REQUEST_TICKETS", body={"id": worker_id})
#     res = await send_command_to_server(message=message)
#     # print("we really got {} from server".format(res))
#     answer = Message(**json.loads(res))
#     dicts_list = json.loads(answer.body)
#     print(answer.header)
#     # print(type(json.loads(answer.body)))
#     # print(type(answer.body[0]))
#     tickets_list = [Ticket(**t_dict) for t_dict in dicts_list]
#     for t in tickets_list:
#         print(t.id, t.to, t.tfrom)
#
#
# async def main_test_GET_TICKET_RESULT(ticket_id):
#     message = Message(header="GET_TICKET_RESULT", body={"id": ticket_id})
#     res = await send_command_to_server(message=message)
#     answer = Message(**json.loads(res))
#     print(answer.header)
#     print(answer.body)
#
#
# async def main_test_SET_TICKET_RESULT(ticket_id, result):
#     message = Message(header="SET_TICKET_RESULT", body={"id": ticket_id, "result": result})
#     res = await send_command_to_server(message=message)
#     answer = Message(**json.loads(res))
#     print(answer.header)
#     print(answer.body)

# wrappers for using in outside modules


async def command_get_server_info(
        host: str = '127.0.0.1',
        port: int = 8888
):
    message = Message(header="GET_SERVER_INFO", body={})
    res = await send_command_to_server(host=host, port=port, message=message)
    answer = Message(**json.loads(res))
    return answer


async def command_add_ticket(
        tick: Ticket,
        host: str = '127.0.0.1',
        port: int = 8888
):
    message = Message(header="ADD_TICKET", body=tick.tdict)
    res = await send_command_to_server(host=host, port=port, message=message)
    answer = Message(**json.loads(res))
    return answer


async def command_delete_ticket(
        ticket_id: int,
        host: str = '127.0.0.1',
        port: int = 8888
):
    message = Message(header="DELETE_TICKET", body={"id": ticket_id})
    res = await send_command_to_server(host=host, port=port, message=message)
    answer = Message(**json.loads(res))
    return answer


async def command_request_ticket(
        worker_id : int,
        host: str = '127.0.0.1',
        port: int = 8888
):
    message = Message(header="REQUEST_TICKETS", body={"id": worker_id})
    res = await send_command_to_server(host=host, port=port, message=message)
    answer = Message(**json.loads(res))
    return answer


async def command_get_ticket_result(
        ticket_id : int,
        host: str = '127.0.0.1',
        port: int = 8888
):
    message = Message(header="GET_TICKET_RESULT", body={"id": ticket_id})
    res = await send_command_to_server(host=host, port=port, message=message)
    answer = Message(**json.loads(res))
    return answer


async def command_set_ticket_result(
        ticket_id: int,
        result: Any,
        host: str = '127.0.0.1',
        port: int = 8888
):
    message = Message(header="SET_TICKET_RESULT", body={"id": ticket_id, "result": result})
    res = await send_command_to_server(host=host, port=port, message=message)
    answer = Message(**json.loads(res))
    return answer


async def simple_test():
    com = Command(
        cunit= "system_unit",
        cfunc= "get_info",
        cargs= None,
        ctype="single"
    )
    tick = Ticket(
        tfrom=10,
        tto=155167253286217647024261323245457212920,
        tid=None,
        tcommand=com.cdict,
        tresult=None
    )
    message = Message(header="ADD_TICKET", body=tick.tdict)
    raw = json.dumps(message.mdict)

    with open("test.txt", 'w') as file_handler:
        file_handler.write(raw)
    print(raw)


async def main():
    # example uuid for worker =155167253286217647024261323245457212920
    com = Command(
        cunit= "system_unit",
        cfunc= "get_info",
        cargs= None,
        ctype="single"
    )
    ans = await command_get_server_info()
    print(ans.header)
    print(ans.body)
    while True:
        tick = Ticket(
            tfrom=10,
            tto=155167253286217647024261323245457212920,
            tid=None,
            tcommand=com.cdict,
            tresult=None
        )
        await asyncio.sleep(5)
        ans = await command_add_ticket(tick)
        print(ans.header)
        print(ans.body)
        res = await command_get_ticket_result(tick.id)
        print(res.header)
        print(res.body)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    # loop.run_until_complete(main())
    loop.run_until_complete(simple_test())
    # loop.run_forever()
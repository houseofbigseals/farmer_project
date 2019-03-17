import asyncio
import json
from command import Command, Ticket, Message
from typing import Any

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
        print('Accepted connection from {}'.format(self.address))

    def send_message(self, message):
        # transport.write(self.message.encode())
        message = message.encode()
        self.transport.write(message)
        print('Data sent: {!r}'.format(message))

    def data_received(self, data):
        asyncio.ensure_future(self.handle_incoming(data))

    async def handle_incoming(self, data):
        self.result = data
        # TODO: fix that ugly crutch
        self.placeholder[0] = data
        print('Data received: {!r}'.format(data.decode()))
        return self.result

    def connection_lost(self, exc):
        if exc:
            print('Client {} error: {}'.format(self.address, exc))
        print('The server closed the connection')
        self.on_con_lost.set_result(True)


async def send_command_to_server(
        message: Message = Message(),
        host: str = '127.0.0.1',
        port: int = 8888
        ):
    """
    wrapper-constructor for create commands and send them to server
    in format of Message object

    :param scommand: str = "ADD_TICKET"
    :param host: str = '127.0.0.1'
    :param port: str = "ADD_TICKET"
    :param data: Any
    :return: result : Any
    """

    loop = asyncio.get_running_loop()
    on_con_lost = loop.create_future()
    message_str = json.dumps(message.mdict)
    result = [None]
    transport, protocol = await loop.create_connection(
        lambda: ClientProtocol(on_con_lost, result),
        host, port)


    # Wait until the protocol signals that the connection
    # is lost and close the transport.
    try:
        protocol.send_message(message_str)
        # await asyncio.sleep(5)
        # protocol.send_message("OIOIOIO")
        # print("we really got {} from server".format(result))
        await on_con_lost
    finally:
        transport.close()
        return result[0]


async def main_test_GET_SERVER_INFO():
    # com = Command()
    # tick = Ticket(tfrom=1, tto=2, tcommand=com)
    res = await send_command_to_server()
    # print("we really got {} from server".format(res))
    answer = Message(**json.loads(res))
    print(answer.header)
    print(answer.body)


async def main_test_ADD_TICKET(tick):
    message = Message(header="ADD_TICKET", body=tick.tdict)
    res = await send_command_to_server(message=message)
    # print("we really got {} from server".format(res))
    answer = Message(**json.loads(res))
    print(answer.header)
    print(answer.body)


async def main_test_DELETE_TICKET(tick):
    message = Message(header="DELETE_TICKET", body={"id": tick.tdict["tid"]})
    res = await send_command_to_server(message=message)
    # print("we really got {} from server".format(res))
    answer = Message(**json.loads(res))
    print(answer.header)
    print(answer.body)


async def main_test_REQUEST_TICKETS(worker_id):
    message = Message(header="REQUEST_TICKETS", body={"id": worker_id})
    res = await send_command_to_server(message=message)
    # print("we really got {} from server".format(res))
    answer = Message(**json.loads(res))
    dicts_list = json.loads(answer.body)
    print(answer.header)
    # print(type(json.loads(answer.body)))
    # print(type(answer.body[0]))
    tickets_list = [Ticket(**t_dict) for t_dict in dicts_list]
    for t in tickets_list:
        print(t.id, t.to, t.tfrom)


async def main_test_GET_TICKET_RESULT(ticket_id):
    message = Message(header="GET_TICKET_RESULT", body={"id": ticket_id})
    res = await send_command_to_server(message=message)
    answer = Message(**json.loads(res))
    print(answer.header)
    print(answer.body)


async def main_test_SET_TICKET_RESULT(ticket_id, result):
    message = Message(header="SET_TICKET_RESULT", body={"id": ticket_id, "result": result})
    res = await send_command_to_server(message=message)
    answer = Message(**json.loads(res))
    print(answer.header)
    print(answer.body)

if __name__ == "__main__":
    com = Command()
    tick = Ticket(tfrom=100, tto=2, tcommand=com.cdict)
    tick2 = Ticket(tfrom=109, tto=3, tcommand=com.cdict)
    asyncio.run(main_test_ADD_TICKET(tick))
    asyncio.run(main_test_GET_SERVER_INFO())
    asyncio.run(main_test_ADD_TICKET(tick2))
    asyncio.run(main_test_GET_SERVER_INFO())
    # asyncio.run(main_test_REQUEST_TICKETS(3))
    asyncio.run(main_test_GET_TICKET_RESULT(tick.id))
    asyncio.run(main_test_GET_TICKET_RESULT(tick2.id))
    asyncio.run(main_test_SET_TICKET_RESULT(tick.id, 1234567890))
    asyncio.run(main_test_SET_TICKET_RESULT(1234567890, {"a":123456, "b":456789, "c":567890, "d":"asdfghjk"}))
    asyncio.run(main_test_GET_TICKET_RESULT(tick.id))
    asyncio.run(main_test_GET_TICKET_RESULT(tick2.id))
    # asyncio.run(main_test_DELETE_TICKET(tick))
    # asyncio.run(main_test_GET_SERVER_INFO())
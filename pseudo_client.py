import asyncio
import json
from command import Command, Ticket


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
        self.placeholder[0] = data
        print('Data received: {!r}'.format(data.decode()))
        return self.result

    def connection_lost(self, exc):
        if exc:
            print('Client {} error: {}'.format(self.address, exc))
        print('The server closed the connection')
        self.on_con_lost.set_result(True)


async def send_command_to_server(
        tick: Ticket,
        host: str = '127.0.0.1',
        port: int = 8888,
        scommand: str = "ADD_TICKET"
        ):
    loop = asyncio.get_running_loop()
    on_con_lost = loop.create_future()
    data = json.dumps({
        "COMMAND": scommand,
        "DATA": tick.tdict
    })
    result = [None]
    transport, protocol = await loop.create_connection(
        lambda: ClientProtocol(on_con_lost, result),
        host, port)


    # Wait until the protocol signals that the connection
    # is lost and close the transport.
    try:
        protocol.send_message(data)
        # await asyncio.sleep(5)
        # protocol.send_message("OIOIOIO")
        # print("we really got {} from server".format(result))
        await on_con_lost
    finally:
        transport.close()
        return result


async def main():
    com = Command()
    tick = Ticket(tfrom=1, tto=2, tcommand=com)
    res = await send_command_to_server(tick)
    print("we really got {} from server".format(res))


if __name__ == "__main__":
    asyncio.run(main())


# This a simple server that just answer one command to every
# RPi_master request. Also it must keep list of user commands
# when user sends command to do in RPi, server puts it to list
# and when server get RPi_master request, it send it to him.
# All requests must be written to ./server_log.txt
# The format must be
# request : time : who : addr : port : decoded message
# response : time : who : addr : port : decoded message


import asyncio
import json
from command import Command, Ticket, Message


class ServerProtocol(asyncio.Protocol):

    def __init__(self, server: Server):
        self.serv = server

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport

    def data_received(self, data):
        message = data.decode()
        self.server.handle_message(message)
        print('Close the client socket\n')
        self.transport.close()


class Server:
    """
    Server prototype
    Simple wrapper for asyncio.create_server
    with parsing messages

    Server answers
    head: STATUS
    body:
    INVALID_HEADER_ERROR
    INVALID_BODY_ERROR
    OK
    """
    def __init__(self, host: str = '127.0.0.1', port: int = 8888):
        # self.workers = [] # just list with ids
        # self.clients = [] # just list with ids
        self.tickets = []
        self.host = host
        self.port = port
        self.is_started = False
        self.server = None
        # self.protocol = ServerProtocol
        pass

    async def start(self):
        if not self.is_started:
            print("Server started")
            self.is_started = True
            loop = asyncio.get_event_loop()
            coro = loop.create_server(
                lambda: ServerProtocol(self.commands_list),
                self.addr,
                self.port
                )
            self.server = await coro

    async def stop(self):
        print("Server stopped")
        self.server.close()

    async def serve_forever(self):
        loop = asyncio.get_running_loop()
        print("Server started")
        self.is_started = True

        server = await loop.create_server(
            lambda: ServerProtocol(self),
            self.host,
            self.port)

        async with server:
            await server.serve_forever()

    # def create_commands_pack(self, worker_id):
    #     out = list()
    #     out.append(c for c in self.commands if c.id == worker_id)

    def parse_message(self, message):
        data_dict = json.loads(message)

    def handle_message(self, message : Message):
        """
        Must parse incoming message and return answer message to answer
        :param message: Message
        :return: Message
        """
        data_dict = json.loads(message)
        header = message.header
        # parse header
        valid_heads = [
            "ADD_TICKET",
            "DELETE_TICKET",
            "GET_TICKET_RESULT",
            "SET_TICKET_RESULT",
            "REQUEST_TICKETS",
            "GET_SERVER_INFO"
            ]
        if header not in valid_heads:
            return Message(header="STATUS", body="INVALID_HEADER_ERROR")
        else:
            body = message.body
            if header == "ADD_TICKET":
                # there must be a Ticket in body
                try:
                    #new_tick = body.
                    # TODO: how to create Ticket obj from raw dictionary
                    self.add_ticket()
                    return Message(header="STATUS", body="OK")
                except Exception as e:
                    return Message(header="STATUS", body="INVALID_BODY_ERROR:"+str(e))

            if header == "DELETE_TICKET":
                try:
                    self.delete_ticket(body)
                    return Message(header="STATUS", body="OK")
                except Exception as e:
                    return Message(header="STATUS", body="INVALID_BODY_ERROR:" + str(e))

            if header == "GET_TICKET_RESULT":
                try:
                    self.get_ticket_result(body)
                    return Message(header="STATUS", body="OK")
                except Exception as e:
                    return Message(header="STATUS", body="INVALID_BODY_ERROR:" + str(e))

            if header == "SET_TICKET_RESULT":
                try:
                    self.set_ticket_result(body)
                    return Message(header="STATUS", body="OK")
                except Exception as e:
                    return Message(header="STATUS", body="INVALID_BODY_ERROR:" + str(e))






async def main():
    # start server for 1 minut
    server = Server()
    loop = asyncio.get_event_loop()
    loop.run_forever()
    await server.start()
    await asyncio.sleep(160)
    await server.stop()


if __name__ == '__main__':
    asyncio.run(main())

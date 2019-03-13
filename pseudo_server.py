# This a simple server that just answer one command to every
# RPi_master request. Also it must keep list of user commands
# when user sends command to do in RPi, server puts it to list
# and when server get RPi_master request, it send it to him.
# All requests must be written to ./stupid_server_log.txt
# The format must be
# request : time : who : addr : port : decoded message
# response : time : who : addr : port : decoded message


import asyncio
import json

empty_message_dict = {
    "type": "client",
    "command":
        {
            "unit": "LED",
            "task": "set_current",
            "params": {"red": 100, "white": 100},
            "priority": 3,
            "secret_value": 1

        }
}


"""

messages formats:

1. from client to server:
message_dict = {
    "type": "client",
    "id" : client_id
    "address" : worker_id
    "command":
        {
            "unit": "LED",
            "task": "set_current",
            "params": {"red": 100, "white": 100},
            "priority": 3,
            "mode": "long"  

        }
}


2. from server to client

message_dict = {
    "status_of_execution_or_error": "no_such_worker_error"
}

3. from 

"""

error_message_dict = {

}


class ServerProtocol(asyncio.Protocol):

    def __init__(self, commands_list):
        self.commands = commands_list

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport

    def data_received(self, data):
        message = data.decode()
        data_dict = json.loads(message)
        print('Data received: {!r}'.format(message))
        print('Commands in stack: {}'.format(len(self.commands)))

        if data_dict["type"] == "worker":
            if len(self.commands) != 0:
                out_data = json.dumps(self.commands.pop())
            else:
                out_data = json.dumps(empty_message_dict)
            print('Send: {!r}'.format(out_data))
            self.transport.write(out_data.encode())
        else:
            out_data = json.dumps({"status": "we got that"})
            self.commands.append(data_dict)
            print('Send: {!r}'.format(out_data))
            self.transport.write(out_data.encode())

        print('Close the client socket\n')
        self.transport.close()


# class WorkersList:
#     def __init__(self, id_):
#         self.id = id_
#
# class ClientsList:
#     def __init__(self, id_):
#         self.id = id_
#     def add(self, id_):


class Server:
    """
    Server prototype
    Simple wrapper for asyncio.create_server
    """
    def __init__(self, addr: str = '127.0.0.1', port: int = 8888):
        self.workers = [] # just list with ids
        self.clients = [] # just list with ids
        self.commands_list = []
        self.addr = addr
        self.port = port
        self.is_started = False
        self.server = None
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

    def create_commands_pack(self, worker_id):
        out = list()
        out.append(c for c in self.commands if c.id == worker_id)

    def parse_message(self, message):
        data_dict = json.loads(message)
        if data_dict["type"] == "worker":
            new_id = data_dict["id"]
            # TODO: check id for type

            # add worker to list
            if new_id not in self.workers:
                self.workers.append(new_id)
            # find commands for this worker
            if len(self.commands) != 0:
                return json.dumps(self.commands.pop())
            else:
                return json.dumps(empty_message_dict)

        elif data_dict["type"] == "client":
            pass
        else:
            return


async def main():
    # start server for 1 minut
    server = Server()
    await server.start()
    await asyncio.sleep(60)
    await server.stop()


if __name__ == '__main__':
    asyncio.run(main())

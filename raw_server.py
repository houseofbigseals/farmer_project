# This a simple server that just answer one command to every
# worker request. Also it must keep list of user commands
# when user sends command to do in RPi, server puts it to list
# and when server get worker request, it send it to him.


import asyncio
import json
from command import Command, Ticket, Message
from typing import Any
import logging

logger = logging.getLogger("Server.RawServer")


class ServerProtocol(asyncio.Protocol):

    def __init__(self, server: Any):
        # TODO: how to fix that Any type hint and change to Server object?
        self.server = server

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        logger.debug('Connection from {}'.format(peername))
        self.transport = transport

    def data_received(self, data):
        message = data.decode()
        answer = json.dumps((self.server.handle_message(message)).mdict)
        logger.debug('Send: {!r}'.format(answer))
        self.transport.write(answer.encode())
        logger.debug('Close the client socket\n')
        self.transport.close()


class Server(object):
    """
    Server prototype
    Simple wrapper for asyncio.create_server
    with parsing messages

    Server answers
    head:
    SUCCESS
    ERROR
    body:
    INVALID_HEADER_ERROR
    INVALID_BODY_ERROR:error_str
    UNKNOWN_ERROR:error_str
    OK
    {server info dict}
    """
    def __init__(self, host: str = '127.0.0.1', port: int = 8888):
        # self.workers = [] # just list with ids
        # self.clients = [] # just list with ids
        self.tickets = []
        self.host = host
        self.port = port
        self.is_started = False
        self.aioserver = None
        # self.protocol = ServerProtocol
        pass

    async def start(self):
        if not self.is_started:
            logger.debug("Server started")
            self.is_started = True
            loop = asyncio.get_event_loop()
            coro = loop.create_server(
                lambda: ServerProtocol(self.commands_list),
                self.addr,
                self.port
                )
            self.aioserver = await coro

    async def stop(self):
        logger.debug("Server stopped")
        self.aioserver.close()

    async def serve_forever(self):
        loop = asyncio.get_event_loop()
        logger.debug("Server started")
        self.is_started = True

        self.aioserver = await loop.create_server(
            lambda: ServerProtocol(self),
            self.host,
            self.port)

        # async with self.aioserver:
        # await self.aioserver.

    def handle_message(self, message_: Any):
        """
        Must parse incoming message and return answer message to send response
        :param message_: Any (raw message dict)
        :return: Message
        """
        data_dict = json.loads(message_)
        message = Message(**data_dict)
        # print(data_dict)
        # print(type(data_dict))
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
            return Message(header="ERROR", body="INVALID_HEADER_ERROR")
        else:
            body = message.body
            if header == "ADD_TICKET":
                # there must be a dict describes a ticket in body
                # like that:
                # body = {
                #   "tfrom": int,
                #   "tto": int,
                #   "tid": UUID = None,
                #   "tcommand": dict = None,  # it must be a dict, that describes command
                #   "tresult": Any = None
                #   }
                try:
                    new_tick = Ticket(**body)
                    self.add_ticket(new_tick)
                    return Message(header="SUCCESS", body="OK")
                except Exception as e:
                    return Message(header="ERROR", body="INVALID_BODY_ERROR:" + str(e))

            elif header == "DELETE_TICKET":
                # there must be a dict in body
                # body = {
                #           "id": int
                #       }
                try:
                    self.delete_ticket(body["id"])
                    return Message(header="SUCCESS", body="OK")
                except Exception as e:
                    return Message(header="ERROR", body="INVALID_BODY_ERROR:" + str(e))

            elif header == "GET_TICKET_RESULT":
                # there must be a dict in body
                # body = {
                #           "id": int
                #       }
                try:
                    ans_body = self.get_ticket_result(body["id"])
                    return Message(header="SUCCESS", body=ans_body)
                except Exception as e:
                    return Message(header="ERROR", body="INVALID_BODY_ERROR:" + str(e))

            elif header == "SET_TICKET_RESULT":
                # there must be a dict in body
                # body = {
                #           "id": int,
                #           "result": Any
                #       }
                try:
                    self.set_ticket_result(body["id"], body["result"])
                    return Message(header="SUCCESS", body="OK")
                except Exception as e:
                    return Message(header="ERROR", body="INVALID_BODY_ERROR:" + str(e))

            elif header == "REQUEST_TICKETS":
                # there must be a dict in body
                # body = {
                #           "id": int,
                #       }
                try:
                    worker_id = body["id"]
                    tickets_list = self.find_tickets_for_worker(worker_id)
                    return Message(header="SUCCESS", body=json.dumps(tickets_list))
                except Exception as e:
                    return Message(header="ERROR", body="INVALID_BODY_ERROR:" + str(e))

            elif header == "GET_SERVER_INFO":
                # there must be nothing in body
                # body = {}
                try:
                    ans_body = self.server_info()
                    return Message(header="SUCCESS", body=ans_body)
                except Exception as e:
                    return Message(header="ERROR", body="UNKNOWN_ERROR:" + str(e))

            else:
                return Message(header="ERROR", body="UNKNOWN_ERROR:" + "UNKNOWN")

    def server_info(self):
        # Send all interesting info from server as a str
        logger.debug("Send info")
        info = {
            "tickets_number": len(self.tickets),
            "tickets_ids": [t.id for t in self.tickets]
            }
        ans = json.dumps(info)
        return ans

    def add_ticket(self, tick: Ticket):
        # add ticket from message to our tickets_list
        logger.debug("Add ticket with id = {}".format(tick.id))
        self.tickets.append(tick)

    def delete_ticket(self, del_id: int):
        # remove ticket if it in tickets_list, else raise exception
        logger.debug("Trying to delete ticket with id = {}".format(del_id))
        deleted = False
        for t in self.tickets:
            if t.id == del_id:
                self.log_ticket(t)
                logger.debug("Delete ticket with id = {}".format(t.id))
                self.tickets.remove(t)
                deleted = True
        if not deleted:
            logger.debug("There is no ticket with id={}".format(del_id))
            raise ValueError("There is no ticket with id={}".format(del_id))

    def log_ticket(self, tick: Ticket):
        # add ticket to log
        logger.debug("Log ticket with id = {}".format(tick.id))
        # TODO: do real logging
        pass

    def get_ticket_result(self, tick_id: int):
        # return result from ticket
        logger.debug("Trying to get result of ticket with id = {}".format(tick_id))
        found = False
        for t in self.tickets:
            if t.id == tick_id:
                found = True
                logger.debug("Got result of ticket with id = {}".format(tick_id))
                return t.result
        if not found:
            logger.debug("There is no ticket with id={}".format(tick_id))
            raise ValueError("There is no ticket with id={}".format(tick_id))

    def set_ticket_result(self, tick_id: int, result: Any):
        # set result to ticket
        logger.debug("Trying to set result of ticket with id = {}".format(tick_id))
        found = False
        for t in self.tickets:
            if t.id == tick_id:
                found = True
                logger.debug("Set result of ticket with id = {}".format(tick_id))
                t.result = result
        if not found:
            logger.debug("There is no ticket with id={}".format(tick_id))
            raise ValueError("There is no ticket with id={}".format(tick_id))

    def find_tickets_for_worker(self, worker_id: int):
        # find tickets, add them to list and then return that list
        logger.debug("Trying to find tickets for worker with id = {}".format(worker_id))
        # TODO: check if ticket was already sent !!!
        # dirty move for now:
        # if ticket at work - put "at_work" string to result and check it
        tickets_list = []
        for t in self.tickets:
            if t.to == worker_id and not t.result:
                t.result = "at_work"
                tickets_list.append(t.tdict)
        return tickets_list


async def server_main():
    # start server for 1 minute
    server = Server()

    await server.serve_forever()
    # loop.run_forever()
    # await server.start()
    # await asyncio.sleep(160)
    # await server.stop()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(server_main())
    loop.run_forever()
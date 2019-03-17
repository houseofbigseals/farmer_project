# There are command protocol

from uuid import uuid4, UUID
from typing import Dict, Any
import json


class Message(object):
    """
    Message to server from worker or client
    Valid headers:
    to server:
    ADD_TICKET
    DELETE_TICKET
    GET_TICKET_RESULT
    SET_TICKET_RESULT
    REQUEST_TICKETS
    GET_SERVER_INFO
    from server:
    STATUS
    ERROR
    Valid bodies - any, server must handle and do validation, not we
    """
    def __init__(self,
                 header: str = "GET_SERVER_INFO",
                 body: Any = ""
                 ):
        self._header = header
        self._body = body
        self._dict = {
            "header": self._header,
            "body": self._body
        }
        self._string = json.dumps(self._dict)

    @property
    def header(self):
        return self._header

    @property
    def body(self):
        return self._body

    @property
    def string(self):
        return self._string

    @property
    def mdict(self):
        return self._dict


class Command(object):
    """
    Command to worker
    """
    def __init__(self,
                 cunit: str = "system",
                 cfunc: str = "get_info",
                 cargs: Dict = None,
                 ctype: str = "single"
                 ):
        self._unit = cunit
        self._func = cfunc
        self._args = cargs if cargs is not None else {}
        self._ctype = ctype
        self._dict = {
            "cunit": self._unit,
            "cfunc": self._func,
            "cargs": self._args,
            "ctype": self._ctype
        }
        self._string = json.dumps(self._dict)

    @property
    def unit(self):
        return self._unit

    @property
    def func(self):
        return self._func

    @property
    def args(self):
        return self._args

    @property
    def ctype(self):
        return self._ctype

    @property
    def string(self):
        return self._string

    @property
    def cdict(self):
        return self._dict


class Ticket(object):
    """
    Wrapper for command, to send to server
    """
    def __init__(self,
                 tfrom: int,
                 tto: int,
                 tid: int = None,
                 tcommand: dict = None,  # it must be a dict, that describes command such as Command.cdict
                 tresult: Any = None
                 ):
        self._from = tfrom
        self._to = tto
        self._id = tid if tid is not None else uuid4().int  # it must be a big integer
        self._command = tcommand
        self._result = tresult
        self._dict = {
            "tfrom": self._from,
            "tto": self._to,
            "tid": self._id,
            "tcommand": self._command,
            "tresult": self._result
        }
        self._string = json.dumps(self._dict)

    @property
    def tfrom(self):
        return self._from

    @property
    def to(self):
        return self._to

    @property
    def id(self):
        return self._id

    @property
    def command(self):
        return self._command

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, res: Any = None):
        # TODO: res might be unserializable so we need to check it
        self._result = res
        self._dict["result"] = self._result
        self._string = json.dumps(self._dict)

    @property
    def tdict(self):
        return self._dict

    @property
    def string(self):
        return self._string


if __name__ == "__main__":
    command_kwargs = {
        "cunit": "test_unit",
        "cfunc": "test_func",
        "cargs": {"a": 1, "b": 2,"c": 3},
        "ctype": "test_type"
    }
    c = Command(**command_kwargs)
    cd = c.cdict
    ccc = Command(**cd)
    print(ccc.unit)
    print(ccc.cdict)
    ticket_kwargs = {
        "tfrom": 1000,
        "tto": 100,
        "tid": str(uuid4()),
        "tcommand": command_kwargs,
        "tresult": {"error": "BAD_ERROR"}
    }
    t = Ticket(**ticket_kwargs)
    tt = Ticket(**t.tdict)
    print(tt.command)
    print(tt.result)
    print(tt.id)
    # T = Ticket(tfrom=1, tto=2, tcommand=c)
    # print(T.result)
    # T.result = 56
    # print(T.result)
    # print(c.string)
    # print(T.string)

# There are command protocol

from uuid import uuid4, UUID
from typing import Dict, Any
import json


class Command(object):
    """
    Command to worker
    """
    def __init__(self,
                 unit: str = "system",
                 func: str = "get_info",
                 args: Dict = None,
                 ctype: str = "single"
                 ):
        self._unit = unit
        self._func = func
        self._args = args if args is not None else {}
        self._ctype = ctype
        self._dict = {
            "unit": self._unit,
            "func": self._func,
            "args": self._args,
            "type": self._ctype
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
                 tid: UUID = None,
                 tcommand: Command = None,
                 tresult: Any = None
                 ):
        self._from = tfrom
        self._to = tto
        self._id = tid if tid is not None else uuid4()
        self._command = tcommand
        self._result = tresult
        self._dict = {
            "from": self._from,
            "to": self._to,
            "id": str(self._id),
            "command": self._command.cdict,
            "result": self._result
        }
        self._string = json.dumps(self._dict)

    @property
    def from_(self):
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
    c = Command()
    print(c.unit)
    T = Ticket(tfrom=1, tto=2, tcommand=c)
    print(T.result)
    T.result = 56
    print(T.result)
    print(c.string)
    print(T.string)

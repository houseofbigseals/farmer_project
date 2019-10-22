"""
This module contain base class BasePattern
"""
import asyncio


class BasePattern:
    """
    BasePattern is object, that must contain and handle
    all things related to user-defined behavior of system
    All user-created behavioral patterns must be inherited from this object and put in ../tools/patterns
    """
    pass

    def __init__(self):
        self.units = list()
        self.exposed_methods = list()
        pass

    async def start(self):
        pass

    async def stop(self):
        pass

    async def pause(self):
        pass

    async def rpc_handle(self):
        pass
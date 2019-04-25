
from aiohttp import web
import json


class TServer(object):
    """

    """
    def __init__(
            self,
            host = ""
    ):
        self.app = web.Application()
        self.app.add_routes([web.get('/', self.handler)])
        self.app.add_routes([web.put('/', self.handler)])
        web.run_app(
            self.app,
            host="127.0.0.1",
            port="8888"
        )

    async def handler(self, request):
        peername = request.transport.get_extra_info('peername')
        if peername is not None:
            host, port = peername
        body = await request.text()
        print(host, port)
        print(body)
        return web.Response(text="heh")


if __name__ == "__main__":
    ts = TServer()
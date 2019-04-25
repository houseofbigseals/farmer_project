import aiohttp
import asyncio

class TClient(object):
    """

    """
    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def get(self, addr):
        async with self.session.get(addr) as resp:
            print(resp.status)
            print(await resp.text())

    async def put(self, addr):
        async with self.session.put(addr, data="AAAAAAAAAAAAAAAA") as resp:
            print(resp.status)
            print(await resp.text())

    async def close(self):
        await self.session.close()


async def loop_main():
    tc = TClient()
    while True:
        await tc.get("http://127.0.0.1:8888")
        await tc.get("http://127.0.0.1:8888/")
        await tc.put("http://127.0.0.1:8888/")
    await tc.close()

async def main():
    tc = TClient()
    await tc.get("http://127.0.0.1:8888")
    await tc.get("http://127.0.0.1:8888/")
    await tc.put("http://127.0.0.1:8888/")
    await tc.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    # loop.run_forever()
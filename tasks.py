# module with tasks - single and

import asyncio
from contextlib import suppress
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


class PeriodicTask:
    def __init__(self, func, time):
        self.func = func
        self.time = time
        self.is_started = False
        self._task = None

    async def start(self):
        if not self.is_started:
            self.is_started = True
            # Start task to call func periodically:
            self._task = asyncio.ensure_future(self._run())

    async def stop(self):
        if self.is_started:
            self.is_started = False
            # Stop task and await it stopped:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

    async def _run(self):
        while True:
            await asyncio.sleep(self.time)
            self.func()


class LongSingleTask:
    def __init__(self, func, executor, loop):
        self.executor = executor
        self.func = func
        self.is_started = False
        self.done = False
        self._task = None
        self.loop = loop

    async def start(self):
        if not self.is_started:
            self.is_started = True
            # Start task to call func periodically:
            await self.loop.run_in_executor(self.executor, self.func)
            self.done = True
            # self._task = asyncio.ensure_future(self._run())

    async def stop(self):
        if self.is_started:
            self.is_started = False
            if self.done:
                return
            else:
                # Stop task and await it stopped:
                self._task.cancel()
                with suppress(asyncio.CancelledError):
                    await self._task

    # async def _run(self):
    #         await asyncio.sleep(0)
    #         self.func()


class SingleTask:
    def __init__(self, func, loop):
        self.func = func
        self.is_started = False
        self.done = False
        self._task = None
        self.loop = loop

    async def start(self):
        if not self.is_started:
            self.is_started = True
            # Start task to call func one time:
            # await self.loop.run_in_executor(self.executor, self.func)
            # self.done = True
            self._task = asyncio.ensure_future(self._run())

    async def stop(self):
        if self.is_started:
            self.is_started = False
            if self.done:
                return
            else:
                # Stop task and await it stopped:
                self._task.cancel()
                with suppress(asyncio.CancelledError):
                    await self._task

    async def _run(self):
            await asyncio.sleep(0)
            self.func()


def long_problem(n = 0, t = 20):
    print("long_problem_{}_started".format(n))
    time.sleep(t)
    print("long_problem_{}_finished".format(n))


async def main():
    loop_ = asyncio.get_event_loop()
    executor = ThreadPoolExecutor()
    p = PeriodicTask(lambda: print('p1 at work!'), 1)
    p2 = PeriodicTask(lambda: print('p2 at work!'), 1)
    # p3 = PeriodicAdderTask(lambda: long_problem(39, t = 5), 5)
    # p3 = Periodic(lambda: long_problem(), 1)
    s1 = LongSingleTask(long_problem, executor, loop_)
    # try:
    #     print('Start p1 and p2 p3')
    #     await p.start()
    #     await p2.start()
    #     _task = asyncio.ensure_future(s1.start())
    #     await asyncio.sleep(3.1)
    #
    #     print('Stop p1')
    #     await p.stop()
    #     await asyncio.sleep(3.1)
    #
    #     print('Start p1')
    #     await p.start()
    #     await asyncio.sleep(3.1)
    # finally:
    #     print('Stop p1 and p2')
    #     await p.stop()  # we should stop task finally
    #     await p2.stop()
    #     await _task
    #     await s1.stop()
    # print('Start p1 and p2 p3')
    print(len(asyncio.Task.all_tasks()))
    # await p3.start()
    await asyncio.sleep(0)
    await p.start()
    print(len(asyncio.Task.all_tasks()))
    await p2.start()
    print(len(asyncio.Task.all_tasks()))
    _task = asyncio.ensure_future(s1.start())
    await asyncio.sleep(3.1)
    print(len(asyncio.Task.all_tasks()))
    # print('Stop p1')
    # await p.stop()
    await asyncio.sleep(3.1)
    print(len(asyncio.Task.all_tasks()))
    # print('Start p1')
    # await p.start()
    await asyncio.sleep(3.1)
    await _task


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()
    # asyncio.run(main())

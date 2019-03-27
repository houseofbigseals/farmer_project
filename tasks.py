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


class PeriodicCoro:
    def __init__(self, coro, time, *args, **kwargs):
        self.coro_args = args
        self.coro_kwargs = kwargs
        self.coro = coro
        self.time = time
        self.is_started = False
        self._task = None

    async def _repeat_forever(self):
        while True:
            await asyncio.sleep(self.time)
            print("_repeat_forever at work !")
            await self.coro(*self.coro_args, **self.coro_kwargs)

    async def start(self):
        if not self.is_started:
            loop_ = asyncio.get_event_loop()
            self.is_started = True
            # Start task to call coro periodically:
            self._task = asyncio.ensure_future(self._repeat_forever())
            # loop_.run_until_complete(self._task)

    async def stop(self):
        if self.is_started:
            self.is_started = False
            # Stop task and await it stopped:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task


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
            # Start task to call func once
            self._task = self.loop.run_in_executor(self.executor, self.func)
            self.done = True
            await self.stop()

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
    #
    # async def _run(self):
    #         self.func()


class SingleTask:
    def __init__(self, func):
        self.func = func
        self.is_started = False
        self.done = False
        self._task = None
        _loop = asyncio.get_event_loop()
        self.loop = _loop

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
            self.done = True
            await self.stop()


def long_problem(n=0, t=20):
    print("long_problem_{}_started".format(n))
    time.sleep(t)
    print("long_problem_{}_finished".format(n))


async def long_coro(n=0, t=5):
    long_problem(n, t)


async def main():
    loop_ = asyncio.get_event_loop()
    executor = ThreadPoolExecutor()
    print(asyncio.Task.all_tasks(loop_))
    pp = PeriodicCoro(long_coro, 5, 1, 10)
    pp2 = PeriodicTask(lambda: print("periodic task 1 !"), 1)
    await pp2.start()
    await pp.start()
    print(asyncio.Task.all_tasks(loop_))
    await asyncio.sleep(20)
    print(asyncio.Task.all_tasks(loop_))

# async def main():
#     loop_ = asyncio.get_event_loop()
#     while True:
#         asyncio.sleep(1)
#         await long_coro()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()
    # asyncio.run(main())

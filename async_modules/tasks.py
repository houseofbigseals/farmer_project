# module with tasks - single and

import asyncio
from contextlib import suppress
import time
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

logger = logging.getLogger("Worker.async_tasks")

# TODO rewrite all things here and add exception control, logging and catching
#  especially _run in ever task !


class PeriodicTask:
    def __init__(self, func, time, name=None):
        self.func = func
        self.time = time
        self.is_started = False
        self._task = None
        self._name = name if name is not None else str(self.func)

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
            logger.debug("{} at work !".format(self._name))
            self.func()


class PeriodicCoro:
    def __init__(self, coro, time, name=None, *args, **kwargs):
        self.coro_args = args
        self.coro_kwargs = kwargs
        self.coro = coro
        self.time = time
        self.is_started = False
        self._task = None
        self._name = name if name is not None else str(self.coro)

    async def _repeat_forever(self):
        while True:
            await asyncio.sleep(self.time)
            try:
                await self.coro(*self.coro_args, **self.coro_kwargs)
                logger.debug("{} done correctly".format(self._name))
            except Exception as e:
                logger.error("Error in {} : {} ".format(self._name, e))
                logger.error("Periodic Coro {} will be stopped ".format(self._name))
                await self.stop()

    async def start(self):
        if not self.is_started:
            loop_ = asyncio.get_event_loop()
            self.is_started = True
            # Start task to call coro periodically:
            self._task = asyncio.ensure_future(self._repeat_forever())
            # loop_.run_until_complete(self._task)
            logger.info("Periodic Coro {} started ".format(self._name))

    async def stop(self):
        if self.is_started:
            self.is_started = False
            # Stop task and await it stopped:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            logger.info("Periodic Coro {} stopped ".format(self._name))


class LongSingleTask:
    def __init__(self, func, executor, name=None, *args, **kwargs):
        self.coro_args = args
        self.coro_kwargs = kwargs
        self.executor = executor
        self.func = func
        self.is_started = False
        self.done = False
        self._task = None
        self.loop = asyncio.get_event_loop()
        self._name = name if name is not None else str(self.func)

    async def start(self):
        if not self.is_started:
            self.is_started = True
            # Start task to call func once
            self._task = self.loop.run_in_executor(self.executor, self.func)
            logger.debug("{} at work !".format(self._name))
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
    def __init__(self, func, name=None, *args, **kwargs):
        self.coro_args = args
        self.coro_kwargs = kwargs
        self.func = func
        self.is_started = False
        self.done = False
        self._task = None
        _loop = asyncio.get_event_loop()
        self.loop = _loop
        self._name = name if name is not None else str(self.func)

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
            logger.debug("{} at work !".format(self._name))
            self.func()
            self.done = True
            # await self.stop()


class SingleCoro:
    def __init__(self, coro, name=None, *args, **kwargs):
        self.coro_args = args
        self.coro_kwargs = kwargs
        self.coro = coro
        self.is_started = False
        self.done = False
        self._task = None
        _loop = asyncio.get_event_loop()
        self.loop = _loop
        self._name = name if name is not None else str(self.coro)

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
        try:
            await self.coro(*self.coro_args, **self.coro_kwargs)
            self.done = True
            logger.debug("{} done correctly".format(self._name))
        except Exception as e:
            logger.error("Error in {} : {} ".format(self._name, e))
            logger.error("Single coro {} will be stopped ".format(self._name))
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
    # pp = PeriodicCoro(long_coro, 5, 1, 10)
    pp2 = PeriodicTask(lambda: print("periodic task 1 !"), 1)
    await pp2.start()
    # await pp.start()
    # print(asyncio.Task.all_tasks(loop_))
    # await asyncio.sleep(20)
    # print(asyncio.Task.all_tasks(loop_))
    sing = SingleTask(lambda: print("single task 1 !"))
    await sing.start()
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

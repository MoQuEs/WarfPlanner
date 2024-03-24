from atexit import register
from typing import Callable, Any, Optional
from queue import Empty
from threading import Timer
from multiprocessing import Process, Queue, Value
from time import sleep
from uuid import uuid4, UUID

from .Logger import error

TaskCallable = Callable[[UUID, ...], Any]
TaskCallableArgs = tuple[Any, ...] | None
TaskCallableKwargs = dict[str, Any] | None

TaskCallback = Callable[[UUID, Any], None] | None
TaskErrorCallback = Callable[[UUID, Exception], None] | None

AddTask = (TaskCallable, TaskCallback, TaskCallableArgs, TaskCallableKwargs)
Task = (UUID, TaskCallable, TaskCallback, TaskCallableArgs, TaskCallableKwargs)

_pools: dict[str, "Pool"] = {}


def get_pool(
    name: str, pool_size: int = 5, max_in_queue: int = 0, use_return_queue: bool = False, use_error_queue: bool = False
) -> "Pool":
    global _pools

    if name in _pools:
        return _pools[name]

    _pools[name] = Pool(pool_size, max_in_queue, use_return_queue, use_error_queue)
    register(_pools[name].join)

    return _pools[name]


def join_pool(name: str):
    global _pools

    _pools[name].join()


def del_pool(name: str):
    global _pools

    pool = _pools.pop(name)
    del pool


class Worker(Process):
    daemon: bool = True
    _TIMEOUT: float = 0.1

    def __init__(
        self, _task_done: Value, tasks: Queue, returns: Optional[Queue] = None, errors: Optional[Queue] = None
    ):
        Process.__init__(self)

        self._task_done: Value = _task_done
        self._exit: Value = Value("b", False)

        self._tasks: Queue = tasks
        self._returns: Optional[Queue] = returns
        self._errors: Optional[Queue] = errors

        self.start()

    def run(self):
        while True:
            with self._exit.get_lock():
                if self._exit.value:
                    return

            try:
                uid, func, callback, errorCallback, args, kwargs = self._tasks.get(block=True, timeout=self._TIMEOUT)

                try:
                    data = func(uid, *args, **kwargs)

                    if callback is not None:
                        callback(uid, data)

                    if self._returns is not None:
                        self._returns.put((uid, data))

                except Exception as e:
                    if errorCallback is not None:
                        errorCallback(uid, e)

                    if self._errors is not None:
                        self._errors.put((uid, e))

                    error(e)
                finally:
                    with self._task_done.get_lock():
                        self._task_done.value += 1
            except Empty:
                pass
            except ValueError:
                pass

    def set_exit(self):
        with self._exit.get_lock():
            self._exit.value = True


class Pool:
    def __init__(
        self,
        pool_size: int = 20,
        max_items_in_queue: int = 0,
        use_return_queue: bool = False,
        use_error_queue: bool = False,
    ):
        self._tasks: Queue = Queue(max_items_in_queue)

        self._returns: Optional[Queue] = Queue(max_items_in_queue) if use_return_queue else None
        self._errors: Optional[Queue] = Queue(max_items_in_queue) if use_error_queue else None

        self._pool_size: int = pool_size
        self._max_pool_reached: bool = False

        self._task_counter: int = 0
        self._task_done: Value = Value("i", 0)

        self._timer: Timer = Timer(5.0, self._remove_workers_if_no_tasks)
        register(self._timer.cancel)
        self._timer.start()

        self._workers: list = []

    def _init_worker(self):
        if self._max_pool_reached or self._tasks.empty():
            return

        if len(self._workers) >= self._pool_size:
            self._max_pool_reached = True
            return

        self._workers.append(Worker(self._task_done, self._tasks, self._returns, self._errors))

    def add_task(
        self, func: TaskCallable, callback: TaskCallback, errorCallback: TaskErrorCallback, *args, **kwargs
    ) -> UUID:
        uid = uuid4()
        self._add_task(uid, func, callback, errorCallback, args, kwargs)
        return uid

    def get_result(self, block: bool = False) -> tuple[UUID, Any]:
        if self._returns is None:
            raise ValueError(f"Queue return not enabled")

        return self._returns.get(block=block)

    def get_error(self, block: bool = False) -> tuple[UUID, Exception]:
        if self._errors is None:
            raise ValueError(f"Queue return not enabled")

        return self._errors.get(block=block)

    def _remove_workers_if_no_tasks(self):
        if self._tasks.empty():
            self._stop_workers(False)

    def _add_task(
        self,
        uid: UUID,
        task_callable: TaskCallable,
        callback: TaskCallback,
        errorCallback: TaskErrorCallback,
        args: TaskCallableArgs,
        kwargs: TaskCallableKwargs,
    ):
        self._task_counter += 1
        self._tasks.put((uid, task_callable, callback, errorCallback, args, kwargs))
        self._init_worker()

    def empty(self) -> bool:
        with self._task_done.get_lock():
            return self._task_counter - self._task_done.value <= 0

    def join(self):
        while True:
            if self.empty():
                return
            sleep(0.1)

    def __del__(self):
        self._stop_workers()

    def _stop_workers(self, close_all: bool = True):
        self._max_pool_reached = False

        for idx, worker in enumerate(self._workers):
            if not close_all and idx == 0:
                continue

            proc: Worker = self._workers.pop(idx)
            if proc.is_alive():
                proc.set_exit()

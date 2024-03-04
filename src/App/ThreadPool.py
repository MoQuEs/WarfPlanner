from typing import Callable
from queue import Queue, Empty
from threading import Thread, Event


class Worker(Thread):
    _TIMEOUT: int = 10
    tasks: Queue
    daemon: bool = True
    done: Event = Event()

    def __init__(self, tasks: Queue):
        Thread.__init__(self)
        self.tasks = tasks

        self.start()

    def run(self):
        while not self.done.is_set():
            try:
                func, args, kwargs = self.tasks.get(block=True, timeout=self._TIMEOUT)
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    print(e)
                finally:
                    self.tasks.task_done()
            except Empty:
                pass
        return

    def signal_exit(self):
        self.done.set()


class ThreadPool:
    tasks: Queue
    workers: list = []
    done: bool = False

    def __init__(self, num_threads: int, tasks: list | None = None):
        self.tasks = Queue(num_threads)

        self.__init_workers(num_threads)
        for task in tasks if tasks is not None else []:
            self.tasks.put(task)

    def __init_workers(self, num_threads):
        for thread_index in range(num_threads):
            self.workers.append(Worker(self.tasks))

    def add_task(self, func: Callable, *args, **kwargs):
        self.tasks.put((func, args, kwargs))

    def __close_all_threads(self):
        for worker in self.workers:
            worker.signal_exit()

        self.join()

        self.workers = []

    def join(self):
        self.tasks.join()

    def __del__(self):
        self.__close_all_threads()

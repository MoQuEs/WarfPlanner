import threading
from queue import Queue, Empty
from threading import Thread


class Worker(Thread):
    _TIMEOUT = 10

    tasks: Queue
    daemon: bool = True
    done: threading.Event = threading.Event()

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

    def __init__(self, num_threads: int, tasks: list = None):
        self.tasks = Queue(num_threads)

        self._init_workers(num_threads)
        for task in (tasks if tasks is not None else []):
            self.tasks.put(task)

    def _init_workers(self, num_threads):
        for thread_index in range(num_threads):
            self.workers.append(Worker(self.tasks))

    def add_task(self, func: callable, *args, **kwargs):
        self.tasks.put((func, args, kwargs))

    def _close_all_threads(self):
        for worker in self.workers:
            worker.signal_exit()

        self.join()

        self.workers = []

    def join(self):
        self.tasks.join()

    def __del__(self):
        self._close_all_threads()

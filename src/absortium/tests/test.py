__author__ = 'andrew.shvv@gmail.com'

from core.utils.logging import getLogger

logger = getLogger(__name__)

_client = None


def get_crossbar_client():
    global _client
    if not _client:
        _client = Client()
    return _client


def set_crossbar_client(client):
    global _client
    _client = client


class Client():
    def publish(self, topic, pubsliment):
        logger.debug("Topic: {} Publishment: {}".format(topic, pubsliment))


class Atomic():
    """
        Replace real client with mock one and consume all publishments which was made during block execution. Then
        if exceptions was not raised publish them with real client.
    """

    def __init__(self, *args, **kwargs):
        self.topics = {}
        self.client = get_crossbar_client()

    def publish(self, topic, publishment):
        if not topic in self.topics:
            self.topics[topic] = []
        self.topics[topic].append(publishment)

    def __enter__(self):
        set_crossbar_client(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            for topic, publishments in self.topics.items():
                for publishment in publishments:
                    self.client.publish(topic, publishment)

        if exc_type is NotEnoughMoney:
            self.client.publish("error topic", exc_val.msg)

        set_crossbar_client(self.client)


class NotEnoughMoney(Exception):
    msg = "Not enough money bitch!"

    def __init__(self, data):
        self.data = data


from queue import Queue
from multiprocessing import Process, Lock


class ProcessQueue():
    threads = []

    def __init__(self, num_worker_process=10):
        self.num_worker_process = num_worker_process
        self.q = Queue()

    def _worker(self, lock, name):
        while True:
            data = self.q.get()
            if data is None:
                break

            func = data["func"]
            args = data["args"]
            kwargs = data["kwargs"]

            # time.sleep(random.random())
            func(*args, **kwargs)
            self.q.task_done()

        logger.debug("Close session")
        from django import db
        db.connection.close()

    def add(self, func, *args, **kwargs):
        data = {
            "func": func,
            "args": args,
            "kwargs": kwargs
        }

        self.q.put(data)

    def start(self):
        lock = Lock()

        for i in range(self.num_worker_process):
            kwargs = {
                "name": "process-{}".format(i)
            }
            args = (lock,)

            p = Process(target=self._worker, args=args, kwargs=kwargs)
            p.start()
            self.threads.append(p)

    def stop(self):
        # stop workers
        for i in range(self.num_worker_process):
            self.q.put(None)
        for t in self.threads:
            t.join()

    def join(self):
        # block until all tasks are done
        self.q.join()


# pq = ProcessQueue()
#
#
# def f(name):
#     logger.debug('hello', name)
#
# with Pool(processes=4) as pool:
#     logger.debug("start")
#     # res = pool.apply_async(f, args=("world",))
#     pool.apply_async(f, args=("world",))
#     # logger.debug(res)
import time
from multiprocessing import Pool

def f(a):
    raise Exception
    print('f(' + str(a) + ')')
    return True

t = time.time()
pool = Pool(processes=10)
result = pool.apply_async(f, (1,))
print(type(result.get()))
print(result.get())
pool.close()
# print(' [i] Time elapsed ' + str(time.time() - t))

import Queue
from threading import Thread
from yelib.util import singleton, coroutine

class Task(object):
    _id = 0

    def __init__(self, func, *args, **kwargs):
        Task._id += 1
        self.id = Task._id
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.taskq = None

    def register(self, taskq):
        self.taskq = taskq

    def unregister(self, taskq):
        try:
            self.taskq.get_nowait(self)
        except Queue.Empty:
            pass
        self.taskq = None

    def run(self):
        if self.taskq is not None:
            self.taskq.put(self)


class WorkThread(Thread):

    def __init__(self):
        Thread.__init__(self)
        self._continue = True
        self.start()

    def stop(self):
        self._continue = False

    def _run(self):
        pass
    def _cleanup(self):
        pass

    def run(self):
        while True:
            try:
                if not self._continue:
                    self._cleanup()
                    break
                self._run()
            except Exception as ex:
                print ex

class Worker(WorkThread):

    def __init__(self):
        self._todo_list = Queue.Queue()
        self.deliver = Deliver()
        WorkThread.__init__(self)

    def exit(self):
        self.deliver.stop()
        self.stop()

    def add(self, task):
        task.register(self._todo_list)

    def remove(self, task):
        task.unregister()

    def _cleanup(self):
        try:
            while True:
                t = self._todo_list.get_nowait()
                self.deliver.remove(t.id)
        except Queue.Empty:
            pass

    def _run(self):
        try:
            t = self._todo_list.get(timeout=0.1)
            for msg in t.func(*t.args, **t.kwargs):
                self.deliver.send(t.id, msg)
        except Queue.Empty:
            pass

@singleton
class Deliver(WorkThread):

    def __init__(self):
        self._mail_box = Queue.Queue()
        self._task_list = {}
        WorkThread.__init__(self)

    def send(self, tid, msg):
        self._mail_box.put( {'tid':tid, 'msg':msg} )

    def add(self, tid, target):
        self._task_list.setdefault(tid, set()).add(target)

    def remove(self, tid, target=None):
        try:
            if target is not None:
                self._task_list[tid].remove(target)
            else:
                targets = self._task_list.pop(tid)
                for t in targets:
                    t.close()
        except KeyError:
            pass

    def _run(self):
        try:
            m = self._mail_box.get(timeout=0.1)
            for target in self._task_list[m['tid']]:
                try:
                    target.send(m['msg'])
                except StopIteration:
                    pass
        except Queue.Empty:
            pass


class Subscriber(object):

    # TODO: What if too many subscribers, need to close hdlr elegantly

    def __init__(self, hdlr):
        self.hdlr = hdlr
        self.deliver = Deliver()

    def subscribe(self, task):
        self.deliver.add(task.id, self.hdlr)

    def unsubscribe(self, task):
        self.deliver.remove(task.id, self.hdlr)


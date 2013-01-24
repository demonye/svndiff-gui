#!/usr/bin/env python2
# -* coding: utf-8 -*-

import os
import time
import types
import Queue
from threading import Thread, Lock, ThreadError
from subprocess import *
from yelib.util import enum
from PySide.QtCore import QObject, Signal, Slot
import locale
from yelib.util import singleton

OutputType = enum(
    'NOTIFY', 'OUTPUT', 'ERROR', 'WARN', 'INFO',
    'DEBUG', 'DEBUG1', 'DEBUG2', 'DEBUG3', 'DEBUG4'
    )
local_coding = locale.getdefaultlocale()[1]

class TaskOutput(object):
    num = 0

    def __init__(self, output=None, tp=OutputType.INFO):
        TaskOutput.num += 1
        self.no = TaskOutput.num
        if output is None:
            TaskOutput.num = 0
        self.output = output
        self.type = tp
        self.typestr = OutputType.reverse_mapping[tp]
        self.logtime = time.strftime('%H:%M:%S')

    def __unicode__(self):
        try:
            return self.output.decode(local_coding)
        except UnicodeDecodeError:
            return self.output

    def formatted(self):
        return u"{} [{:6s}] {}".format(
                self.logtime, self.typestr, self.output)

    def formatted_html(self):
        color = 'green'
        if self.type == OutputType.ERROR:
            color = 'red'
        elif self.type == OutputType.WARN:
            color = 'orange'
        elif self.type >= OutputType.DEBUG:
            color = 'gray'
        return (u"<span style='color:gray;'>{}</span> "
                u"<span style='color:{};font-weight:bold;'>"
                u"[{:6s}]</span> {}".format(
                    self.logtime, color, self.typestr, unicode(self))
                    #self.output.decode(local_coding))
                )


class Task(object):

    _id = 0

    def __init__(self, *steps):
        Task._id += 1
        self.id = Task._id
        self.steps = []
        self._lock = Lock()
        self._begin = None
        self._end = None
        self._handlers = None
        self._resume = True
        self._continue = True
        with self._lock:
            for step in steps: self.steps.append(step)

    def init(self, begin, end, *hdlrs):
        self._begin = begin
        self._end = end
        self._handlers = hdlrs

    def put(self, step):
        with self._lock:
            self.steps.append(step)

    def put0(self, step):
        with self._lock:
            self.steps.insert(0, step)

    def get(self):
        with self._lock:
            step = self.steps.pop(0)
        return step

    def resume(self):
        self._resume = True

    def _pause(self):
        time.sleep(0.1)
        if (not self._resume) and self._continue:
            self.put0(self._pause)
    def pause(self):
        self._resume = False
        self.put0(self._pause)

    def _stop(self):
        with self._lock:
            while True: self.steps.pop(0)
    def stop(self):
        "=== task stop ==="
        self._continue = False
        self.put0(self._stop)

    def emit(self, output):
        if self._handlers:
            for hdlr in self._handlers:
                hdlr.send(output)


@singleton
class TaskWorker(object):

    def __init__(self, autostart=True, debug_level=OutputType.INFO):
        self._todo = Queue.Queue()
        self._workthd = Thread(target=self.run)
        #self._dbg_lvl = debug_level
        if autostart:
            self._workthd.start()
        self._currtask = None

    def start(self):
        self._workthd.start()

    def stop(self):
        self.add_task('quit')
        self.stop_task()
        self._workthd.join()

    def pause_task(self):
        if self._currtask:
            self._currtask.pause()
    def resume_task(self):
        if self._currtask:
            self._currtask.resume()
    def stop_task(self):
        if self._currtask and isinstance(self._currtask, Task):
            self._currtask.stop()

    def add_task(self, task):
        self._todo.put(task)

    def add_step(self, step):
        if self._currtask and isinstance(self._currtask, Task):
            self._currtask.put(step)

    def run(self):
        while True:
            try:
                self._currtask = self._todo.get(0.1)
                task = self._currtask
                if type(task) == str and task == 'quit':
                    break
                if task._begin: task._begin.send()
                while True:
                    try:
                        step = task.get()
                        if isinstance(step, types.GeneratorType):
                            output = step.next()
                            task.emit(output)
                            while True:
                                output = step.send(task._continue)
                                task.emit(output)
                        elif isinstance(step, (types.MethodType,types.FunctionType)):
                            step()
                    except IndexError:
                        break
                    except StopIteration:
                        pass
                if task._end: task._end.send()
                ## task.close() will cause RuntimeError: 'generator ignored GeneratorExit'
                ## See http://mail.python.org/pipermail/python-dev/2006-August/068429.html
            except Queue.Empty:
                pass


class TaskHandler(QObject):

    sig = Signal(TaskOutput)

    def __init__(self, *funcs):
        QObject.__init__(self)
        for func in funcs:
            self.sig.connect(func)

    def send(self, output=TaskOutput('')):
        self.sig.emit(output)

class CommandTerminated(Exception):
    pass

def CmdTask(args=[], workdir=None):
    currdir = None
    if workdir:
        currdir = os.getcwdu()
        os.chdir(workdir)
    popen_args = {
        'args': args,
        'stdout': PIPE,
        'stderr': PIPE,
        }
    if os.name != 'posix':
        popen_args['shell'] = True
    code = 0
    p = Popen(**popen_args)
    try:
        cmdline = ' '.join(args)
        #print cmdline
        (yield TaskOutput(u'START: %s ...' % cmdline))
        running = True
        while True:
            line = p.stdout.readline()
            if line == "":
                break
            if not (yield TaskOutput(line.rstrip(), OutputType.OUTPUT)):
                raise CommandTerminated()
        errmsg = p.stderr.read()
        if len(errmsg) > 0:
            raise Exception(errmsg)
        (yield TaskOutput(u'END: %s ...' % args[0]))
    except CommandTerminated:
        code = -2
        (yield TaskOutput(u'TERMINITED: %s' % args[0], OutputType.WARN))
        try:
            p.terminate()
            p.wait()
        except: pass
    except Exception as ex:
        code = -1
        (yield TaskOutput(ex.message, OutputType.ERROR))
    finally:
        if currdir:
            os.chdir(currdir)
        (yield TaskOutput(u'EXIT %d' % code, OutputType.NOTIFY))



if __name__ == "__main__":
    def begin():
        print "begin a task"
    def end():
        print "end a task"
    def hdlr(output):
        print output.output

    #hdlr = MyHandler()
    task = Task(CmdTask(["dir", "D:\\temp\\msys"]))
    task.init(begin, end, TaskHandler(hdlr))
    task.put(CmdTask(["dir", "C:\\tmp"]))
    worker = TaskWorker()
    worker.add_task(task)
    #while True:
    #    try:
    #        msg = my_que.get(0.1)
    #        if msg.output.startswith('EXIT '):
    #        	break
    #        print msg.output
    #    except Queue.Empty:
    #        pass
    time.sleep(2)
    worker.stop()

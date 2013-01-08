#!/usr/bin/env python2
# -* coding: utf-8 -*-

import os
import time
import Queue
from threading import Thread, Lock, ThreadError
from subprocess import *
from yelib.util import enum
from PySide.QtCore import QObject, Signal
import locale

OutputType = enum(
    'NOTIFY', 'OUTPUT', 'ERROR', 'WARN', 'INFO',
    'DEBUG', 'DEBUG1', 'DEBUG2', 'DEBUG3', 'DEBUG4'
    )

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
                    self.logtime, color, self.typestr, self.output) )


class Worker(object):

    def __init__(self, autostart=True, debug_level=OutputType.INFO):
        self._todo = Queue.Queue()
        self._workthd = Thread(target=self.run)
        self._lock = Lock()
        self._task_run = False
        self._dbg_lvl = debug_level
        if autostart:
        	self._workthd.start()

    def __del__(self):
        self.stop()
        self._workthd.join()

    def start(self):
        self._workthd.start()
    def stop(self):
        self._todo.put(('quit', None))
        self.stop_task()
        self._workthd.join()

    def add_task(self, task, hdlr=None, start=True):
        self._todo.put((task, hdlr))
        if start:
            self.start_task()
    def start_task(self):
        self._task_run = True
        self.resume_task()
    def stop_task(self):
        self._task_run = False
        self.resume_task()
    def pause_task(self):
        self._lock.acquire()
    def resume_task(self):
        try:
            self._lock.release()
        except ThreadError:
            pass

    def run(self):
        while True:
            try:
                task, hdlr = self._todo.get(timeout=0.1)
                #print "get one task"
                if type(task) == str and task == 'quit':
                    break
                while self._task_run:
                    self.resume_task()
                    try:
                        output = task.send(None)
                        if hdlr and output.type <= self._dbg_lvl:
                            hdlr.send(output)
                    except StopIteration:
                        break
                    finally:
                        self.pause_task()
                #task.close()
            except Queue.Empty:
                pass


class TaskHandler(QObject):

    sig = Signal(TaskOutput)

    def __init__(self, func):
        QObject.__init__(self)
        self.sig.connect(func)

    def send(self, output):
        self.sig.emit(output)

class CommandTerminated(Exception):
    pass

def CmdTask(*args):
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
        errmsg = p.stderr.read()
        if len(errmsg) > 0:
        	raise Exception(errmsg)
        while True:
            line = p.stdout.readline()
            if line == "":
                break
            (yield TaskOutput(line.rstrip(), OutputType.OUTPUT))
        (yield TaskOutput(u'END: %s' % args[0]))
    except GeneratorExit:
        p.terminate()
        p.wait()
        (yield TaskOutput(u'TERMINITED: %s' % args[0], OutputType.WARN))
    except Exception as ex:
        (yield TaskOutput(ex.message, OutputType.ERROR))
        code = -1
    finally:
        (yield TaskOutput(u'EXIT %d' % code, OutputType.NOTIFY))

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
from yelib.util import coroutine

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


class TaskWorker(object):

    def __init__(self, autostart=True, debug_level=OutputType.INFO):
        self._todo = Queue.Queue()
        self._workthd = Thread(target=self.run)
        self._lock = Lock()
        self._task_run = False
        self._dbg_lvl = debug_level
        if autostart:
        	self._workthd.start()

    #def __del__(self):
    #    self.stop()
    #    self._workthd.join()

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
                if type(task) == str and task == 'quit':
                    break
                output = task.next()
                if hdlr and output.type <= self._dbg_lvl:
                    hdlr.send(output) # For Qt app, emit signal
                try:
                    while True:
                        self.resume_task()
                        output = task.send(self._task_run)
                        if hdlr and output.type <= self._dbg_lvl:
                            hdlr.send(output) # For Qt App, emit Signal
                        self.pause_task()
                except StopIteration:
                    pass
                # Cause RuntimeError: 'generator ignored GeneratorExit'
                # See http://mail.python.org/pipermail/python-dev/2006-August/068429.html
                # task.close()
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
        running = True
        while running:
            line = p.stdout.readline()
            if line == "":
                break
            running = (yield TaskOutput(line.rstrip(), OutputType.OUTPUT))
        if not running:
            raise CommandTerminated()
        (yield TaskOutput(u'END: %s' % args[0]))
    except CommandTerminated:
        (yield TaskOutput(u'TERMINITED: %s' % args[0], OutputType.WARN))
        try: p.terminate()
        except: pass
        p.wait()
    except Exception as ex:
        code = -1
        (yield TaskOutput(ex.message, OutputType.ERROR))
    finally:
        (yield TaskOutput(u'EXIT %d' % code, OutputType.NOTIFY))

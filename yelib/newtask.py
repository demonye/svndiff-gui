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
from yelib.util import singleton

OutputType = enum(
    'NOTIFY', 'OUTPUT', 'ERROR', 'WARN', 'INFO',
    'DEBUG', 'DEBUG1', 'DEBUG2', 'DEBUG3', 'DEBUG4'
    )
TASK_START, TASK_STOP, TASK_PAUSE = 0, 1, 2
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


@singleton
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
        self.add_task('quit', None, False)
        self.stop_task()
        self._workthd.join()

    def add_task(self, task, hdlr=None, start=TASK_START):
        self._todo.put((task, hdlr, start))
        if start:
            self.start_task()

    def start_task(self):
        self._task_run = TASK_START
    def stop_task(self):
        self._task_run = TASK_STOP
    def pause_task(self):
        self._task_run = TASK_PAUSE

    def run(self):
        while True:
            try:
                task, hdlr, self._task_run = self._todo.get(timeout=0.1)
                if type(task) == str and task == 'quit':
                    break
                output = task.next()
                if hdlr and output.type <= self._dbg_lvl:
                    hdlr.send(output)   # For Qt App, emit Signal
                try:
                    while True:
                        if self._task_run == TASK_PAUSE:
                        	time.sleep(0.1)
                        	continue
                        output = task.send(self._task_run == TASK_START)
                        if hdlr and output.type <= self._dbg_lvl:
                            hdlr.send(output)   # For Qt App, emit Signal
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
    (yield TaskOutput(u'ENTER', OutputType.NOTIFY))
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
        (yield TaskOutput(u'END: %s' % args[0]))
    except CommandTerminated:
        (yield TaskOutput(u'TERMINITED: %s' % args[0], OutputType.WARN))
        try:
            p.terminate()
            p.wait()
        except: pass
    except Exception as ex:
        code = -1
        (yield TaskOutput(ex.message, OutputType.ERROR))
    finally:
        (yield TaskOutput(u'EXIT %d' % code, OutputType.NOTIFY))


def CmdTask2(workdir, *args):
    (yield TaskOutput(u'ENTER', OutputType.NOTIFY))
    currdir = os.getcwdu()
    os.chdir(workdir)
    print workdir
    popen_args = {
        'args': args,
        'stdout': PIPE,
        'stderr': PIPE,
        }
    if os.name != 'posix':
        popen_args['shell'] = True
    code = 0
    p = None
    try:
        p = Popen(**popen_args)
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
        (yield TaskOutput(u'END: %s' % args[0]))
    except CommandTerminated:
        (yield TaskOutput(u'TERMINITED: %s' % args[0], OutputType.WARN))
        try:
            p.terminate()
            p.wait()
        except: pass
    except Exception as ex:
        code = -1
        (yield TaskOutput(ex.message, OutputType.ERROR))
    finally:
        os.chdir(currdir)
        (yield TaskOutput(u'EXIT %d' % code, OutputType.NOTIFY))

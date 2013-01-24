#!/usr/bin/env python2
# -* coding: utf-8 -*-

import os
import time
from threading import Thread
from subprocess import *
from yelib.util import enum
from PySide.QtCore import QObject, Signal

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


class Task(QObject):
    _id = 0
    _sig = Signal(TaskOutput)

    def __init__(self, *args, **kwargs):
        Task._id += 1
        self.id = Task._id
        self.args = args
        self.kwargs = kwargs
        self.debug_lvl = kwargs.get('debug_lvl', OutputType.INFO)
        self.terminate = False
        QObject.__init__(self)

    def inst(self, hdlr):
        self._sig.connect(hdlr)

    def uninst(self):
        self._sig.disconnect()

    def _send(self, out, lvl=OutputType.INFO):
        if self.debug_lvl >= lvl:
            self._sig.emit(TaskOutput(out, lvl))

    def emitNotify(self, out):
        self._send(out, OutputType.NOTIFY)
    def emitOutput(self, out):
        self._send(out, OutputType.OUTPUT)
    def emitError(self, out):
        self._send(out, OutputType.ERROR)
    def emitWarn(self, out):
        self._send(out, OutputType.WARN)
    def emitInfo(self, out):
        self._send(out, OutputType.INFO)
    def emitDebug(self, out):
        self._send(out, OutputType.DEBUG)
    def emitDebug1(self, out):
        self._send(out, OutputType.DEBUG1)
    def emitDebug2(self, out):
        self._send(out, OutputType.DEBUG2)
    def emitDebug3(self, out):
        self._send(out, OutputType.DEBUG3)
    def emitDebug4(self, out):
        self._send(out, OutputType.DEBUG4)


# Base class of worker
class Worker(Thread):

    def __init__(self, task):
        self._task = task
        self._continue = True
        self._alive = True
        Thread.__init__(self)
        self.start()

    def stop(self):
        self._continue = False
    def stop_wait(self):
        self.stop()
        self.join()

    def is_alive(self):
        return self._alive

    def _run(self):
        pass

    def _cleanup(self):
        self._task.uninst()
        self._alive = False

    def run(self):
        while self._continue:
            self._run()
        self._cleanup()


class FuncWorker(Worker):

    def _run(self):
        self._task.args[0](*self._task.args[1:], **self._task.kwargs)
        self.stop()


class CmdWorker(Worker):

    def __init__(self, task, interval=-1):
        self._code = 0
        self._interval = interval
        Worker.__init__(self, task)

    def _run(self):
        try:
            popen_args = {
                'args': self._task.args,
                'stdout': PIPE,
                'stderr': STDOUT,
                }
            if os.name != 'posix':
                popen_args['shell'] = True
            p = Popen(**popen_args)
            cmdline = ' '.join(self._task.args)
            self._task.emitInfo(u'START: {} ...'.format(cmdline))
            while self._continue:
                line = p.stdout.readline()
                if line == "":
                    break
                self._task.emitOutput(line.rstrip())
            if self._continue:
                self._task.emitInfo(u'END: {}'.format(self._task.args[0]))
            else:
                p.terminate()
                p.wait()
                self._task.emitWarn(u'TERMINITED: {}'.format(cmdline))
        except Exception as ex:
            self._task.emitError(unicode(ex))
            self._code = -1
        finally:
            self._task.emitNotify('EXIT ' + str(self._code))

        if self._interval < 0:
        	self.stop()
        if self._continue and self._interval > 0:
            time.sleep(self._interval)



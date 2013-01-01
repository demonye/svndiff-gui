import time
from PySide.QtCore import QObject, Signal
from threading import Thread
from subprocess import *
from yelib.util import enum

OutputType = enum(
    'ERROR', 'WARN', 'INFO', 'DEBUG',
    'DEBUG1', 'DEBUG2', 'DEBUG3', 'DEBUG4'
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
        return "{} [{:6s}] {}".format(
                self.logtime, self.typestr, self.output)

class CmdTask(QObject):
    _id = 0
    _sig = Signal(TaskOutput)

    def __init__(self, args=[], debug_lvl=OutputType.INFO):
        CmdTask._id += 1
        self.id = CmdTask._id
        self.args = args
        self.debug_lvl = debug_lvl
        QObject.__init__(self)

    def inst(self, hdlr):
        self._sig.connect(hdlr)

    def send(self, out, lvl=OutputType.INFO):
        if self.debug_lvl >= lvl:
            self._sig.emit(TaskOutput(out, lvl))

    def emitInfo(self, out):
        self.send(out, OutputType.INFO)
    def emitWarn(self, out):
        self.send(out, OutputType.WARN)
    def emitError(self, out):
        self.send(out, OutputType.ERROR)
    def emitDebug(self, out):
        self.send(out, OutputType.DEBUG)
    def emitDebug1(self, out):
        self.send(out, OutputType.DEBUG1)
    def emitDebug2(self, out):
        self.send(out, OutputType.DEBUG2)
    def emitDebug3(self, out):
        self.send(out, OutputType.DEBUG3)
    def emitDebug4(self, out):
        self.send(out, OutputType.DEBUG4)


# Base class of worker
class CmdWorker(Thread):

    def __init__(self, task):
        self._continue = True
        self._task = task
        Thread.__init__(self)
        self.start()

    def stop(self):
        self._continue = False

    def _cleanup(self):
        pass

    def run(self):
        try:
            p = Popen(self._task.args, shell=True, stdout=PIPE, stderr=STDOUT)
            self._task.emitInfo(' '.join(self._task.args))
            while self._continue:
                line = p.stdout.readline()
                if line == "":
                    break
                self._task.emitDebug(line.rstrip())
            if self._continue:
                self._task.emitInfo("Execution OK")
            else:
                p.terminate()
                p.wait()
                self._task.emitWarn("Execution terminated")
        finally:
            self._cleanup()


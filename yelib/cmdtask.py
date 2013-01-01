import time
from PySide.QtCore import QObject, Signal
from threading import Thread
from subprocess import *
from yelib.util import enum

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
        return u"<font style='color:gray;'>{}</font> <font style='color:{};font-weight:bold;'>[{:6s}]</font> {}".format(
                self.logtime, color,
                self.typestr, self.output)

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

    def emitNotify(self, out):
        self.send(out, OutputType.NOTIFY)
    def emitOutput(self, out):
        self.send(out, OutputType.OUTPUT)
    def emitError(self, out):
        self.send(out, OutputType.ERROR)
    def emitWarn(self, out):
        self.send(out, OutputType.WARN)
    def emitInfo(self, out):
        self.send(out, OutputType.INFO)
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

    def run(self):
        try:
            p = Popen(self._task.args, shell=True, stdout=PIPE, stderr=STDOUT)
            cmdline = ' '.join(self._task.args)
            self._task.emitInfo(u'START: {} ...'.format(cmdline))
            while self._continue:
                line = p.stdout.readline()
                if line == "":
                    break
                self._task.emitOutput(line.rstrip())
            if self._continue:
                self._task.emitInfo(u'END: {}'.format(cmdline))
            else:
                p.terminate()
                p.wait()
                self._task.emitWarn(u'TERMINITED: {}'.format(cmdline))
        except Exception as ex:
            self._task.emitError(unicode(ex))
        finally:
            self._task.emitNotify('EXIT')


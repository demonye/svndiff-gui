from threading import Thread
from subprocess import *
import os
import time
import sys
import Queue
from yelib.util import *
from yelib.task import *


def ls(*args):
    p = Popen(["dir"] + list(args),
            shell=True, #close_fds=True,
            stdout=PIPE, stderr=STDOUT)
    while True:
    	line = p.stdout.readline()
        if line == "":
        	break
        yield line.rstrip()

@coroutine
def ls_hdlr():
    try:
        while True:
            msg = (yield)
            print msg
    except GeneratorExit:
        print "ls_hdlr done"

worker = Worker()

task1 = Task(ls, "D:\\")
task2 = Task(ls, "/w", "D:\\")
subscriber = Subscriber(ls_hdlr())
subscriber.subscribe(task1)
subscriber.subscribe(task2)
worker.add(task1)
worker.add(task2)

#worker.add(Task(ls_l, ls_hdlr))
#
time.sleep(2)

worker.exit()

sys.exit(0)

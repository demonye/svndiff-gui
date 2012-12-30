import os
from threading import Thread

def singleton(cls):
    instances = {}
    def getinstance(*args, **kws):
        if cls not in instances:
            instances[cls] = cls(*args, **kws)
        return instances[cls]
    return getinstance


def thread_run(target):
    def execute(*args, **kwargs):
        td = Thread(target=target, args=args, kwargs=kwargs)
        td.start()
    return execute

def coroutine(func):
    def start(*args, **kwargs):
        cr = func(*args, **kwargs)
        cr.next()
        return cr
    return start

def force_rmdir(dirname):
    dirarr = []
    for root,dirs,files in os.walk(dirname):
        dirarr.append(root)
        for f in files:
            os.remove(os.path.join(root, f))
    while True:
        try:
            os.rmdir(dirarr.pop())
        except IndexError:
            break

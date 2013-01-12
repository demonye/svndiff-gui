import os
from threading import Thread
from subprocess import Popen, PIPE

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

def mkdir_p(dirname):
    if os.path.exists(dirname):
        if not os.path.isdir(dirname):
            raise Exception("File %s exists" % dirname)
    else:
        os.makedirs(dirname)

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

def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.iteritems())
    enums['reverse_mapping'] = reverse
    return type('Enum', (), enums)

def runcmd(*args):
    popen_args = {
        'args': args,
        'stdout': PIPE,
        'stderr': PIPE,
        }
    if os.name != 'posix':
        popen_args['shell'] = True
    code = 0
    p = Popen(**popen_args)
    while True:
        line = p.stdout.readline()
        if line == "":
            break
        yield line.rstrip()
    errmsg = p.stderr.read()
    if len(errmsg) > 0:
        raise Exception(errmsg)

from PySide.QtCore import *

class C1(QObject):
    sig = Signal()
    def __init__(self, funcs):
        QObject.__init__(self)
        for f in funcs:
            self.sig.connect(f)
    def send(self):
        self.sig.emit()

def f1():
    print "f1"
def f2():
    print "f2"

c = C1([f1, f2])
c.send()


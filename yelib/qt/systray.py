from PySide.QtCore import *
from PySide.QtGui import *
import time, threading

class yBlinkingThread(threading.Thread):
    def __init__(self, tray):
        super(yBlinkingThread, self).__init__()
        self.blinking = False
        self.running = True
        self.tray = tray
        self.icons = (tray.icon(), QIcon())
        self.current = 0
        #self.cond = threading.Condition() Condition is not suitable for this case

    def do_blink(self, flag=True):
        self.blinking = flag
    def quit(self):
        self.running = False

    def run(self):
        while self.running:
            if self.blinking:
                try:
                    self.tray.setIcon(self.icons[self.current%2])
                except:
                    pass
                self.current += 1
                self.tray.show()
            else:
                if self.current == 1:
                    self.current = 0
                    self.tray.setIcon(self.icons[0])
                    self.tray.show()
            #print("yBlinkingThread: after setIcon")
            time.sleep(0.5)
        return

class ySysTray(QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        super(ySysTray, self).__init__(icon, parent)
        print("ySysTray: after super __init__")
        self.blinkThread = yBlinkingThread(self)
        self.blinkThread.start()

    def blink(self, flag=True):
        self.blinkThread.do_blink(flag)

    def quit(self):
        self.blinkThread.quit()
        self.blinkThread.join()


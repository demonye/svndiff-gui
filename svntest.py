#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
from PySide.QtCore import *
from PySide.QtGui import *

from yelib.task import *
import locale

class MainWindow(QDialog):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setFont(QFont("Monospace", 10))

        # ==== Main Layout ====
        tb = QTableWidget()
        tb.setColumnCount(2)
        tb.setHorizontalHeaderLabels(("Icon", "String"))
        tb.insertRow(0)
        tb.setItem(0, 0, QTableWidgetItem(QIcon('fileadd.ico'), 'icon'))
        tb.setItem(0, 1, QTableWidgetItem(u'Something'))
        self.tb = tb

        self.txt = QTextBrowser()
        self.lt = QVBoxLayout()
        self.lt.addWidget(self.tb)
        self.lt.addWidget(self.txt)
        self.btnStart = QPushButton('Start')
        self.btnResume = QPushButton('Resume')
        self.btnPause = QPushButton('Pause')
        self.btnStop  = QPushButton('Stop')
        ltButton = QHBoxLayout()
        ltButton.addWidget(self.btnStart)
        ltButton.addWidget(self.btnResume)
        ltButton.addWidget(self.btnPause)
        ltButton.addWidget(self.btnStop)
        self.lt.addLayout(ltButton)
        self.setLayout(self.lt)
        self.setWindowTitle('Excute Command')
        # ==== Main Layout ====

        self.worker = TaskWorker()
        self.btnStart.clicked.connect(self.startTask1)
        self.btnResume.clicked.connect(self.resumeTask1)
        self.btnPause.clicked.connect(self.pauseTask1)
        self.btnStop.clicked.connect(self.stopTask1)

        self.txt.setOpenExternalLinks(True)
        self.txt.anchorClicked.connect(self.open_link)
        html = [
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "<a href='D:/yehq'><img src='loading.gif'/></a>",
            #"<a href='http://192.168.22.18'><img src='loading.gif'/></a>",
        ]
        #for t in html:
        #	self.txt.append(t)

        self.coding = locale.getdefaultlocale()[1]


    def open_link(self, url):
        print url.toEncoded()
        pos = self.txt.verticalScrollBar().value()
        self.txt.reload()
        self.txt.verticalScrollBar().setValue(pos)

    def reject(self):
        self.close()

    def closeEvent(self, event):
        self.worker.stop()
        event.accept()

    def startTask1(self):
        def begin():
            print "start Task1"
            self.btnStart.setDisabled(True)
        def end():
            self.btnStart.setDisabled(False)
            print "end Task1"

        task = Task(self.Task1())
        #task = Task(CmdTask("dir", "D:\\"))
        task.init(
                TaskHandler(begin),
                TaskHandler(end),
                TaskHandler(self.Task1Handler)
                )
        self.worker.add_task(task)

    def pauseTask1(self):
        self.worker.pause_task()
    def resumeTask1(self):
        self.worker.resume_task()
    def stopTask1(self):
        self.worker.stop_task()

    def Task1(self):
        (yield TaskOutput("ENTER", OutputType.NOTIFY))
        try:
            for i in xrange(5):
                if not (yield TaskOutput(u"message %d" % i)):
                	raise Exception('stopped')
                time.sleep(1)
            self.worker.add_step(CmdTask(["dir", "D:\\"]))
        except GeneratorExit:
            print "terminate Task1"
        except Exception as ex:
            (yield TaskOutput(ex.message, OutputType.ERROR))
        finally:
            (yield TaskOutput("EXIT 0", OutputType.NOTIFY))

    def Task1Handler(self, msg):
        self.txt.append(unicode(msg))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

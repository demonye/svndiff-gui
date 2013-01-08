#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
from PySide.QtCore import *
from PySide.QtGui import *

from yelib.newtask import *
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

        self.worker = Worker()
        self.btnStart.clicked.connect(self.startTask1)
        self.btnResume.clicked.connect(self.worker.resume_task)
        self.btnPause.clicked.connect(self.worker.pause_task)
        self.btnStop.clicked.connect(self.worker.stop_task)

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

        self.task1_hdlr = TaskHandler(self.Task1Handler)
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
        #self.worker.add_task(self.Task1(), self.task1_hdlr)
        self.worker.add_task(CmdTask("dir1", "D:\\"), self.task1_hdlr)

    def Task1(self):
        print "start Task1"
        try:
            for i in xrange(10):
                (yield TaskOutput(u"message %d" % i))
                time.sleep(1)
        except GeneratorExit:
            print "terminate Task1"
        finally:
            print "end Task1"

    def Task1Handler(self, msg):
        self.txt.append(msg.output.decode(self.coding))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

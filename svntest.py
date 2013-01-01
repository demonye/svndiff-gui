#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
from PySide.QtCore import *
from PySide.QtGui import *
from yelib.qt.layout import *
from yelib.cmdtask import *
import locale

coding = locale.getdefaultlocale()[1]

class MainWindow(QDialog):
    hasOutput = Signal(str)

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setFont(QFont("Monospace", 10))

        self.hasOutput.connect(self.appendLog)

        # ==== Main Layout ====
        #self.txtCommand = QLineEdit('./test.sh')
        self.txtCommand = QLineEdit("dist\\test1")
        self.btnStart = QPushButton('Start')
        self.btnPause = QPushButton('Pause')
        self.btnStop = QPushButton('Stop')
        self.btnExit = QPushButton(u'Exit')

        self.txtLog = QTextBrowser()
        self.txtLog.setReadOnly(True)
        self.txtLog.setOpenExternalLinks(True)

        self.lt = yBoxLayout([
            [ ('', QLabel(u'Command')), ('', self.txtCommand) ],
            [ ('', self.btnStart),
              ('', self.btnPause),
              ('', self.btnStop),
              ('', self.btnExit), ],
            [ ('', self.txtLog) ],
        ])
        self.setLayout(self.lt)
        self.setWindowTitle('Excute Command')
        self.setWindowIcon(QIcon('logo.png'))

        self.btnStart.clicked.connect(self.start)
        self.btnStop.clicked.connect(self.stop)
        self.btnExit.clicked.connect(self.close)
        # ==== Main Layout ====
        self.worker = None

    def start(self):
        cmd = self.txtCommand.text()
        task = CmdTask([cmd], OutputType.DEBUG)
        task.inst(self.appendLog)
        self.worker = CmdWorker(task)

    def stop(self):
        if self.worker:
            self.worker.stop()
            self.worker = None

    def reject(self):
        self.close()

    def closeEvent(self, event):
        self.stop()
        event.accept()

    @Slot(TaskOutput)
    def appendLog(self, msg):
        #self.txtLog.appendPlainText(logtext)
        if msg.type == OutputType.OUTPUT:
            self.txtLog.append(msg.output.decode(coding))
        else:
            self.txtLog.append(msg.formatted())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

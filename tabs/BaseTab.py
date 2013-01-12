# -* coding: utf-8 -*-

import os
from PySide.QtCore import *
from PySide.QtGui import *
from yelib.qt.layout import *
from yelib.util import singleton
from yelib.newtask import TaskOutput, OutputType

class BaseTab(QWidget):


    def __init__(self, parent=None):
        super(BaseTab, self).__init__(parent)
        self.parent = parent
        #self.setting = parent.tabSettings
        self.setFont(QFont("Monospace", 10))
        settings = None

    def init(self, *args, **kwargs):
        pass

    def showLoading(self, msg, loading=True):
        self.parent.parent().showLoading(msg, loading)

    def appendLog(self, log, print_output=False):
        if log.type == OutputType.NOTIFY:
            return
        pt = self.parent
        if log.type == OutputType.OUTPUT:
            if print_output:
                pt.append_log(unicode(log))
        else:
            pt.append_log(log.formatted_html())

    def taskHandler(self, taskmsg, loading=None, btn=None, finalword=None):
        if taskmsg.type == OutputType.NOTIFY:
            if taskmsg.output == u'ENTER':
                if btn: btn.setDisabled(True)
                if loading: self.showLoading(loading, True)
            elif taskmsg.output.startswith('EXIT '):
                code = int(taskmsg.output.split()[1])
                if code == 0 and finalword:
                    self.appendLog(TaskOutput(finalword))
                if loading: self.showLoading('', False)
                if btn: btn.setDisabled(False)
            return None
        self.appendLog(taskmsg)
        return taskmsg.type == OutputType.OUTPUT and taskmsg.output or None

class SelectFile(yBoxLayout):

    def __init__(self, label, title, filter="*.*", type="file"):

        self.txt = QLineEdit()
        self.label = label
        self.title =  title
        self.filter = filter
        self.type = type
        self.btn = QPushButton(' / ')
        self.btn.setFixedWidth(20)
        self.btn.clicked.connect(self.selectFile)

        ltData = [
            [ QLabel(self.label), self.txt, self.btn ]
        ]
        super(SelectFile, self).__init__(ltData)
        #self.setLayout(lt)
        #self.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.MinimumExpanding))
        #self.setContentsMargins(0,0,0,0)
        #self.setBaseSize(0, 0)
        #self.setStyleSheet("margin:0px;padding:0px")

    def text(self):
        return self.txt.text()
    def setText(self, text):
        return self.txt.setText(text)

    def selectFile(self):
        if self.type == "file":
            fname = QFileDialog.getOpenFileName(None,
                    self.title, self.text(), self.filter)
            if len(fname) > 0:
                self.txt.setText(fname[0].replace('/', os.sep))
        elif self.type == "dir":
            fname = QFileDialog.getExistingDirectory(None,
                    self.title, self.text())
            if len(fname) > 0:
                self.txt.setText(fname)



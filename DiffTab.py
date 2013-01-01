#!/usr/bin/env python2
# -* coding: utf-8 -*-

import os
import time
from PySide.QtCore import *
from PySide.QtGui import *
from yelib.qt.layout import *
from yelib.cmdtask import *
from yelib.util import force_rmdir

class DiffTab(QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self)
        self.parent = parent
        self.setFont(QFont("Monospace", 10))
        tb = QTableWidget()
        tb.setColumnCount(5)
        tb.setSelectionBehavior(QAbstractItemView.SelectRows)
        tb.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tb.setHorizontalHeaderLabels(("Check", "Icon", "Status", "File", "FullFile"))
        tb.horizontalHeader().setResizeMode(0, QHeaderView.Fixed)
        tb.horizontalHeader().setResizeMode(1, QHeaderView.Fixed)
        tb.horizontalHeader().setResizeMode(3, QHeaderView.Stretch)
        tb.horizontalHeader().resizeSection(0, 30) 
        tb.horizontalHeader().resizeSection(1, 25) 
        tb.setColumnHidden(2, True)
        tb.setColumnHidden(4, True)
        tb.horizontalHeader().hide()
        tb.verticalHeader().hide()
        tb.setAlternatingRowColors(True)

        self.txtBugId = QLineEdit()
        self.txtBugId.setMaximumWidth(120)
        self.btnFind = QPushButton(u'Get Changed Files')
        self.btnDiff = QPushButton(u'    Make Diff    ')
        self.btnUpload = QPushButton(u'Upload')
        self.lstFiles = tb
        self.lt = yBoxLayout([
            [ ('', self.lstFiles) ],
            [ ('', self.btnFind), ('', self.btnDiff), None,
              ('', QLabel(u'Bug Id')), ('', self.txtBugId),
              ('', self.btnUpload),
            ],
        ])
        self.setLayout(self.lt)

        self.statusIcons = {
                'A': QIcon('fileadd.ico'),
                'M': QIcon('filemodify.ico'),
                'D': QIcon('filedelete.ico'),
                }
        self.worker = None
        self.btnFind.clicked.connect(self.getStatus)
        self.btnDiff.clicked.connect(self.makeDiff)
        self.btnUpload.clicked.connect(self.uploadFiles)


    def conf(self, key):
        return self.parent.tab.widget(1).conf(key)

#    def showEvent(self, event):
#        event.accept()

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
        event.accept()

    def getStatus(self):
        self.btnFind.setDisabled(True)
        cmds = ["svndiff", "-c", "-s", self.parent.txtSrcDir.text()]
        task = CmdTask(cmds)
        task.inst(self.showChangedFiles)
        self.worker = CmdWorker(task)

    @Slot(TaskOutput)
    def showChangedFiles(self, msg):
        if msg.type == OutputType.NOTIFY and msg.output == 'EXIT':
            self.btnFind.setDisabled(False)
            return
        if msg.type == OutputType.OUTPUT and msg.output:
            tb = self.lstFiles
            m = msg.output.split()
            n = tb.rowCount()
            tb.insertRow(n)
            item = QTableWidgetItem()
            item.setCheckState(Qt.Checked)
            tb.setItem(n, 0, item)
            tb.setItem(n, 1, QTableWidgetItem(self.statusIcons[m[0]], ''))
            tb.setItem(n, 2, QTableWidgetItem(m[0]))
            tb.setItem(n, 3, QTableWidgetItem(m[1]))
            tb.setItem(n, 4, QTableWidgetItem(m[2]))
        else:
            self.appendLog(msg)


    def makeDiff(self):
        self.btnDiff.setDisabled(True)
        files = []
        tb = self.lstFiles
        for i in xrange(tb.rowCount()):
            item = tb.item(i, 0)
            if item.checkState() == Qt.Checked:
                files.append(tb.item(i, 4).text())
        cmds = ["svndiff", "-s", self.parent.txtSrcDir.text()] + files
        task = CmdTask(cmds)
        task.inst(self.readyToUpload)
        self.worker = CmdWorker(task)

    @Slot(TaskOutput)
    def readyToUpload(self, msg):
        if msg.type == OutputType.NOTIFY and msg.output == 'EXIT':
            self.appendLog(TaskOutput(u"*** Check directory 'hdiff' to review the result ***"))
            self.btnDiff.setDisabled(False)
            return
        self.appendLog(msg)

    def uploadFiles(self):
        if self.txtBugId.text() == "":
            self.appendLog(TaskOutput(u"!!! Please input Bug Id !!!", OutputType.WARN))
            return

        self.btnUpload.setDisabled(True)
        pt = self.parent
        bugid = self.txtBugId.text()
        svnid = pt.txtSvnId.text()
        self.result_url = "http://10.1.1.5/diffs/{}/{}".format(svnid, bugid)
        rmtdir = os.path.join(pt.txtRmtDir.text(), svnid, bugid).replace(os.sep, '/')
        cmds = ["uploadfiles", pt.txtSrvHost.text(),
                "hdiff", rmtdir, "-u", pt.txtSrvUser.text() ]
        if pt.rdoPwd.isChecked():
            cmds.append("-p")
            cmds.append(pt.txtSrvPwd.text())
        elif pt.rdoKey.isChecked():
            cmds.append("-k")
            cmds.append(pt.txtKeyFile.text())
        task = CmdTask(cmds)
        task.inst(self.uploadCompleted)
        self.worker = CmdWorker(task)


    @Slot(TaskOutput)
    def uploadCompleted(self, msg):
        if msg.type == OutputType.NOTIFY and msg.output == 'EXIT':
            self.appendLog(TaskOutput(
                u"*** Click <a href='{}'>Here</a> to check the result ***".format(
                    self.result_url)))
            self.btnUpload.setDisabled(False)
            return
        self.appendLog(msg)


    def appendLog(self, log):
        if log.type == OutputType.NOTIFY:
            return
        self.parent.append_log(log.formatted_html())


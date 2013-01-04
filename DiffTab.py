#!/usr/bin/env python2
# -* coding: utf-8 -*-

import os
import time
from PySide.QtCore import *
from PySide.QtGui import *
from yelib.qt.layout import *
from yelib.cmdtask import *
from yelib.util import force_rmdir
from paramiko import SSHClient, AutoAddPolicy
from threading import Thread

import locale
coding = locale.getdefaultlocale()[1]

class DiffTab(QWidget):

    ssh_sig = Signal(TaskOutput)

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
                'A': 'fileadd.ico',
                'M': 'filemodify.ico',
                'D': 'filedelete.ico',
                }
        self.worker = None
        self.sshStop = False
        self.sshtask = None
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
        if self.sshtask:
            self.sshStop = True
            self.sshtask.join()
        event.accept()

    def getStatus(self):
        self.btnFind.setDisabled(True)
        cmds = ["svndiff", "-c", "-s", self.parent.txtSrcDir.text()]
        task = CmdTask(cmds)
        task.inst(self.showChangedFiles)

        tb = self.lstFiles
        for i in xrange(tb.rowCount()):
            tb.removeRow(0)
        self.worker = CmdWorker(task)

    @Slot(TaskOutput)
    def showChangedFiles(self, msg):
        if msg.type == OutputType.NOTIFY and msg.output.startswith('EXIT '):
            self.btnFind.setDisabled(False)
            return
        if msg.type == OutputType.OUTPUT and msg.output:
            #print "****", msg.output
            tb = self.lstFiles
            m = msg.output.split()
            if m[0] not in self.statusIcons:
                self.appendLog(msg)
                return
            n = tb.rowCount()
            tb.insertRow(n)
            item = QTableWidgetItem()
            item.setCheckState(Qt.Checked)
            tb.setItem(n, 0, item)
            tb.setItem(n, 1, QTableWidgetItem(QIcon(self.statusIcons[m[0]]), m[0]))
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
        if msg.type == OutputType.NOTIFY and msg.output.startswith('EXIT '):
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
        if svnid == "":
            svnid = "yanpeng.wang"
        self.result_url = "http://10.1.1.5/diffs/{}/{}".format(svnid, bugid)
        rmtdir = os.path.join(pt.txtRmtDir.text(), svnid, bugid).replace(os.sep, '/')

        conargs = {
            'hostname': pt.txtSrvHost.text(),
            'username': pt.txtSrvUser.text(),
            'timeout' : 10,
            'compress': True,
            }
        if pt.rdoPwd.isChecked():
            conargs['password'] = pt.txtSrvPwd.text()
        elif pt.rdoKey.isChecked():
            conargs['key_filename'] = pt.txtKeyFile.text()

        self.ssh_sig.connect(self.uploadHandler)
        self.sshtask = Thread(target=self._upload, args=(rmtdir,), kwargs=conargs)
        self.sshtask.start()


    def _upload(self, dstdir, **sshargs):
        sshcli = SSHClient()
        sftpcli = None
        code = 0
        self.ssh_sig.emit(TaskOutput(u'Conntecting to {} ...'.format(sshargs['hostname'])))
        try:
            sshcli.set_missing_host_key_policy(AutoAddPolicy())
            sshcli.connect(**sshargs)
            self.ssh_sig.emit(TaskOutput(u'Connected!'))
            ret = sshcli.exec_command("[ -d {0} ] && rm -rf {0}; mkdir -p {0}".format(dstdir))
            errstr = ret[2].read()
            if errstr != '':
                raise Exception(errstr)
            sftpcli = sshcli.open_sftp()
            srcdir = "hdiff"
            for f in os.listdir(srcdir):
                if self.sshStop:
                    self.ssh_sig.emit(TaskOutput(u'Terminating ...'))
                    return
                if f.lower().endswith('.html'):
                    localfile = os.path.join(srcdir, f)
                    remotefile = os.path.join(dstdir, f).replace(os.sep, '/')
                    self.ssh_sig.emit(TaskOutput(u'Uploading ' + f + ' ...'))
                    sftpcli.put(localfile, remotefile)
        except Exception as ex:
            self.ssh_sig.emit(TaskOutput(unicode(ex), OutputType.ERROR))
            code = -1
        finally:
            if sftpcli: sftpcli.close()
            sshcli.close()
            self.ssh_sig.emit(TaskOutput('EXIT '+str(code), OutputType.NOTIFY))
            self.ssh_sig.disconnect()


    @Slot(TaskOutput)
    def uploadHandler(self, msg):
        if msg.type == OutputType.NOTIFY and msg.output.startswith('EXIT '):
            code = int(msg.output.split()[1])
            if code == 0:
                self.appendLog(TaskOutput(
                    u"*** Click <a href='{}'>Here</a> to check the result ***".format(
                        self.result_url)))
            self.btnUpload.setDisabled(False)
            self.sshtask = None
            return
        self.appendLog(msg)


    def appendLog(self, log):
        if log.type == OutputType.NOTIFY:
            return
        if log.type == OutputType.OUTPUT:
            self.parent.append_log(log.output.decode(coding))
        else:
            self.parent.append_log(log.formatted_html())


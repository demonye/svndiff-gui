#!/usr/bin/env python2
# -* coding: utf-8 -*-

import os
from PySide.QtCore import *
from PySide.QtGui import *
from yelib.qt.layout import *
#from yelib.task import *
from yelib.newtask import *
from yelib.util import coroutine
from paramiko import SSHClient, AutoAddPolicy
from tabs.BaseTab import BaseTab


class DiffTab(BaseTab):

    def __init__(self, parent=None):
        super(DiffTab, self).__init__(parent)

        self.hdiff_dir = "data/hdiff"

        # ==== File List ====
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
        self.lstFiles = tb
        # ==== File List ====

        self.txtSrcDir = QLineEdit()
        self.btnSrcDir = QPushButton(' / ')
        self.btnSrcDir.setFixedWidth(20)
        self.btnSrcDir.clicked.connect(self.selectSrcDir)
        self.txtBugId = QLineEdit()
        self.txtBugId.setMaximumWidth(120)
        self.btnFind = QPushButton(u'Get Status')
        self.btnDiff = QPushButton(u'Make Diff')
        self.btnUpload = QPushButton(u'Upload')
        self.lbSlikSvn = QLabel(
                u"<span style='color:dimgray'>"
                u"If you are using Windows, please install "
                u"<a href='http://www.sliksvn.com/en/download'>"
                u"Slik SVN</a> first.</span>"
                )
        self.lbSlikSvn.setTextFormat(Qt.RichText)
        self.lbSlikSvn.setOpenExternalLinks(True)
        
        self.lt = yBoxLayout([
            [ QLabel(u'Source Path'), self.txtSrcDir, self.btnSrcDir ],
            [ self.lstFiles ],
            [ self.lbSlikSvn ],
            [ self.btnFind, self.btnDiff, None,
              QLabel(u'Bug Id'), self.txtBugId,
              self.btnUpload,
            ],
        ])
        self.setLayout(self.lt)

        self.statusIcons = {
                'A': QIcon('fileadd.png'),
                'M': QIcon('filemodify.png'),
                'D': QIcon('filedelete.png'),
                }
        self.worker = TaskWorker()
        self.btnFind.clicked.connect(self.getStatus)
        self.btnDiff.clicked.connect(self.makeDiff)
        self.btnUpload.clicked.connect(self.uploadFiles)

    def selectSrcDir(self):
        srcdir = self.txtSrcDir
        dirname = QFileDialog.getExistingDirectory(
                self, u'Select Source Directory', srcdir.text())
        if len(dirname) > 0:
            srcdir.setText(dirname)


#    def showEvent(self, event):
#        event.accept()

    def closeEvent(self, event):
        self.worker.stop()
        event.accept()

    def getStatus(self):
        srcdir = self.txtSrcDir.text()
        if srcdir == "":
            self.appendLog(TaskOutput(u'Please set the path of source code in Setting Tab!', OutputType.WARN))
            return
        self.worker.add_task(
                CmdTask("svndiff", "-c", "-s", srcdir),
                TaskHandler(self.showChangedFiles)
                )
        tb = self.lstFiles
        for i in xrange(tb.rowCount()):
            tb.removeRow(0)

    @Slot(TaskOutput)
    def showChangedFiles(self, msg):
        ret = self.taskHandler(msg, u'Getting svn status ... ', self.btnFind)
        if ret is not None:
            tb = self.lstFiles
            m = ret.split()
            if m[0] not in self.statusIcons:
                self.appendLog(
                    TaskOutput(u'Not recognized flag: %s' % m[0],
                        OutputType.ERROR)
                    )
                return
            n = tb.rowCount()
            tb.insertRow(n)
            item = QTableWidgetItem()
            item.setCheckState(Qt.Checked)
            tb.setItem(n, 0, item)
            tb.setItem(n, 1, QTableWidgetItem(self.statusIcons[m[0]], m[0]))
            tb.setItem(n, 2, QTableWidgetItem(m[0]))
            tb.setItem(n, 3, QTableWidgetItem(m[1]))
            tb.setItem(n, 4, QTableWidgetItem(m[2]))


    def makeDiff(self):
        srcdir = self.txtSrcDir.text()
        files = []
        tb = self.lstFiles
        for i in xrange(tb.rowCount()):
            item = tb.item(i, 0)
            if item.checkState() == Qt.Checked:
                files.append(tb.item(i, 4).text())
        cmds = [ "svndiff", "-s", srcdir, "-d", self.hdiff_dir ] + files
        self.worker.add_task(
                CmdTask(*cmds),
                TaskHandler(self.readyToUpload) )

    @Slot(TaskOutput)
    def readyToUpload(self, msg):
        if not hasattr(self, 'fwReadyToUpload'):
            hdiff_dir = os.path.join(os.getcwdu(), self.hdiff_dir)
            hdiff_dir = hdiff_dir.replace(os.sep, '/')
            self.fwReadyToUpload = (
                u"Go to <a href='{}'>HDIFF Directory</a> "
                "to check the result.".format(hdiff_dir)
                )
        self.taskHandler(msg, u'Making diff files ... ',
                self.btnDiff, self.fwReadyToUpload)

    def uploadFiles(self):
        if self.txtBugId.text() == "":
            self.appendLog(TaskOutput(u"!!! Please input Bug Id !!!", OutputType.WARN))
            return

        st = self.settings
        rmtdir = st.txtRmtDir.text()
        bugid = self.txtBugId.text()
        svnid = st.txtSvnId.text()
        if svnid == "":
            svnid = "yanpeng.wang"
        self.result_url = "{}/{}/{}".format(st.txtHttpUrl.text().rstrip('/'), svnid, bugid)
        rmtdir = os.path.join(rmtdir, svnid, bugid).replace(os.sep, '/')

        sshargs = {
            'hostname': st.txtDiffSrv.text(),
            'username': st.txtSrvUser.text(),
            'timeout' : 10,
            'compress': True,
            }
        if st.rdoPwd.isChecked():
            sshargs['password'] = st.txtSrvPwd.text()
        elif st.rdoKey.isChecked():
            sshargs['key_filename'] = st.txtKeyFile.text()

        self.worker.add_task(
                self._uploadFiles(rmtdir, **sshargs),
                TaskHandler(self.uploadHandler)
                )

    def _uploadFiles(self, dstdir, **sshargs):
        (yield TaskOutput(u'ENTER', OutputType.NOTIFY))
        sshcli = SSHClient()
        sftpcli = None
        code = 0
        try:
            if not (yield TaskOutput(u'Conntecting to %s ...' % sshargs['hostname'])):
                raise CommandTerminated()
            sshcli.set_missing_host_key_policy(AutoAddPolicy())
            sshcli.connect(**sshargs)
            if not (yield TaskOutput(u'Connected, ready to upload ...')):
                raise CommandTerminated()
            ret = sshcli.exec_command("[ -d {0} ] && rm -rf {0}; mkdir -p {0}".format(dstdir))
            errstr = ret[2].read()
            if errstr != '':
                raise Exception(errstr)
            sftpcli = sshcli.open_sftp()
            for f in os.listdir(self.hdiff_dir):
                if f.lower().endswith('.html'):
                    localfile = os.path.join(self.hdiff_dir, f)
                    remotefile = os.path.join(dstdir, f).replace(os.sep, '/')
                    if not (yield TaskOutput(u'Uploading %s ...' % f)):
                        raise CommandTerminated()
                    sftpcli.put(localfile, remotefile)
        except CommandTerminated:
            code = -2
            (yield TaskOutput(u'Uploading Terminited', OutputType.WARN))
        except Exception as ex:
            code = -1
            (yield TaskOutput(ex.message, OutputType.ERROR))
        finally:
            if sftpcli: sftpcli.close()
            sshcli.close()
            (yield TaskOutput(u'EXIT %d' % code, OutputType.NOTIFY))


    @Slot(TaskOutput)
    def uploadHandler(self, msg):
        if not hasattr(self, 'fwUpload'):
            self.fwUpload = (
                u"Click <a href='{0}'>{0}</a> to review the result.".format(
                    self.result_url)
                )
        self.taskHandler(msg, u'Uploading diff files ... ',
                self.btnUpload, self.fwUpload)



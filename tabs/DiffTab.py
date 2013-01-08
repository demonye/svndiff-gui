#!/usr/bin/env python2
# -* coding: utf-8 -*-

import os
from PySide.QtCore import *
from PySide.QtGui import *
from yelib.qt.layout import *
#from yelib.task import *
from yelib.newtask import *
from paramiko import SSHClient, AutoAddPolicy
from tabs.BaseTab import BaseTab


class DiffTab(BaseTab):

    def __init__(self, parent=None):
        super(DiffTab, self).__init__(parent)

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
            [ ('', QLabel(u'Source Path')), ('', self.txtSrcDir), ('', self.btnSrcDir) ],
            [ ('', self.lstFiles) ],
            [ ('', self.lbSlikSvn) ],
            [ ('', self.btnFind), ('', self.btnDiff), None,
              ('', QLabel(u'Bug Id')), ('', self.txtBugId),
              ('', self.btnUpload),
            ],
        ])
        self.setLayout(self.lt)

        self.statusIcons = {
                'A': QIcon('fileadd.png'),
                'M': QIcon('filemodify.png'),
                'D': QIcon('filedelete.png'),
                }
        self.worker = Worker()
        #self.workers = {}
        #self.sshtask = None
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
        #if self.sshtask:
        #    self.sshtask.terminate = True
        #for w in self.workers.values():
        #	w.stop_wait()
        self.worker.stop()
        event.accept()

    def getStatus(self):
        srcdir = self.txtSrcDir.text()
        if srcdir == "":
            self.appendLog(TaskOutput(u'Please set the path of source code in Setting Tab!', OutputType.WARN))
            return
        self.btnFind.setDisabled(True)
        self.showLoading(u'Getting svn status of ' + srcdir, True)
        self.worker.add_task(
                CmdTask("svndiff", "-c", "-s", srcdir),
                TaskHandler(self.showChangedFiles)
                )
        tb = self.lstFiles
        for i in xrange(tb.rowCount()):
            tb.removeRow(0)

    @Slot(TaskOutput)
    def showChangedFiles(self, msg):
        if msg.type == OutputType.NOTIFY and msg.output.startswith('EXIT '):
            self.showLoading('', False)
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
            tb.setItem(n, 1, QTableWidgetItem(self.statusIcons[m[0]], m[0]))
            tb.setItem(n, 2, QTableWidgetItem(m[0]))
            tb.setItem(n, 3, QTableWidgetItem(m[1]))
            tb.setItem(n, 4, QTableWidgetItem(m[2]))
        else:
            self.appendLog(msg)


    def makeDiff(self):
        srcdir = self.txtSrcDir.text()
        self.btnDiff.setDisabled(True)
        self.showLoading(u'Making diff files of ' + srcdir, True)
        files = []
        tb = self.lstFiles
        for i in xrange(tb.rowCount()):
            item = tb.item(i, 0)
            if item.checkState() == Qt.Checked:
                files.append(tb.item(i, 4).text())
        cmds = ["svndiff", "-s", srcdir] + files
        self.worker.add_task(
                CmdTask(*cmds),
                TaskHandler(self.readyToUpload) )

    @Slot(TaskOutput)
    def readyToUpload(self, msg):
        if msg.type == OutputType.NOTIFY and msg.output.startswith('EXIT '):
            code = int(msg.output.split()[1])
            if code == 0:
                hdiff_dir = os.path.join(os.getcwdu(), "hdiff").replace(os.sep, '/')
                self.appendLog(TaskOutput(u"Go to <a href='{}'>HDIFF Directory</a> to check the result.".format(hdiff_dir)))
            self.showLoading('', False)
            self.btnDiff.setDisabled(False)
            return
        self.appendLog(msg)

    def uploadFiles(self):
        if self.txtBugId.text() == "":
            self.appendLog(TaskOutput(u"!!! Please input Bug Id !!!", OutputType.WARN))
            return

        st = self.settings
        rmtdir = st.txtRmtDir.text()
        self.btnUpload.setDisabled(True)
        self.showLoading(u'Uploading diff files to ' + rmtdir, True)
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

        self.sshtask = Task(self._upload, rmtdir, **sshargs)
        self.sshtask.inst(self.uploadHandler)
        self.workers['ssh'] = FuncWorker(self.sshtask)


    def _upload(self, dstdir, **sshargs):
        sshcli = SSHClient()
        sftpcli = None
        code = 0
        self.sshtask.emitInfo(u'Conntecting to {} ...'.format(sshargs['hostname']))
        try:
            sshcli.set_missing_host_key_policy(AutoAddPolicy())
            sshcli.connect(**sshargs)
            self.sshtask.emitInfo(u'Connected, ready to upload ...')
            ret = sshcli.exec_command("[ -d {0} ] && rm -rf {0}; mkdir -p {0}".format(dstdir))
            errstr = ret[2].read()
            if errstr != '':
                raise Exception(errstr)
            sftpcli = sshcli.open_sftp()
            srcdir = "hdiff"
            for f in os.listdir(srcdir):
                if self.sshtask.terminate:
                    self.sshtask.emitInfo(u'Terminating ...')
                    return
                if f.lower().endswith('.html'):
                    localfile = os.path.join(srcdir, f)
                    remotefile = os.path.join(dstdir, f).replace(os.sep, '/')
                    self.sshtask.emitInfo(u'Uploading ' + f + ' ...')
                    sftpcli.put(localfile, remotefile)
        except Exception as ex:
            self.sshtask.emitError(unicode(ex))
            code = -1
        finally:
            if sftpcli: sftpcli.close()
            sshcli.close()
            self.sshtask.emitNotify('EXIT '+str(code))


    @Slot(TaskOutput)
    def uploadHandler(self, msg):
        if msg.type == OutputType.NOTIFY and msg.output.startswith('EXIT '):
            code = int(msg.output.split()[1])
            if code == 0:
                self.appendLog(TaskOutput(
                    u"Click <a href='{0}'>{0}</a> to review the result.".format(
                        self.result_url)))
            self.showLoading('', False)
            self.btnUpload.setDisabled(False)
            return
        self.appendLog(msg)



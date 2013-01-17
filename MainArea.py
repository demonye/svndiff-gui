#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys, os
import glob
from PySide.QtCore import *
from PySide.QtGui import *
from paramiko import SSHClient, AutoAddPolicy
import zipfile
import shutil

from yelib.qt.layout import *
from yelib.qt.widgets import *
from yelib.newtask import *
from yelib.util import *

from SettingsDlg import decrypt


hdiff_dir = os.path.join("data", "hdiff")
backup_dir = os.path.join("data", "backup")
clstemp_dir = os.path.join("data", "clstemp")
approot_dir = os.path.join("data", "approot")
target_dir = os.path.join("data", "target")
target_file = os.path.join(target_dir, "target.jar")

class MainArea(QWidget):

    def __init__(self, parent=None):
        super(MainArea, self).__init__(parent)

        self.settings = parent.dlgSettings
        self.jar_bin = self.settings.conf('app', 'jar bin')

        # ==== File List ====
        # Application Combo
        self.cboApp = QComboBox()
        self.cboApp.activated.connect(self.selectApp)
        self.txtSrcDir = QLineEdit()
        self.txtSrcDir.setReadOnly(True)
        self.txtSrcDir.setMinimumWidth(350)

        # Main Group
        self.grpMain = QGroupBox('Work Area')
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
        ltMain = yBoxLayout([
            [ 'App', self.cboApp, None,
              'Source Dir', self.txtSrcDir ],
            [ self.lstFiles ],
        ])
        self.grpMain.setLayout(ltMain)
        self.grpMain.setMinimumSize(700, 400)
        # ==== Main ====

        # ==== Log ====
        self.grpLog = QGroupBox(u'Information of Execution')
        self.txtLog = QTextBrowser()
        self.txtLog.setReadOnly(True)
        self.txtLog.setMinimumHeight(150)
        self.txtLog.setOpenExternalLinks(True)
        ltLog = yBoxLayout([
            [ self.txtLog ],
        ])
        self.grpLog.setLayout(ltLog)
        self.grpLog.setSizePolicy(
            QSizePolicy.Policy(QSizePolicy.Preferred),
            QSizePolicy.Policy(QSizePolicy.Fixed),
            )
        # ==== Log ====

        # ==== Buttons ====
        self.btnGetStatus = QPushButton(QIcon('image/getstatus1.png'), u'Get Status')
        self.btnGetStatus.setFixedSize(120, 30)
        self.btnMakeDiff = QPushButton(QIcon('image/makediff1.png'), u'Make Diff')
        self.btnMakeDiff.setFixedSize(120, 30)
        self.btnDeployNew = QPushButton(QIcon('image/deployclass1.png'), u'Deploy New')
        self.btnDeployNew.setFixedSize(120, 30)
        # ==== Buttons ====

        # ==== Main Layout ====
        #self.btnExit = QPushButton(u'Exit')
        self.txtBugId = QLineEdit(self.settings.conf('diff', 'last bug'))
        self.txtBugId.setFixedWidth(100)
        lt = yBoxLayout([
            [ self.grpMain ],
            [ self.btnGetStatus, None,
              QLabel('Bug Id'), self.txtBugId, self.btnMakeDiff, None,
              self.btnDeployNew ],
            [ self.grpLog ],
        ])
        #self.btnExit.clicked.connect(self.close)
        self.setLayout(lt)
        self.updateAppList()
        # ==== Main Layout ====

        self.statusIcons = {
                'A': QIcon('image/file_add.png'),
                'M': QIcon('image/file_edit.png'),
                'D': QIcon('image/file_delete.png'),
                }

        self.worker = TaskWorker()
        self.btnGetStatus.clicked.connect(self.getStatus)
        self.btnMakeDiff.clicked.connect(self.makeDiff)
        self.btnDeployNew.clicked.connect(self.deployNew)
        self.workdir = os.getcwdu()
        self.targetFile = None


    def appendLog(self, log, print_output=False):
        if log.type == OutputType.NOTIFY:
            return
        if log.type == OutputType.OUTPUT:
            if print_output:
                self.txtLog.append(unicode(logtext))
        else:
            self.txtLog.append(log.formatted_html())

    def taskHandler(self, taskmsg, loading=None, btn=None, finalword=None):
        pt = self.parent()
        if taskmsg.type == OutputType.NOTIFY:
            if taskmsg.output == u'ENTER':
                if btn: btn.setDisabled(True)
                if loading: pt.showLoading(loading, True)
            elif taskmsg.output.startswith('EXIT '):
                code = int(taskmsg.output.split()[1])
                if code == 0 and finalword:
                    self.appendLog(TaskOutput(finalword))
                if loading: pt.showLoading('', False)
                if btn: btn.setDisabled(False)
            return None
        self.appendLog(taskmsg)
        return taskmsg.type == OutputType.OUTPUT and taskmsg.output or None

    def selectApp(self, idx):
        sect = self.cboApp.itemText(idx)
        srcdir = self.settings.conf(sect, 'source root')
        self.txtSrcDir.setText(srcdir)

    def updateAppList(self):
        st = self.settings
        applist = st.conf('app', 'list').split(',')
        self.cboApp.clear()
        for app in applist:
            self.cboApp.addItem(QIcon('image/application.png'), app.strip())
        if self.cboApp.count() > 0:
            self.selectApp(0)

    def getStatus(self):
        srcdir = self.txtSrcDir.text()
        if srcdir == "":
            self.appendLog(TaskOutput(u'Please set the path of source code in Setting Tab!', OutputType.WARN))
            return
        self.worker.add_task(
                CmdTask(os.path.join("bin", "svndiff"), "-c", "-s", srcdir),
                TaskHandler(self.getStatusHandler)
                )
        tb = self.lstFiles
        for i in xrange(tb.rowCount()):
            tb.removeRow(0)

    @Slot(TaskOutput)
    def getStatusHandler(self, msg):
        ret = self.taskHandler(msg, u'Getting svn status ... ', self.btnGetStatus)
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
        if self.txtBugId.text() == "":
            self.appendLog(TaskOutput(u"!!! Please input Bug Id !!!", OutputType.WARN))
            return

        srcdir = self.txtSrcDir.text()
        files = []
        tb = self.lstFiles
        for i in xrange(tb.rowCount()):
            item = tb.item(i, 0)
            if item.checkState() == Qt.Checked:
                files.append(tb.item(i, 4).text())
        cmds = [
                os.path.join("bin", "svndiff"),
                "-s", srcdir, "-d", hdiff_dir,
                "-f", os.path.join("bin", "diff"),
                "-v", os.path.join("bin", "svn"),
                "-t", os.path.join("html", "diff_template.html"),
                ] + files
        self.worker.add_task(
                CmdTask(*cmds),
                TaskHandler(self.makeDiffHandler) )


        st = self.settings
        bugid = self.txtBugId.text()
        rmtdir = st.conf('diff', 'remote dir')
        svnid = st.conf('svn', 'username')
        httpurl = st.conf('diff', 'http url')
        if svnid == "":
            svnid = "yanpeng.wang"
        self.result_url = "{}/{}/{}".format(httpurl.rstrip('/'), svnid, bugid)
        rmtdir = os.path.join(rmtdir, svnid, bugid).replace(os.sep, '/')

        sshargs = {
            'hostname': st.conf('diff', 'server'),
            'username': st.conf('diff', 'username'),
            'password': st.conf('diff', 'password'),
            'timeout' : 10,
            'compress': True,
            }
        self.worker.add_task(
                self._uploadDiffs(rmtdir, **sshargs),
                TaskHandler(self.uploadDiffsHandler)
                )


    def _uploadDiffs(self, dstdir, **sshargs):
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
            for f in os.listdir(hdiff_dir):
                if f.lower().endswith('.html'):
                    localfile = os.path.join(hdiff_dir, f)
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
            if sshcli: sshcli.close()
            (yield TaskOutput(u'EXIT %d' % code, OutputType.NOTIFY))


    @Slot(TaskOutput)
    def makeDiffHandler(self, msg):
        if not hasattr(self, 'fwReadyToUpload'):
            path = os.path.join(os.getcwdu(), hdiff_dir)
            path = path.replace(os.sep, '/')
            self.fwReadyToUpload = (
                u"Go to <a href='{}' style='color:dodgerblue;'>HDIFF Directory</a> "
                "to check the result.".format(path)
                )
        self.taskHandler(msg, u'Making diff files ... ',
                self.btnMakeDiff, self.fwReadyToUpload)


    @Slot(TaskOutput)
    def uploadDiffsHandler(self, msg):
        if not hasattr(self, 'fwUpload'):
            self.fwUpload = (
                u"Click <a href='{0}' style='color:dodgerblue;'>{0}</a> to review the result.".format(
                self.result_url)
                )
        self.taskHandler(msg, u'Uploading diff files ... ',
                self.btnMakeDiff, self.fwUpload)


    def deployNew(self):
        st = self.settings
        app = self.cboApp.itemText(self.cboApp.currentIndex())
        try:
            force_rmdir(approot_dir)
            force_rmdir(clstemp_dir)
            mkdir_p(approot_dir)
            mkdir_p(clstemp_dir)
        except Exception as ex:
            self.appendLog(TaskOutput(ex.message, OutputType.ERROR))
            return

        hostname = st.conf(app, 'server')
        sshargs = {}
        if hostname not in ('localhost', '127.0.0.1'):
            sshargs = {
                'hostname': hostname,
                'username': st.conf(app, 'username'),
                'password': decrypt(st.conf(app, 'password')),
                'timeout' : 10,
                'compress': True,
                }
        self.worker.add_task(
                self._deployNew(sshargs),
                TaskHandler(self.deployNewHandler)
                )

    def _copyfile(self, ssh, sftp, from_file, to_file, method='get', overwrite=True):
        if os.path.isdir(to_file):
            fname = os.path.basename(from_file)
            to_dir = to_file
            to_file = os.path.join(to_file, fname)
        else:
            to_dir = os.path.dirname(to_file)
        if not overwrite and os.path.exists(to_file):
            return
        if not os.path.exists(to_dir):
            mkdir_p(to_dir)

        if sftp:
            if method == 'put':
                sftp.put(from_file, to_file)
            else:
                sftp.get(from_file, to_file)
        else:
            shutil.copy(from_file, to_file)

    def _copyfiles(self, ssh, sftp, wildcard, to_dir, method='get', overwrite=True):
        if sftp:
            files = []
            dn = os.path.dirname(wildcard)
            bn = os.path.basename(wildcard)
            _, stdout, stderr = ssh.exec_command(
                    "find %s -maxdepth 1 -type f -name %s" % (dn, bn)
                    )
            files = stdout.read().split()
            errmsg = stderr.read()
            if errmsg: raise Exception(errmsg) 
        else:
            files = glob.glob(wildcard)
        mkdir_p(to_dir)
        for fn in files:
            self._copyfile(ssh, sftp, fn, to_dir, method, overwrite)

#
# data/backup/appname/
#    |_ other files 
#    |_ WEB-INF/classes/com/.../*.class
#    \_ WEB-INF/lib/*.jar
# data/approot  ----------- Stores all new stuff to be deployed
#    |_ other files 
#    |_ WEB-INF/classes/com/.../*.class
#    \_ WEB-INF/lib/*.jar
# data/clstemp  ----------- new classes to be put in jar
#    \_ com/.../*.class
#
    def _deployNew(self, sshargs):
        (yield TaskOutput(u'ENTER', OutputType.NOTIFY))
        st = self.settings
        app = self.cboApp.itemText(self.cboApp.currentIndex())
        sshcli = SSHClient()
        sftpcli = None
        tb = self.lstFiles
        code = 0

        try:
            if sshargs:
                if not (yield TaskOutput(u'Conntecting to %s ...' % sshargs['hostname'])):
                    raise CommandTerminated()
                sshcli.set_missing_host_key_policy(AutoAddPolicy())
                sshcli.connect(**sshargs)
                if not (yield TaskOutput(u'Connected!')):
                    raise CommandTerminated()
                sftpcli = sshcli.open_sftp()

            items = [ tb.item(i,3).text() for i in xrange(tb.rowCount())
                    if tb.item(i,0).checkState() == Qt.Checked ]
            clsitems = []  # items found in class dir or non-java-file
            jaritems = {}   # items found in jar file

            # === Fetch and backup files ====
            # backup class files, and copy them to approot dir
            if not (yield TaskOutput(u'Making backup ...')):
                raise CommandTerminated()
            srcroot = st.conf(app, 'source root')
            webappdir = st.conf(app, 'webapp dir')
            javadir = st.conf(app, 'java dir')
            clsdir = st.conf(app, 'class dir')
            tgroot = st.conf(app, 'target root')
            tgsep = tgroot[0]
            tgclsdir = st.conf(app, 'target class dir')
            appbakdir = os.path.join(backup_dir, app)
            for fn in items:
                if fn.endswith('.java'):
                    fn = fn.replace(javadir.replace(os.sep, '/'), '').lstrip('/')
                    _clsfn = fn[0:-5]+'.class'
                    clsfn = os.path.join(tgclsdir, _clsfn).replace(os.sep, tgsep)
                    tgt_f = os.path.join(tgroot, clsfn).replace(os.sep, tgsep)
                    bak_f = os.path.join(appbakdir, clsfn)
                    new_f = os.path.join(srcroot, clsdir, _clsfn)
                    tmp_f = os.path.join(approot_dir, clsfn)
                    clsitems.append(_clsfn)
                else:
                    fn = fn.replace(webappdir.replace(os.sep, '/'), '').lstrip('/')
                    tgt_f = os.path.join(tgroot, fn).replace(os.sep, tgsep)
                    bak_f = os.path.join(appbakdir, fn)
                    new_f = os.path.join(srcroot, webappdir, fn)
                    tmp_f = os.path.join(approot_dir, fn)
                try:
                    self._copyfile(sshcli, sftpcli, tgt_f, bak_f, overwrite=False)
                    self._copyfile(None, None, new_f, tmp_f)
                except IOError as ex:   # No file found
                    if ex.args[0] != 2:
                        raise ex

            # 1. backup jar files
            # 2. copy them to approot dir 
            # 3. will be updated with clstemp fileslater
            tgjarfile = st.conf(app, 'target jar file')
            jardir = os.path.dirname(tgjarfile)
            bakjardir = os.path.join(appbakdir, jardir)
            newjardir = os.path.join(approot_dir, jardir)
            self._copyfiles(sshcli, sftpcli,
                    os.path.join(tgroot, tgjarfile).replace(os.sep, tgsep),
                    bakjardir, overwrite=False)
            self._copyfiles(None, None,
                    os.path.join(appbakdir, tgjarfile),
                    newjardir)

            # copy new class files to temp dir, for updating jar file above
            for jar in os.listdir(newjardir):
                zf = zipfile.ZipFile(os.path.join(newjardir, jar))
                zflist = zf.namelist()
                jaritems[jar] = []
                for fn in clsitems:
                    if fn in zflist:
                        new_f = os.path.join(srcroot, clsdir, fn)
                        tmp_f = os.path.join(clstemp_dir, fn)
                        self._copyfile(None, None, new_f, tmp_f)
                        jaritems[jar].append(fn)    # clsss in which jarfile
            # copy new class files to temp dir, for updating jar file above
            # ==== Fetch and backup files ====

            # ==== Copy into approot_dir and update ====
            if not (yield TaskOutput(u'Copying new files and updating ...')):
                raise CommandTerminated()
            for jar, files  in jaritems.items():
                args = [ os.path.join(self.jar_bin), "-uf",
                        os.path.join("..", "..", newjardir, jar)
                       ]
                args += files
                self.worker.add_task(
                    CmdTask2(clstemp_dir, *args),
                    TaskHandler(self.taskHandler)
                    )
            # ==== Copy into approot_dir and update ====

            # ==== Replace or upload  files ====
            #if not (yield TaskOutput(u'Deploying new files to target ...')):
            #    raise CommandTerminated()
            # ==== Replace or upload  files ====

        except CommandTerminated:
            code = -2
            (yield TaskOutput(u'Uploading Terminited', OutputType.WARN))
        except Exception as ex:
            code = -1
            (yield TaskOutput(ex.message, OutputType.ERROR))
        finally:
            if sftpcli: sftpcli.close()
            if sshcli: sshcli.close()
            (yield TaskOutput(u'EXIT %d' % code, OutputType.NOTIFY))


    def _uploadTargetLocal(self, st, app):
        self.worker.add_task(
            CmdTask(*(st.conf(app, 'shutdown').split())),
            TaskHandler(self.uploadTargetHandler)
            )
        self.worker.add_task(
            self._copyToLocalTarget(st, app),
            TaskHandler(self.uploadTargetHandler)
            )
        self.worker.add_task(
            CmdTask(*(st.conf(app, 'startup').split())),
            TaskHandler(self.uploadTargetHandler)
            )


    def _uploadTarget(self, shutdown, startup, **sshargs):
        (yield TaskOutput(u'ENTER', OutputType.NOTIFY))
        sshcli = SSHClient()
        sftpcli = None
        code = 0
        try:
            if self.targetFile is None:
                raise Exception(u'None Target File')

            if not (yield TaskOutput(u'Conntecting to %s ...' % sshargs['hostname'])):
                raise CommandTerminated()
            sshcli.set_missing_host_key_policy(AutoAddPolicy())
            sshcli.connect(**sshargs)
            if not (yield TaskOutput(u'Connected, fetchting file ...')):
                raise CommandTerminated()

            sftpcli = sshcli.open_sftp()

            if shutdown:
                if not (yield TaskOutput(u'Stopping service ...' % fn)):
                    raise CommandTerminated()
                ret = sshcli.exec_command(shutdown)
                errstr = ret[2].read()
                if errstr != '':
                    raise Exception(errstr)

            if not (yield TaskOutput(u'Uploading target file ...' % fn)):
                raise CommandTerminated()
            sftpcli.put(target_file, self.targetFile)

            if startup:
                if not (yield TaskOutput(u'Starting service ...' % fn)):
                    raise CommandTerminated()
                ret = sshcli.exec_command(startup)
                errstr = ret[2].read()
                if errstr != '':
                    raise Exception(errstr)
        except CommandTerminated:
            code = -2
            (yield TaskOutput(u'TERMINITED: Target file not uploaded ... ', OutputType.WARN))
        except Exception as ex:
            code = -1
            (yield TaskOutput(ex.message, OutputType.ERROR))
        finally:
            if sftpcli: sftpcli.close()
            sshcli.close()
            (yield TaskOutput(u'EXIT %d' % code, OutputType.NOTIFY))

    def deployNewHandler(self, msg):
        if not hasattr(self, 'fwDevplyNew'):
            self.fwDeployNew = u"Dploied New Files ..."
        self.taskHandler(msg, u'Deploying Target File ... ',
                self.btnDeployNew, self.fwDeployNew)

    def uploadTargetHandler(self):
        if not hasattr(self, 'fwUploadTarget'):
            self.fwUploadTarget = u"Uploaded target file."
        self.taskHandler(msg, u'Uploading target file ... ',
                self.btnDeployNew, self.fwUploadTarget)


    @Slot(TaskOutput)
    def updateTargetHandler(self, msg):
        if not hasattr(self, 'fwUpdateTarget'):
            self.fwUpdateTarget = u"Updated target file."
        self.taskHandler(msg, u'Updating target file ... ',
                self.btnDeployNew, self.fwUpdateTarget)


    def closeEvent(self, event):
        #for i in xrange(self.tab.count()):
        #    self.tab.widget(i).close()
        self.worker.stop()
        event.accept()

 
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    win.center()
    sys.exit(app.exec_())

#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys, os
import glob
from PySide.QtCore import *
from PySide.QtGui import *
from paramiko import SSHClient, AutoAddPolicy
import zipfile
import shutil
import time

from yelib.qt.layout import *
from yelib.qt.widgets import *
from yelib.task import *
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
        self.txtSrv = QLineEdit()
        self.txtSrv.setReadOnly(True)
        self.txtSrcRoot = QLineEdit()
        self.txtSrcRoot.setReadOnly(True)
        self.txtSrcRoot.setMinimumWidth(350)
        self.txtTgRoot = QLineEdit()
        self.txtTgRoot.setReadOnly(True)
        self.txtTgRoot.setMinimumWidth(350)

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
            [
                yGridLayout([
                    [ 'App', self.cboApp ],
                    [ 'Server', self.txtSrv ],
                    ]),
                None,
                yGridLayout([
                  [ 'Source Root', self.txtSrcRoot ],
                  [ 'Target Root', self.txtTgRoot ],
                  ]),
            ],
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
        self.btnGetStatus = QPushButton(QIcon('image/refresh.png'), u'Get Status')
        self.btnGetStatus.setFixedSize(110, 28)
        self.btnMakeDiff = QPushButton(QIcon('image/game-chip.png'), u'Make Diff')
        self.btnMakeDiff.setFixedSize(110, 28)
        self.btnDeployNew = QPushButton(QIcon('image/organization.png'), u'Deploy New')
        self.btnDeployNew.setFixedSize(110, 28)
        self.chkBackup = QCheckBox('Backup')
        self.btnRestore = QPushButton(QIcon('image/undo.png'), u'Restore')
        self.btnRestore.setFixedSize(110, 28)
        # ==== Buttons ====

        # ==== Main Layout ====
        #self.btnExit = QPushButton(u'Exit')
        self.txtBugId = QLineEdit(self.settings.conf('diff', 'last bug'))
        self.txtBugId.setFixedWidth(100)
        lt = yBoxLayout([
            [ self.grpMain ],
            [ self.btnGetStatus, None,
              QLabel('BugId'), self.txtBugId, self.btnMakeDiff, None,
              self.btnDeployNew, self.chkBackup, self.btnRestore ],
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

    def echoMsg(self, msg):
        (yield TaskOutput(msg))

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
        st = self.settings
        self.txtSrv.setText(st.conf(sect, 'server'))
        self.txtSrcRoot.setText(st.conf(sect, 'source root'))
        self.txtTgRoot.setText(st.conf(sect, 'target root'))

    def updateAppList(self):
        st = self.settings
        applist = st.conf('app', 'list').split(',')
        self.cboApp.clear()
        for app in applist:
            self.cboApp.addItem(app.strip())
        if self.cboApp.count() > 0:
            self.selectApp(0)

    def defaultHandler(self, msg):
        if msg.type == OutputType.NOTIFY and msg.output.startswith('EXIT '):
            code = int(msg.output.split()[1])
            if code != 0:
                self.worker.stop_task()
        self.appendLog(msg)

    def getStatus(self):
        def begin():
            self.btnGetStatus.setDisabled(True)
            self.parent().showLoading(u'Getting svn status ... ', True)
            tb = self.lstFiles
            for i in xrange(tb.rowCount()):
                tb.removeRow(0)
        def end():
            self.parent().showLoading('', False)
            self.btnGetStatus.setDisabled(False)

        srcdir = self.txtSrcRoot.text()
        if srcdir == "":
            self.appendLog(TaskOutput(u'!!! Please set source root !!!', OutputType.WARN))
            return
        task = Task(CmdTask([os.path.join("bin", "svndiff"), "-c", "-s", srcdir]))
        task.init(
                TaskHandler(begin), TaskHandler(end),
                TaskHandler(self.getStatusHandler),
                TaskHandler(self.defaultHandler)
                )
        self.worker.add_task(task)

    def getStatusHandler(self, msg):
        if msg.type != OutputType.OUTPUT:
        	return
        tb = self.lstFiles
        m = msg.output.split()
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
        def begin():
            self.btnMakeDiff.setDisabled(True)
            self.parent().showLoading(u'Making diff files ... ', True)
        def end():
            self.parent().showLoading('', False)
            self.btnMakeDiff.setDisabled(False)
        if self.txtBugId.text() == "":
            self.appendLog(TaskOutput(u"!!! Please input Bug Id !!!", OutputType.WARN))
            return

        srcdir = self.txtSrcRoot.text()
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

        task = Task(CmdTask(cmds))
        task.init(
                TaskHandler(begin), TaskHandler(end),
                TaskHandler(self.defaultHandler)
                )

        path = os.path.join(os.getcwdu(), hdiff_dir).replace(os.sep, '/')
        task.put(self.echoMsg(
                u"Go to <a href='{}' style='color:dodgerblue;'>HDIFF Directory</a> "
                "to check the result.".format(path)
                ))

        st = self.settings
        bugid = self.txtBugId.text()
        rmtdir = st.conf('diff', 'remote dir')
        svnid = st.conf('svn', 'username')
        httpurl = st.conf('diff', 'http url')
        if svnid == "":
            svnid = "yanpeng.wang"
        result_url = "{}/{}/{}".format(httpurl.rstrip('/'), svnid, bugid)
        rmtdir = os.path.join(rmtdir, svnid, bugid).replace(os.sep, '/')

        sshargs = {
            'hostname': st.conf('diff', 'server'),
            'username': st.conf('diff', 'username'),
            'password': decrypt(st.conf('diff', 'password')),
            'timeout' : 10,
            'compress': True,
            }

        task.put(self._uploadDiffs(rmtdir, sshargs))
        task.put(self.echoMsg(
                u"Click <a href='{0}' style='color:dodgerblue;'>{0}</a> "
                u"to review the result.".format(result_url),
                ))

        self.worker.add_task(task)

    def _uploadDiffs(self, dstdir, sshargs):
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
            try:
                shutil.copy(from_file, to_file)
            except Exception as ex:
                raise ex

    def _copyfiles(self, ssh, sftp, wildcard, to_dir, method='get', overwrite=True):
        files = []
        if sftp:
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
        #for fn in files:
        #    self._copyfile(ssh, sftp, fn, to_dir, method, overwrite)
        if len(files) == 1:
            self._copyfile(ssh, sftp, files[0], to_dir, method, overwrite)


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
    def deployNew(self):
        st = self.settings
        app = self.cboApp.itemText(self.cboApp.currentIndex())
        sshcli = SSHClient()
        sftpcli = None

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

        def begin():
            self.btnDeployNew.setDisabled(True)
            self.parent().showLoading(u'Deploying Target File ... ', True)
            if sshargs:
                try:
                    self.appendLog(TaskOutput(u'Conntecting to %s ...' % sshargs['hostname']))
                    sshcli.set_missing_host_key_policy(AutoAddPolicy())
                    sshcli.connect(**sshargs)
                    self.appendLog(TaskOutput(u'Connected'))
                    sftpcli = sshcli.open_sftp()
                except Exception as ex:
                    self.appendLog(repr(ex), OutputType.ERROR)
        def end():
            if sftpcli: sftpcli.close()
            if sshcli: sshcli.close()
            self.parent().showLoading('', False)
            self.btnDeployNew.setDisabled(False)

        try:
            force_rmdir(approot_dir)
            force_rmdir(clstemp_dir)
            mkdir_p(approot_dir)
            mkdir_p(clstemp_dir)
        except Exception as ex:
            self.appendLog(TaskOutput(ex.message, OutputType.ERROR))
            return

        task = Task(self._deployNew(st, app, sshcli, sftpcli))
        task.init(
                TaskHandler(begin), TaskHandler(end),
                TaskHandler(self.defaultHandler),
                )
        self.worker.add_task(task)

#    def deployNewHandler(self, msg):
#        if msg.type == OutputType.NOTIFY and msg.output.startswith('EXIT '):
#            code = int(msg.output.split()[1])
#            if code == 0:
#                self.worker.


    # Fetch and backup files
    def _deployNew(self, st, app, sshcli, sftpcli):
        tb = self.lstFiles
        code = 0
        srcroot = st.conf(app, 'source root')
        webappdir = st.conf(app, 'webapp dir')
        javadir = st.conf(app, 'java dir')
        clsdir = st.conf(app, 'class dir')
        tgroot = st.conf(app, 'target root')
        tgsep = '/'
        tgclsdir = st.conf(app, 'target class dir')
        appbakdir = os.path.join(backup_dir, app)
        clsitems = []  # items found in class dir or non-java-file
        jaritems = {}   # items found in jar file

        try:
            items = [ tb.item(i,3).text() for i in xrange(tb.rowCount())
                    if tb.item(i,0).checkState() == Qt.Checked ]

            # === Fetch and backup files ====
            # backup class files, and copy them to approot dir
            if not (yield TaskOutput(u'Fetching, making backup and copying files ... ')):
                raise CommandTerminated()
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
                if not (yield TaskOutput(u'Copying files ... ')):
                    raise CommandTerminated()
            self.worker.add_step(self._updateNew(st, app, sshcli, sftpcli, clsitems))
        except CommandTerminated:
            code = -2
            (yield TaskOutput(u'Fetching Terminited', OutputType.WARN))
        except Exception as ex:
            code = -1
            (yield TaskOutput(repr(ex), OutputType.ERROR))
        finally:
            (yield TaskOutput(u'EXIT %d' % code, OutputType.NOTIFY))

    def _updateNew(self, st, app, sshcli, sftpcli, clsitems):
        # 1. backup jar files
        # 2. copy them to approot dir 
        # 3. will be updated with clstemp fileslater
        code = 0
        srcroot = st.conf(app, 'source root')
        clsdir = st.conf(app, 'class dir')
        tgroot = st.conf(app, 'target root')
        appbakdir = os.path.join(backup_dir, app)
        tgjarfile = st.conf(app, 'target jar file')
        jardir = os.path.dirname(tgjarfile)
        bakjardir = os.path.join(appbakdir, jardir)
        newjardir = os.path.join(approot_dir, jardir)
        tgsep = '/'
        jaritems = {}

        try:
            self._copyfiles(sshcli, sftpcli,
                    os.path.join(tgroot, tgjarfile).replace(os.sep, tgsep),
                    bakjardir, overwrite=False)
            self._copyfiles(None, None,
                    os.path.join(appbakdir, tgjarfile),
                    newjardir)

            if not (yield TaskOutput(u'Copying new class files ... ')):
                raise CommandTerminated()
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
                        (yield TaskOutput((jar, fn), OutputType.OUTPUT))

            if not (yield TaskOutput(u'Updating target files ... ')):
                raise CommandTerminated()
            for jar, files in jaritems.items():
                if len(files) == 0:
                    continue
                args = [ os.path.join(self.jar_bin), "-uf",
                        os.path.join("..", "..", newjardir, jar)
                       ] + files
                self.worker.add_step(CmdTask(args, clstemp_dir))
            self.worker.add_step(self._uploadNew(st, app, sshcli, sftpcli))
        except CommandTerminated:
            code = -2
            (yield TaskOutput(u'Updating Terminited', OutputType.WARN))
        except Exception as ex:
            code = -1
            (yield TaskOutput(repr(ex), OutputType.ERROR))
        finally:
            (yield TaskOutput(u'EXIT %d' % code, OutputType.NOTIFY))


    def _uploadNew(self, st, app, sshcli, sftpcli):
        tgroot = st.conf(app, 'target root')
        tgsep = '/'
        code = 0
        try:
            for r,_,files in os.walk(approot_dir):
                for f in files:
                    srcfile = os.path.join(r, f)
                    tgfile = os.path.join(tgroot, r.replace(approot_dir+os.sep, ''),
                            f).replace(os.sep, tgsep)
                    if not (yield TaskOutput(u'Uploading %s ... ' % srcfile)):
                        raise CommandTerminated()
                    self._copyfile(sshcli, sftpcli, srcfile, tgfile, method='put')
            (yield TaskOutput(u'Files Uploaded'))
        except CommandTerminated:
            code = -2
            (yield TaskOutput(u'Uploading Terminited', OutputType.WARN))
        except Exception as ex:
            code = -1
            (yield TaskOutput(repr(ex), OutputType.ERROR))
        finally:
            (yield TaskOutput(u'EXIT %d' % code, OutputType.NOTIFY))


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

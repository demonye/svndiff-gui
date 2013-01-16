#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys, os
import glob
from PySide.QtCore import *
from PySide.QtGui import *
from paramiko import SSHClient, AutoAddPolicy
import shutil

from yelib.qt.layout import *
from yelib.qt.widgets import *
from yelib.newtask import *
from yelib.util import *

from SettingsDlg import decrypt


hdiff_dir = os.path.join("data", "hdiff")
backup_dir = os.path.join("data", "backup")
classes_dir = os.path.join("data", "classes")
target_dir = os.path.join("data", "target")
target_file = os.path.join(target_dir, "target.jar")

class MainArea(QWidget):

    def __init__(self, parent=None):
        super(MainArea, self).__init__(parent)

        self.settings = parent.dlgSettings
        self.java_home = self.settings.conf('app', 'java home')

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
        self.btnDeployCls = QPushButton(QIcon('image/deployclass1.png'), u'Deploy Class')
        self.btnDeployCls.setFixedSize(120, 30)
        # ==== Buttons ====

        # ==== Main Layout ====
        #self.btnExit = QPushButton(u'Exit')
        self.txtBugId = QLineEdit(self.settings.conf('diff', 'last bug'))
        self.txtBugId.setFixedWidth(100)
        lt = yBoxLayout([
            [ self.grpMain ],
            [ self.btnGetStatus, None,
              QLabel('Bug Id'), self.txtBugId, self.btnMakeDiff, None,
              self.btnDeployCls ],
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
        self.btnDeployCls.clicked.connect(self.deployCls)
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
            sshcli.close()
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


    def deployCls(self):
        st = self.settings
        app = self.cboApp.itemText(self.cboApp.currentIndex())
        try:
            force_rmdir(classes_dir)
            mkdir_p(classes_dir)
        except Exception as ex:
            self.appendLog(TaskOutput(ex.message, OutputType.ERROR))
            return

        # ==== Copy files to classes dir ====
        tb = self.lstFiles
        for i in xrange(tb.rowCount()):
            item = tb.item(i, 0)
            if item.checkState() != Qt.Checked:
                continue
            srcfile = tb.item(i, 4).text()
            dstfile = tb.item(i, 3).text().replace('/', os.sep)
            prename, ext = os.path.splitext(os.path.basename(dstfile))
            if ext.lower() != '.java':
                continue

            javadir = st.conf(app, 'java dir')
            clsdir = st.conf(app, 'class dir')
            dstdir = os.path.dirname(srcfile.replace(javadir, '')).strip(os.sep)
            clsfile = os.path.join(clsdir, dstdir, prename+".class")
            if os.path.exists(clsfile):
                dstdir = os.path.join(classes_dir, dstdir)
                mkdir_p(dstdir)
                try:
                    shutil.copy(clsfile, dstdir)
                except Exception as ex:
                    self.appendLog(TaskOutput(ex.message, OutputType.ERROR))
                    return
            else:
                self.appendLog(
                    TaskOutput('Class file does not exist: {}'.format(clsfile),
                    OutputType.ERROR)
                    )
                return
        # ==== Copy files to classes dir ====


        tgfile = st.conf(app, 'target file')
        hostname = st.conf(app, 'server')
        sshargs = {
            'hostname': hostname,
            'username': st.conf(app, 'username'),
            'password': decrypt(st.conf(app, 'password')),
            'timeout' : 10,
            'compress': True,
            }
        if tgfile.lower().endswith('.jar'):
            if hostname in ('localhost', '127.0.0.1'):
                files = glob.glob(tgfile)
                if len(files) != 1:
                    self.appendLog(
                        TaskOutput("Found %d file(s): %s" % (len(files), tgfile),
                        OutputType.ERROR)
                        )
                    return
                self.targetFile = files[0]
                tgbsname = os.path.basename(self.targetFile)
                tgbkname = os.path.join(backup_dir, tgbsname)
                try:
                    if not os.path.exists(tgbkname):
                        shutil.copy(self.targetFile, backup_dir)
                    shutil.copy(tgbkname, target_file)
                except Exception as ex:
                    self.appendLog(TaskOutput(ex.message, OutputType.ERROR))
                    return
            else:
                # ==== Fetch File ====
                self.worker.add_task(
                        self._fetchTarget(
                            st.conf(app, 'target file'),
                            **sshargs ),
                        TaskHandler(self.fetchTargetHandler)
                        )
                # ==== Fetch File ====

            # ==== Update File ====
            self.worker.add_task(
                CmdTask2(
                    classes_dir,
                    os.path.join(self.java_home, "bin", "jar"),
                    "-uf", os.path.join("..", "target", "target.jar"), "*"
                    ), 
                TaskHandler(self.updateTargetHandler)
                )
            # ==== Update File ====
        elif tgfile.tolower().endswith('.class'):
            pass
        else:
            self.appendLog(
                TaskOutput('Cannot deal with target file: %s' % tgfile,
                OutputType.ERROR)
                )
            return


        # ==== Upload File ====
        #self.worker.add_task(
        #        self._uploadTarget(
        #            st.conf(app, 'startup'),
        #            st.conf(app, 'shutdown'),
        #            **sshargs ),
        #        TaskHandler(self.uploadTargetHandler)
        #        )
        # ==== Upload File ====

    def _uploadTargetLocal(self, startup=None, shutdown=None):
        os.system(shutdown)
        shutil.copy(target_file, self.targetFile)
        os.shutdown(startup)

    def _fetchTarget(self, target, **sshargs):
        (yield TaskOutput(u'ENTER', OutputType.NOTIFY))
        sshcli = SSHClient()
        sftpcli = None
        code = 0
        try:
            mkdir_p(target_dir)
            if not (yield TaskOutput(u'Conntecting to %s ...' % sshargs['hostname'])):
                raise CommandTerminated()
            sshcli.set_missing_host_key_policy(AutoAddPolicy())
            sshcli.connect(**sshargs)
            if not (yield TaskOutput(u'Connected, fetchting file ...')):
                raise CommandTerminated()
            ret = sshcli.exec_command("""
            target="{}"
            n=$(ls -1 $target 2>&- |wc -l)
            if [ $n -ne 1 ]; then
                echo "Found $n file(s), please check your settings!" 1>&2
            else
                fn=$(ls -1 $target)
                [ ! -f $fn.bak ] && cp $fn $fn.bak
                echo $fn
            fi
            """.format(target) )
            errstr = ret[2].read()
            if errstr != '':
                raise Exception(errstr)
            sftpcli = sshcli.open_sftp()
            fn =  ret[1].readlines()[0].rstrip()
            #local_fn = os.path.basename(fn)
            if not (yield TaskOutput(u'Fetchting %s.bak ...' % fn)):
                raise CommandTerminated()
            sftpcli.get(fn+".bak", target_file)
            (yield TaskOutput(fn, OutputType.OUTPUT))
        except CommandTerminated:
            code = -2
            (yield TaskOutput(u'TERMINITED: Fetching Target File ...', OutputType.WARN))
        except Exception as ex:
            code = -1
            print ex
            (yield TaskOutput(ex.message, OutputType.ERROR))
        finally:
            if sftpcli: sftpcli.close()
            sshcli.close()
            (yield TaskOutput(u'EXIT %d' % code, OutputType.NOTIFY))


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
            print ex
            (yield TaskOutput(ex.message, OutputType.ERROR))
        finally:
            if sftpcli: sftpcli.close()
            sshcli.close()
            (yield TaskOutput(u'EXIT %d' % code, OutputType.NOTIFY))

    def _uploadTargetHandler(self):
        if not hasattr(self, 'fwUploadTarget'):
            self.fwUploadTarget = u"Uploaded target file."
        self.taskHandler(msg, u'Uploading target file ... ',
                self.btnDeployCls, self.fwUploadTarget)

    @Slot(TaskOutput)
    def fetchTargetHandler(self, msg):
        if not hasattr(self, 'fwFetchTarget'):
            self.fwFetchTarget = u"Fetched target file."
        ret = self.taskHandler(msg, u'Fetching target file ... ',
                self.btnDeployCls, self.fwFetchTarget)
        if ret is not None:
            self.targetFile = ret


    @Slot(TaskOutput)
    def updateTargetHandler(self, msg):
        if not hasattr(self, 'fwUpdateTarget'):
            self.fwUpdateTarget = u"Updated target file."
        self.taskHandler(msg, u'Updating target file ... ',
                self.btnDeployCls, self.fwUpdateTarget)


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

#!/usr/bin/env python2
# -* coding: utf-8 -*-

import os
import time
from PySide.QtCore import *
from PySide.QtGui import *
from yelib.qt.layout import *
from yelib.newtask import *
from paramiko import SSHClient, AutoAddPolicy
from tabs.BaseTab import BaseTab

mtime_fmt = "%m/%d %H:%M"

class ClassTab(BaseTab):

    def __init__(self, parent=None):
        super(ClassTab, self).__init__(parent)

        self.local_bakdir = "data/backup"
        self.grpSource = self.createSourceGroup()
        self.grpTarget = self.createTargetGroup()

        self.lt = yBoxLayout([
            [ self.grpSource ],
            [ self.grpTarget ],
        ])
        self.setLayout(self.lt)
        self.setStyleSheet(
                'QTableWidget {border:1px solid gray;}'
                )
        self.worker = TaskWorker()

    # ==== Source Group ====
    def createSourceGroup(self):
        grp = QGroupBox(u'Source')
        self.txtSrcDir = QLineEdit()
        self.btnSrcDir = QPushButton(' / ')
        self.btnSrcDir.setFixedWidth(20)
        self.btnSrcDir.clicked.connect(self.selectSrcDir)

        self.txtClsFile = QLineEdit()
        self.btnClsFile = QPushButton(' / ')
        self.btnClsFile.setFixedWidth(20)
        self.btnClsFile.clicked.connect(self.selectClsFile)

        self.btnFindNew = QPushButton('Find Class\nChanged in')
        self.btnFindNew.clicked.connect(self.findNewClass)
        self.btnFindNew.setFixedWidth(100)
        self.txtNewInMins = QLineEdit()
        self.txtNewInMins.setFixedWidth(40)

        self.btnAddFile = QPushButton('Add')
        self.btnAddFile.setFixedWidth(100)
        self.btnAddFile.clicked.connect(self.addClassFile)
        self.btnRemoveFiles = QPushButton('Remove')
        self.btnRemoveFiles.setFixedWidth(100)
        self.btnRemoveFiles.clicked.connect(self.removeClassFiles)

        tb = QTableWidget()
        tb.setColumnCount(4)
        tb.setSelectionBehavior(QAbstractItemView.SelectRows)
        tb.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tb.setHorizontalHeaderLabels(("", "Class File", "Time", "File In Jar"))
        tb.horizontalHeader().setResizeMode(0, QHeaderView.Fixed)
        tb.horizontalHeader().setResizeMode(1, QHeaderView.Interactive)
        tb.horizontalHeader().setResizeMode(2, QHeaderView.ResizeToContents)
        tb.horizontalHeader().setResizeMode(3, QHeaderView.Interactive)
        tb.horizontalHeader().resizeSection(0, 30) 
        #tb.setColumnHidden(4, True)
        #tb.horizontalHeader().hide()
        tb.verticalHeader().hide()
        tb.setAlternatingRowColors(True)
        tb.setMinimumHeight(100)
        self.tbSource = tb
        wtMin = QWidget()
        ltMin = yBoxLayout([
            [ QLabel('in'), self.txtNewInMins, QLabel(u'mins') ],
        ])
        wtMin.setLayout(ltMin)
        wtMin.setFixedWidth(100)
        lt = yGridLayout([
            [ QLabel('Select Source Dir'), self.txtSrcDir, self.btnSrcDir,
              self.btnFindNew, wtMin ],
            [ QLabel('Select Class File'), self.txtClsFile,
              self.btnClsFile, self.btnAddFile, self.btnRemoveFiles ],
            [ (self.tbSource, 1, 5) ] + [None]*4,
        ])
        grp.setLayout(lt)

        return grp

    # ==== Target ====
    def createTargetGroup(self):
        grp = QGroupBox('Target')
        self.cboAppType = QComboBox()
        self.cboAppType.activated.connect(self.getJarInfo)
        self.txtAppSrv = QLineEdit()
        self.txtSrvUser = QLineEdit()
        self.txtSrvPwd = QLineEdit()
        self.txtSrvPwd.setEchoMode(QLineEdit.Password)

        #tb = QTableWidget()
        #tb.setColumnCount(4)
        ##tb.setSelectionBehavior(QAbstractItemView.SelectRows)
        #tb.setEditTriggers(QAbstractItemView.NoEditTriggers)
        #tb.setHorizontalHeaderLabels(("", "Prefix", "File", "Path"))
        #tb.horizontalHeader().setResizeMode(0, QHeaderView.Fixed)
        #tb.horizontalHeader().setResizeMode(2, QHeaderView.ResizeToContents)
        ##tb.horizontalHeader().setResizeMode(3, QHeaderView.ResizeToContents)
        #tb.horizontalHeader().setResizeMode(3, QHeaderView.Interactive)
        #tb.setColumnHidden(1, True)
        ##tb.horizontalHeader().hide()
        #tb.verticalHeader().hide()
        ##tb.setFixedHeight(70)
        #tb.setColumnWidth(0, 30)
        ##tb.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        ##tb.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        #self.tbJarInfo = tbtbJarInfo

        self.lbFilePrefix = QLabel()
        self.lbRemotePath = QLabel()
        self.lbFetchedFile = QLabel()
        ltJarInfo = yGridLayout([
            [ QLabel('File Prefix'), self.lbFilePrefix ],
            [ QLabel('Remote Path'), self.lbRemotePath ],
            [ QLabel('Fetched File'), self.lbFetchedFile ],
        ])
        ltJarInfo.setColumnStretch(1, 10)
        wtJarInfo = QWidget()
        wtJarInfo.setLayout(ltJarInfo)
        wtJarInfo.setStyleSheet('QLabel {padding:3px;background:lightyellow;border-radius:2px}')


        self.btnFetchJar = QPushButton('Fetch Jarfile')
        self.btnFetchJar.clicked.connect(self.fetchJarFile)
        self.btnMatchInJar = QPushButton('Match Class in Jar')
        self.btnMatchInJar.clicked.connect(self.matchInJar)
        self.btnUpdateJar = QPushButton('Update Jarfile')
        self.btnUpdateJar.clicked.connect(self.updateJar)
        self.btnRestore = QPushButton('Restore Jarfile')
        self.btnRestore.setDisabled(True)
        ltSrvInfo = yGridLayout([
            [ QLabel(u'App Type'), self.cboAppType,
              QLabel(u'Hostname'), self.txtAppSrv ],
            [ QLabel(u'Username'), self.txtSrvUser,
              QLabel(u'Password'), self.txtSrvPwd ],
        ])
        ltGrid = yBoxLayout([
            [ ltSrvInfo ],
            #[ self.tbJarInfo ],
            [ wtJarInfo ],
        ])
        ltBtn = yBoxLayout([
            None,
            [ self.btnFetchJar ],
            [ self.btnMatchInJar ],
            [ self.btnUpdateJar ],
            [ self.btnRestore ],
            None,
        ])
        lt = yBoxLayout([
            [ ltGrid, ltBtn ]
        ])
        grp.setLayout(lt)

        return grp


    def fetchJarFile(self):
        sshargs = {
            'hostname': self.txtAppSrv.text(),
            'username': self.txtSrvUser.text(),
            'password': self.txtSrvPwd.text(),
            'timeout' : 10,
            'compress': True,
            }

        appdata = self.cboAppType.itemData(self.cboAppType.currentIndex())
        if appdata['local'] == 'yes':
            self.appendLog(TaskOutput(u"TODO: Local Server"))
            return

        self.worker.add_task(
                self._fetchJarFile(
                    appdata['prefix'], appdata['suffix'], appdata['path'],
                    **sshargs ),
                TaskHandler(self.fetchJarFileHandler)
                )

    def _fetchJarFile(self, prefix, suffix, dstdir, **sshargs):
        (yield TaskOutput(u'ENTER', OutputType.NOTIFY))
        sshcli = SSHClient()
        sftpcli = None
        code = 0
        try:
            if os.path.exists(self.local_bakdir):
                if not os.path.isdir(self.local_bakdir):
                	raise Exception("File %s exists" % self.lcoal_bakdir)
            else:
                os.makedirs(self.lcoal_bakdir)

            if not (yield TaskOutput(u'Conntecting to %s ...' % sshargs['hostname'])):
                raise CommandTerminated()
            sshcli.set_missing_host_key_policy(AutoAddPolicy())
            sshcli.connect(**sshargs)
            if not (yield TaskOutput(u'Connected, fetchting file ...')):
                raise CommandTerminated()
            ret = sshcli.exec_command("cd {}; ls -1 {}*.{}".format(dstdir, prefix, suffix))
            errstr = ret[2].read()
            if errstr != '':
                raise Exception(errstr)
            sftpcli = sshcli.open_sftp()
            filenum = 0
            for l in ret[1].readlines():
                f = l.rstrip()
                remotefile = os.path.join(dstdir, f).replace(os.sep, '/')
                if not (yield TaskOutput(u'Fetchting %s ...' % f)):
                    raise CommandTerminated()
                sftpcli.get(remotefile, os.path.join(self.local_bakdir, f))
                filenum += 1
            if filenum > 1:
            	raise Exception(u'Found %d files, please check your settings' % filenum)
        except CommandTerminated:
            code = -2
            (yield TaskOutput(u'Fetching Terminited', OutputType.WARN))
            try: p.terminate()
            except: pass
            p.wait()
        except Exception as ex:
            code = -1
            (yield TaskOutput(ex.message, OutputType.ERROR))
        finally:
            if sftpcli: sftpcli.close()
            sshcli.close()
            (yield TaskOutput(u'EXIT %d' % code, OutputType.NOTIFY))


    @Slot(TaskOutput)
    def fetchJarFileHandler(self, msg):
        if msg.type == OutputType.NOTIFY:
            if msg.output == u'ENTER':
                self.btnFetchJar.setDisabled(True)
                self.showLoading(u'Fetching file ... ', True)
            elif msg.output.startswith('EXIT '):
                code = int(msg.output.split()[1])
                if code == 0:
                    data_dir = os.path.join(os.getcwdu(),
                            self.local_bakdir).replace(os.sep, '/')
                    self.appendLog(TaskOutput(
                        u"Go to <a href='{}'>Data Directory</a> "
                        "to check fie.".format(data_dir))
                        )
                self.showLoading('', False)
                self.btnFetchJar.setDisabled(False)
            return
        self.appendLog(msg)


    def matchInJar(self):
        pass

    def updateJar(self):
        pass

    def getJarInfo(self):
        appdata = self.cboAppType.itemData(self.cboAppType.currentIndex())
        pfx = appdata['prefix']
        sfx = appdata['suffix']
        pth = appdata['path']
        self.lbFilePrefix.setText("{}*.{}".format(pfx, sfx))
        self.lbRemotePath.setText(pth)
        files = []
        if not os.path.isdir(self.local_bakdir):
            return
        for fn in os.listdir(self.local_bakdir):
            if fn.startswith(pfx) and fn.endswith(sfx):
                files.append(fn)
        if len(files) == 1:
            self.lbFetchedFile.setText(files[0])
        else:
            self.lbFetchedFile.setText('')


    def selectSrcDir(self):
        srcdir = self.txtSrcDir
        dirname = QFileDialog.getExistingDirectory(
                self, u'Select Source Directory', srcdir.text())
        if len(dirname) > 0:
            srcdir.setText(dirname)

    def selectClsFile(self):
        clsfile = self.txtClsFile
        fname = QFileDialog.getOpenFileName(
                self, u'Select Java Class', clsfile.text(), "Java Class File (*.class)")
        self.txtClsFile.setText(fname[0])

    def addClassFile(self):
        fname = self.txtClsFile.text()
        try:
            mt = os.path.getmtime(fname)
        except Exception as ex:
            self.appendLog(TaskOutput(unicode(ex), OutputType.ERROR))
            return
        self._addClassFile(fname, mt)

    def _addClassFile(self, fname, mt):
        mtime = time.strftime(mtime_fmt, time.localtime(mt))
        n = self.tbSource.rowCount()
        self.tbSource.insertRow(n)
        chk = QTableWidgetItem()
        chk.setCheckState(Qt.Checked)
        self.tbSource.setItem(n, 0, chk)
        self.tbSource.setItem(n, 1, QTableWidgetItem(fname))
        self.tbSource.setItem(n, 2, QTableWidgetItem(mtime))
        self.tbSource.resizeColumnToContents(1)

    def removeClassFiles(self):
        n = self.tbSource.rowCount()

        for row in xrange(n-1, -1, -1):
            if self.tbSource.item(row, 0).checkState() == Qt.Unchecked:
                continue
            self.tbSource.removeRow(row)

    def stopTask(self):
        return False

    def findNewClass(self):
        mins = self.txtNewInMins.text()
        for i in xrange(self.tbSource.rowCount()):
            self.tbSource.removeRow(0)

        self.btnSearch.hide()
        self.btnStopSrch.show()
        self.showLoading(u'Searching class files newer than {} mins'.format(mins), True)

        srcdir = self.txtSrcDir.text()
        self.worker.add_task(
                self._findNewClass(srcdir),
                TaskHandler(self.findNewClassHandler)
                )

    def _findNewClass(self, srcdir):
        curtime = time.time()
        found = 0
        code = 0
        try:
            (yield TaskOutput(u'Start searching ...'))
            for root,dirs,files in os.walk(srcdir):
                for f in files:
                    running = (yield TaskOutput(u'Detect running', OutputType.NOTIFY))
                    if not running:
                        raise CommandTerminated()
                    fname = os.path.join(root, f)
                    ext = os.path.splitext(f)[1]
                    if ext.lower() != ".class":
                        continue
                    mt = os.path.getmtime(fname)
                    secs = int(self.txtNewInMins.text()) * 60
                    if curtime - mt <= secs:
                        (yield TaskOutput(('ADDFILE', fname, mt), OutputType.NOTIFY))
                        found += 1
            (yield TaskOutput(u'Found %s files.' % found))
        except CommandTerminated:
            (yield TaskOutput(u'TERMINITED: %s' % args[0], OutputType.WARN))
            try: p.terminate()
            except: pass
            p.wait()
        except Exception as ex:
            code = -1
            (yield TaskOutput(ex.message, OutputType.ERROR))
        finally:
            (yield TaskOutput(u'EXIT %d' % code, OutputType.NOTIFY))

    @Slot(TaskOutput)
    def findNewClassHandler(self, msg):
        if msg.type == OutputType.NOTIFY:
            output = msg.output
            if type(output) == tuple and output[0] == 'ADDFILE':
                self._addClassFile(output[1], output[2])
            elif output.startswith('EXIT '):
                self.showLoading('', False)
                self.btnStopSrch.hide()
                self.btnSearch.show()
        else:
            self.appendLog(msg)


    def closeEvent(self, event):
        self.worker.stop()
        event.accept()


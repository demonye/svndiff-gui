#!/usr/bin/env python2
# -* coding: utf-8 -*-

import os
import time
import zipfile
from PySide.QtCore import *
from PySide.QtGui import *
from yelib.qt.layout import *
from yelib.newtask import *
from paramiko import SSHClient, AutoAddPolicy
from tabs.BaseTab import *

mtime_fmt = "%m/%d %H:%M"

class ClassTab(BaseTab):

    def __init__(self, parent=None):
        super(ClassTab, self).__init__(parent)

        self.local_bakdir = "data/backup"
        self.grpSource = self.createSourceGroup()
        self.grpTarget = self.createTargetGroup()
        self.grpTarget.setSizePolicy(
            QSizePolicy.Policy(QSizePolicy.Preferred),
            QSizePolicy.Policy(QSizePolicy.Fixed)
            )

        self.lt = yBoxLayout([
            [ self.grpSource ],
            [ self.grpTarget ],
        ])
        self.setLayout(self.lt)
        self.worker = TaskWorker()

    def init(self):
        self.getJarInfo()

    # ==== Source Group ====
    def createSourceGroup(self):
        grp = QGroupBox(u'Source')
        self.txtSrcDir = SelectFile(
                u'Class Path', u'Select Class File Direcory', type="dir",
                )
        self.txtClsFile = SelectFile(
                u'Class File', u'Select Class File',
                filter="Java Class File (*.class)",
                )

        self.btnFindNew = QPushButton('Find New Class In')
        self.btnFindNew.clicked.connect(self.findNewClass)
        self.btnFindNew.setFixedWidth(120)
        self.txtNewInMins = QLineEdit()
        self.txtNewInMins.setFixedWidth(40)

        self.btnAddFile = QPushButton('Add')
        self.btnAddFile.clicked.connect(self.addClassFile)
        self.btnRemoveFiles = QPushButton('Remove')
        self.btnRemoveFiles.clicked.connect(self.removeClassFiles)

        tb = QTableWidget()
        tb.setColumnCount(4)
        tb.setSelectionBehavior(QAbstractItemView.SelectRows)
        tb.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tb.setHorizontalHeaderLabels(("", "", "Class File", "Modified Time"))
        tb.horizontalHeader().setResizeMode(0, QHeaderView.Fixed)
        tb.horizontalHeader().setResizeMode(1, QHeaderView.Fixed)
        tb.horizontalHeader().setResizeMode(2, QHeaderView.Interactive)
        tb.horizontalHeader().setResizeMode(3, QHeaderView.ResizeToContents)
        tb.horizontalHeader().resizeSection(0, 25) 
        tb.horizontalHeader().resizeSection(1, 25) 
        #tb.setColumnHidden(4, True)
        #tb.horizontalHeader().hide()
        #tb.verticalHeader().hide()
        tb.setAlternatingRowColors(True)
        self.tbSource = tb
        lt = yGridLayout([
            [ self.txtSrcDir, self.btnFindNew, self.txtNewInMins, QLabel('mins') ],
            [ self.txtClsFile, (yBoxLayout([ [self.btnAddFile, self.btnRemoveFiles] ]),1,3) ],
            [ (self.tbSource,1,4) ],
        ])
        grp.setLayout(lt)
        return grp

    # ==== Target ====
    def createTargetGroup(self):

        # ==== Server Info ====
        grp = QGroupBox('Target')
        self.cboAppType = QComboBox()
        self.cboAppType.activated.connect(self.getJarInfo)
        self.txtAppSrv = QLineEdit()
        self.txtSrvUser = QLineEdit()
        self.txtSrvPwd = QLineEdit()
        self.txtSrvPwd.setEchoMode(QLineEdit.Password)
        ltSrvInfo = yGridLayout([
            [ QLabel(u'App Type'), self.cboAppType ],
            [ QLabel(u'Hostname'), self.txtAppSrv ],
            [ QLabel(u'Username'), self.txtSrvUser ],
            [ QLabel(u'Password'), self.txtSrvPwd ],
        ])
        # ==== Server Info ====

        # ==== Target File ====
        grpJarInfo = QGroupBox('Target File')
        self.txtFilePatt = QLineEdit()
        self.txtFilePatt.setReadOnly(True)
        self.txtFilePatt.setFixedWidth(130)
        self.txtRemotePath = QLineEdit()
        self.txtRemotePath.setReadOnly(True)
        self.cboFetchedFile = QComboBox()
        ltJarInfo = yGridLayout([
            [ QLabel('File Pattern'), self.txtFilePatt,
              QLabel('Fetched File'), self.cboFetchedFile ],
            [ QLabel('Remote Path'), (self.txtRemotePath,1,3) ],
        ])
        ltJarInfo.setColumnStretch(1, 10)
        grpJarInfo.setLayout(ltJarInfo)
        # ==== Target File ====

        # ==== Buttons ====
        self.btnFetchJar = QPushButton('Fetch Jarfile')
        self.btnFetchJar.clicked.connect(self.fetchJarFile)
        #self.btnMatchInJar = QPushButton('Match Class in Jar')
        #self.btnMatchInJar.clicked.connect(self.matchInJar)
        self.btnUpdateJar = QPushButton('Update Jarfile')
        self.btnUpdateJar.clicked.connect(self.updateJar)
        self.btnRestore = QPushButton('Restore Jarfile')
        self.btnRestore.setDisabled(True)
        ltBtn = yBoxLayout([
            [ None, self.btnFetchJar, self.btnUpdateJar, self.btnRestore, ],
        ])
        # ==== Buttons ====

        ltGrid = yBoxLayout([
            [ grpJarInfo ],
            [ ltBtn ],
        ])
        lt = yBoxLayout([
            [ ltSrvInfo, ltGrid ]
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
                    raise Exception("File %s exists" % self.local_bakdir)
            else:
                os.makedirs(self.local_bakdir)

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
            self.cboFetchedFile.clear()
            for l in ret[1].readlines():
                f = l.rstrip()
                remotefile = os.path.join(dstdir, f).replace(os.sep, '/')
                if not (yield TaskOutput(u'Fetchting %s ...' % f)):
                    raise CommandTerminated()
                sftpcli.get(remotefile, os.path.join(self.local_bakdir, f))
                filenum += 1
                self.cboFetchedFile.addItem(f)
            if filenum > 1:
                (yield TaskOutput(
                    u'Found %d files, please check your settings' % filenum,
                    OutputType.WARN))
        except CommandTerminated:
            code = -2
            (yield TaskOutput(u'Fetching Terminited', OutputType.WARN))
        except Exception as ex:
            code = -1
            (yield TaskOutput(ex.message, OutputType.ERROR))
        finally:
            if sftpcli: sftpcli.close()
            sshcli.close()
            (yield TaskOutput(u'EXIT %d' % code, OutputType.NOTIFY))


    @Slot(TaskOutput)
    def fetchJarFileHandler(self, msg):
        if not hasattr(self, 'fwFetchJarFile'):
            data_dir = os.path.join(os.getcwdu(),
                    self.local_bakdir).replace(os.sep, '/')
            self.fwFetchJarFile = (
                    u"Go to <a href='{}'>Data Directory</a> "
                    u"to check file.".format(data_dir)
                    )
        self.taskHandler(msg, u'Fetching file ... ',
                self.btnFetchJar, self.fwFetchJarFile)


    def matchInJar(self):
        pass

    def updateJar(self):
        jarfile = self.cboFetchedFile.currentText()
        self.worker.add_task(
                self._updateJar(jarfile),
                TaskHandler(self.updateJarHandler)
                )

    def _updateJar(self, jarfile):
        (yield TaskOutput(u'ENTER', OutputType.NOTIFY))
        code = 0
        sshcli = SSHClient()
        sftpcli = None
        try:
            clsfiles = {}
            for i in xrange(self.tbSource.rowCount()):
                clsfile = self.tbSource.item(i, 2).text()
                clsfiles[clsfile] = i

            jarfname = os.path.join(self.local_bakdir, jarfile)
            zf = zipfile.ZipFile(jarfname, 'r')
            for zi in zf.infolist():
                fn = zi.filename
                n = clsfiles.get(fn, None)
                if n is not None:
                    (yield TaskOutput(('FOUND', n), OutputType.OUTPUT))

            #print "_updateJar", jarfile
            (yield TaskOutput(u'_updateJar'))
        except CommandTerminated:
            code = -2
            (yield TaskOutput(u'Updating Terminited', OutputType.WARN))
        except Exception as ex:
            code = -1
            (yield TaskOutput(ex.message, OutputType.ERROR))
        finally:
            if sftpcli: sftpcli.close()
            sshcli.close()
            (yield TaskOutput(u'EXIT %d' % code, OutputType.NOTIFY))

    @Slot(TaskOutput)
    def updateJarHandler(self, msg):
        if not hasattr(self, 'fwUpdateJar'):
            self.fwUpdateJar = u"Updating successfully!"
        ret = self.taskHandler(msg, u'Fetching file ... ',
                self.btnUpdateJar, self.fwUpdateJar)
        if ret is not None:
            if ret[0] == 'FOUND':
                ico_success = QTableWidgetItem(QIcon('success.png'),'')
                self.tbSource.setItem(ret[1], 1, ico_success)

    def getJarInfo(self):
        appdata = self.cboAppType.itemData(self.cboAppType.currentIndex())
        pfx = appdata['prefix']
        sfx = appdata['suffix']
        pth = appdata['path']
        self.txtFilePatt.setText("{}*.{}".format(pfx, sfx))
        self.txtRemotePath.setText(pth)
        if not os.path.isdir(self.local_bakdir):
            return
        self.cboFetchedFile.clear()
        for fn in os.listdir(self.local_bakdir):
            if fn.startswith(pfx) and fn.endswith(sfx):
                self.cboFetchedFile.addItem(fn)


    def addClassFile(self):
        fname = self.txtClsFile.text()
        try:
            mt = os.path.getmtime(fname)
        except Exception as ex:
            self.appendLog(TaskOutput(unicode(ex), OutputType.ERROR))
            return
        self._addClassFile(fname, mt)

    def _addClassFile(self, fname, mt):
        print fname
        mtime = time.strftime(mtime_fmt, time.localtime(mt))
        n = self.tbSource.rowCount()
        self.tbSource.insertRow(n)
        chk = QTableWidgetItem()
        chk.setCheckState(Qt.Checked)
        ico = QTableWidgetItem(QIcon("FAQ.png"), '')
        class_fn = fname.replace(self.txtSrcDir.text()+os.sep, '').replace(os.sep, '/')
        self.tbSource.setItem(n, 0, chk)
        self.tbSource.setItem(n, 1, ico)
        self.tbSource.setItem(n, 2, QTableWidgetItem(class_fn))
        self.tbSource.setItem(n, 3, QTableWidgetItem(mtime))
        self.tbSource.resizeColumnToContents(2)

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

        srcdir = self.txtSrcDir.text()
        self.worker.add_task(
                self._findNewClass(srcdir),
                TaskHandler(self.findNewClassHandler)
                )

    def _findNewClass(self, srcdir):
        (yield TaskOutput(u'ENTER', OutputType.NOTIFY))
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
                        (yield TaskOutput(('ADDFILE', fname, mt), OutputType.OUTPUT))
                        found += 1
            (yield TaskOutput(u'Found %s files.' % found))
        except CommandTerminated:
            code = -2
            (yield TaskOutput(u'TERMINITED: %s' % args[0], OutputType.WARN))
        except Exception as ex:
            code = -1
            (yield TaskOutput(ex.message, OutputType.ERROR))
        finally:
            (yield TaskOutput(u'EXIT %d' % code, OutputType.NOTIFY))

    @Slot(TaskOutput)
    def findNewClassHandler(self, msg):
        ret = self.taskHandler(msg,
                u'Searching New Class Files ... ', self.btnFindNew)
        if ret is not None:
            if type(ret) == tuple and ret[0] == 'ADDFILE':
                self._addClassFile(ret[1], ret[2])

    def closeEvent(self, event):
        self.worker.stop()
        event.accept()


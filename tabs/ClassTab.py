#!/usr/bin/env python2
# -* coding: utf-8 -*-

import os
import time
from PySide.QtCore import *
from PySide.QtGui import *
from yelib.qt.layout import *
from yelib.task import *
from paramiko import SSHClient, AutoAddPolicy
from tabs.BaseTab import BaseTab

mtime_fmt = "%m/%d %H:%M"

class ClassTab(BaseTab):

    def __init__(self, parent=None):
        super(ClassTab, self).__init__(parent)

        self.grpSource = self.createSourceGroup()
        self.grpTarget = self.createTargetGroup()

        self.lt = yBoxLayout([
            [ ('', self.grpSource) ],
            [ ('', self.grpTarget) ],
        ])
        self.setLayout(self.lt)
        self.setStyleSheet(
                'QTableWidget {border:1px solid gray;}'
                )
        self.workers = {}
        self.task = None

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

        self.btnAddFile = QPushButton('Add')
        self.btnAddFile.clicked.connect(self.addClassFile)
        self.btnRemoveFiles = QPushButton('Remove')
        self.btnRemoveFiles.clicked.connect(self.removeClassFiles)

        self.btnSearch = QPushButton('Search New')
        self.btnSearch.clicked.connect(self.searchNewer)
        self.btnStopSrch = QPushButton('Stop Search')
        self.btnStopSrch.clicked.connect(self.stopSearch)
        self.btnStopSrch.hide()
        self.btnSearch.setFixedWidth(80)
        self.btnStopSrch.setFixedWidth(80)
        ltSearch = yBoxLayout([
            [ ('', self.btnSearch), ('', self.btnStopSrch) ]
        ])

        self.txtNewerMins = QLineEdit()
        self.txtNewerMins.setFixedWidth(40)

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
        self.tbSource = tb
        wtMin = QWidget()
        ltMin = yBoxLayout([
            [ ('', QLabel('in')), ('', self.txtNewerMins, 'r'), ('', QLabel(u'mins')) ],
        ])
        wtMin.setLayout(ltMin)
        wtMin.setFixedWidth(100)
        lt = yGridLayout([
            [ ('', QLabel('Select Source Dir')), ('', self.txtSrcDir), ('', self.btnSrcDir),
              ('', ltSearch), ('', wtMin) ],
            [ ('', QLabel('Select Class File')), ('', self.txtClsFile),
              ('', self.btnClsFile), ('', self.btnAddFile), ('', self.btnRemoveFiles) ],
            [ ('', self.tbSource, 1, 5) ] + [None]*4,
        ])
        grp.setLayout(lt)

        return grp

    # ==== Target ====
    def createTargetGroup(self):
        grp = QGroupBox('Target')
        self.cboAppType = QComboBox()
        self.cboAppType.activated.connect(self.updateJarInfo)
        self.txtAppSrv = QLineEdit()
        self.txtSrvUser = QLineEdit()
        self.txtSrvPwd = QLineEdit()
        self.txtSrvPwd.setEchoMode(QLineEdit.Password)

        tb = QTableWidget()
        tb.setColumnCount(4)
        #tb.setSelectionBehavior(QAbstractItemView.SelectRows)
        tb.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tb.setHorizontalHeaderLabels(("", "Prefix", "File", "Path"))
        tb.horizontalHeader().setResizeMode(0, QHeaderView.Fixed)
        tb.horizontalHeader().setResizeMode(2, QHeaderView.ResizeToContents)
        #tb.horizontalHeader().setResizeMode(3, QHeaderView.ResizeToContents)
        tb.horizontalHeader().setResizeMode(3, QHeaderView.Interactive)
        tb.setColumnHidden(1, True)
        #tb.horizontalHeader().hide()
        tb.verticalHeader().hide()
        #tb.setFixedHeight(40)
        tb.setColumnWidth(0, 30)
        #tb.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        #tb.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.tbJarInfo = tb

        self.btnGetJar = QPushButton('Get Jarfile')
        self.btnRestore = QPushButton('Restore Jarfile')
        ltGrid = yGridLayout([
            [ ('', QLabel(u'App Type')), ('', self.cboAppType),
              ('', QLabel(u'Hostname')), ('', self.txtAppSrv) ],
            [ ('', QLabel(u'Username')), ('', self.txtSrvUser),
              ('', QLabel(u'Password')), ('', self.txtSrvPwd) ],
            [ ('', self.tbJarInfo,2,4) ],
        ])
        ltBtn = yBoxLayout([
            [ ('', self.btnGetJar) ],
            [ ('', self.btnRestore) ],
            None,
        ])
        lt = yBoxLayout([
            [ ('', ltGrid), ('', ltBtn) ]
        ])
        grp.setLayout(lt)

        return grp


    def updateJarInfo(self):
        appdata = self.cboAppType.itemData(self.cboAppType.currentIndex())
        self.tbJarInfo.removeRow(0)
        self.tbJarInfo.insertRow(0)
        statItem = QTableWidgetItem(QIcon('FAQ.png'), '')
        #statItem.setTextAlignment(Qt.AlignCenter)
        self.tbJarInfo.setItem(0, 0, statItem)
        self.tbJarInfo.setItem(0, 1, QTableWidgetItem(appdata['prefix']))
        self.tbJarInfo.setItem(0, 2, QTableWidgetItem(appdata['prefix'] + "*." + appdata['suffix']))
        self.tbJarInfo.setItem(0, 3, QTableWidgetItem(appdata['linux path']))
        self.tbJarInfo.resizeColumnToContents(3)


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

    def searchNewer(self):
        if self.task and self.stopTask():
            return

        mins = self.txtNewerMins.text()
        for i in xrange(self.tbSource.rowCount()):
            self.tbSource.removeRow(0)

        self.btnSearch.hide()
        self.btnStopSrch.show()
        self.showLoading(u'Searching class files newer than {} mins'.format(mins), True)

        srcdir = self.txtSrcDir.text()
        self.task = Task(self._searchNewer, srcdir)
        self.task.inst(self.searchHandler)
        self.workers['search'] = FuncWorker(self.task)

    def stopSearch(self):
        if self.task:
            self.task.terminate = True

    def _searchNewer(self, srcdir):
        curtime = time.time()
        found = 0
        code = 0
        try:
            for root,dirs,files in os.walk(srcdir):
                for f in files:
                    if self.task.terminate:
                        self.task.emitInfo(u'Terminating ...')
                        return
                    fname = os.path.join(root, f)
                    ext = os.path.splitext(f)[1]
                    if ext.lower() != ".class":
                        continue
                    mt = os.path.getmtime(fname)
                    secs = int(self.txtNewerMins.text()) * 60
                    if curtime - mt <= secs:
                        self.task.emitNotify(('ADDFILE', fname, mt))
                        found += 1
            self.task.emitInfo(u'Found {} files.'.format(found))
        except Exception as ex:
            self.task.emitError(unicode(ex))
            code = -1
        finally:
            self.task.emitNotify('EXIT '+str(code))

    @Slot(TaskOutput)
    def searchHandler(self, msg):
        if msg.type == OutputType.NOTIFY:
            output = msg.output
            if type(output) == str and output.startswith('EXIT '):
                self.showLoading('', False)
                self.btnStopSrch.hide()
                self.btnSearch.show()
                self.task = None
            elif type(output) == tuple and output[0] == 'ADDFILE':
                self._addClassFile(output[1], output[2])
        else:
            self.appendLog(msg)


    def closeEvent(self, event):
        if self.task:
            self.task.terminate = True
        for w in self.workers.values():
        	w.stop_wait()
        event.accept()


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


class ClassTab(BaseTab):

    def __init__(self, parent=None):
        super(ClassTab, self).__init__(parent)

        # ==== Source ====
        self.grpSource = QGroupBox(u'Source')
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
        self.btnSearch = QPushButton('Search Newer')
        self.btnSearch.clicked.connect(self.searchNewer)
        self.txtNewerMins = QLineEdit()
        self.txtNewerMins.setFixedWidth(40)

        tb = QTableWidget()
        tb.setColumnCount(3)
        tb.setSelectionBehavior(QAbstractItemView.SelectRows)
        tb.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tb.setHorizontalHeaderLabels(("", "Class File", "Modified Time"))
        tb.horizontalHeader().setResizeMode(0, QHeaderView.Fixed)
        tb.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)
        tb.horizontalHeader().setResizeMode(2, QHeaderView.ResizeToContents)
        tb.horizontalHeader().resizeSection(0, 30) 
        #tb.setColumnHidden(4, True)
        #tb.horizontalHeader().hide()
        tb.verticalHeader().hide()
        tb.setAlternatingRowColors(True)
        self.tbSource = tb
        wtMin = QWidget()
        ltMin = yBoxLayout([
            [ ('', self.txtNewerMins, 'r'), ('', QLabel(u'mins')) ],
        ])
        wtMin.setLayout(ltMin)
        wtMin.setFixedWidth(100)
        self.ltSource = yGridLayout([
            [ ('', QLabel('Select Source Dir')), ('', self.txtSrcDir), ('', self.btnSrcDir),
              ('', self.btnSearch), ('', wtMin) ],
            [ ('', QLabel('Select Class File')), ('', self.txtClsFile),
              ('', self.btnClsFile), ('', self.btnAddFile), ('', self.btnRemoveFiles) ],
            [ ('', self.tbSource, 1, 5) ] + [None]*4,
        ])
        self.grpSource.setLayout(self.ltSource)
        # ==== Source ====

        # ==== Target ====
        self.grpTarget = QGroupBox('Target')
        self.cboAppType = QComboBox()
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
        self.ltTarget = yGridLayout([
            [ ('', QLabel(u'App Type')), ('', self.cboAppType),
              ('', QLabel(u'Hostname')), ('', self.txtAppSrv) ],
            [ ('', QLabel(u'Username')), ('', self.txtSrvUser),
              ('', QLabel(u'Password')), ('', self.txtSrvPwd) ],
            [ ('', self.tbJarInfo,2,4), None, None, None, ('', self.btnGetJar) ],
            [ None, None, None, None, ('', self.btnRestore) ],
        ])
        self.grpTarget.setLayout(self.ltTarget)
        # ==== Target ====

        self.lt = yBoxLayout([
            [ ('', self.grpSource) ],
            [ ('', self.grpTarget) ],
        ])
        self.setLayout(self.lt)
        self.setStyleSheet(
                'QTableWidget {border:1px solid gray;}'
                )

        self.cboAppType.activated.connect(self.updateJarInfo)


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
                self, u'Select Java File', clsfile.text(), "Java Source File (*.java)")
        self.txtClsFile.setText(fname[0])

    def addClassFile(self):
        fname = self.txtClsFile.text()
        try:
            mt = os.path.getmtime(fname)
        except Exception as ex:
            self.appendLog(TaskOutput(unicode(ex), OutputType.ERROR))
            return
        mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(mt))
        self._addClassFile(fname, mtime)

    def _addClassFile(self, fname, mtime):
        n = self.tbSource.rowCount()
        self.tbSource.insertRow(n)
        chk = QTableWidgetItem()
        chk.setCheckState(Qt.Checked)
        self.tbSource.setItem(n, 0, chk)
        self.tbSource.setItem(n, 1, QTableWidgetItem(fname))
        self.tbSource.setItem(n, 2, QTableWidgetItem(mtime))

    def removeClassFiles(self):
        n = self.tbSource.rowCount()

        for row in xrange(n-1, -1, -1):
            if self.tbSource.item(row, 0).checkState() == Qt.Unchecked:
            	continue
            self.tbSource.removeRow(row)

    def searchNewer(self):
        mins = self.txtNewerMins.text()
        self.showLoading(u'Searching java files newer than {} mins'.format(mins), True)
        for i in xrange(self.tbSource.rowCount()):
            self.tbSource.removeRow(0)

        srcdir = self.txtSrcDir.text()
        for fname, mtime in self._searchNewer(srcdir):
        	self._addClassFile(fname, mtime)
        self.showLoading('', False)

    def _searchNewer(self, srcdir):
        curtime = time.time()
        for root,dirs,files in os.walk(srcdir):
            for f in files:
            	fname = os.path.join(root, f)
            	ext = os.path.splitext(f)[1]
                if ext.lower() != ".java":
                	continue
            	mtime = os.path.getmtime(fname)
            	secs = int(self.txtNewerMins.text()) * 60
                if curtime - mtime <= secs:
                	yield (fname, mtime)



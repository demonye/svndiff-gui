#!/usr/bin/env python2
# -* coding: utf-8 -*-

import os
import time
from PySide.QtCore import *
from PySide.QtGui import *
from yelib.qt.layout import *
from yelib.task import *
from yelib.util import force_rmdir
from paramiko import SSHClient, AutoAddPolicy

import locale
coding = locale.getdefaultlocale()[1]

class ClassTab(QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.parent = parent
        self.setting = parent.tabSetting

        self.setFont(QFont("Monospace", 10))

        # ==== Source ====
        self.grpSource = QGroupBox(u'Source')
        self.txtSrcDir = QLineEdit()
        self.btnSrcDir = QPushButton(' / ')
        self.btnAddFile = QPushButton('Add File')
        self.btnSearch = QPushButton('Search')
        self.txtNewerTime = QLineEdit()
        self.txtNewerTime.setFixedWidth(40)

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
        self.ltSource = yBoxLayout([
            [ ('', QLabel('Select Class Files')), ('', self.txtSrcDir),
              ('', self.btnSrcDir), ('', self.btnAddFile) ],
            [ ('', self.btnSearch), ('', QLabel(u' Files Modified In Recent ')),
              ('', self.txtNewerTime), ('', QLabel(u' Minutes')), None ],
            [ ('', self.tbSource) ],
        ])
        self.btnSrcDir.setFixedWidth(20)
        self.grpSource.setLayout(self.ltSource)
        # ==== Source ====

        # ==== Target ====
        self.grpTarget = QGroupBox('Target')
        self.cboAppType = QComboBox()
        appconf = open('apptype.conf')
        for l in appconf.readlines():
            arr = l.rstrip().split(',')
            app, prefix, rmtdir = arr[0:3]
            locdir = (len(arr) > 3 and arr[3] or None)
            self.cboAppType.addItem(app, (prefix, rmtdir, locdir))
        self.chkLocal = QCheckBox('Local')
        self.txtSrvIp = QLineEdit()

        tb = QTableWidget()
        tb.setColumnCount(3)
        #tb.setSelectionBehavior(QAbstractItemView.SelectRows)
        tb.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tb.setHorizontalHeaderLabels(("", "Prefix", "Path"))
        tb.horizontalHeader().setResizeMode(0, QHeaderView.Fixed)
        tb.horizontalHeader().setResizeMode(1, QHeaderView.Interactive)
        #tb.horizontalHeader().setResizeMode(1, QHeaderView.ResizeToContents)
        tb.horizontalHeader().setResizeMode(2, QHeaderView.Interactive)
        tb.verticalHeader().hide()
        tb.setFixedHeight(70)
        tb.setColumnWidth(0, 30)
        tb.setColumnWidth(2, 400)
        #tb.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        #tb.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        #tb.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.tbJarInfo = tb

        self.btnGetJar = QPushButton('Get Jar File')
        self.btnGetJar.setFixedHeight(50)
        self.ltTarget = yBoxLayout([
            [ ('', QLabel(u'App Type')), ('', self.cboAppType),
              None, ('', QLabel(u'Remote Ip Address')), ('', self.txtSrvIp),
              None, ('', self.chkLocal), None ],
            [ ('', self.tbJarInfo), ('', self.btnGetJar) ],
        ])
        self.grpTarget.setLayout(self.ltTarget)
        # ==== Target ====

        self.lt = yBoxLayout([
            [ ('', self.grpSource) ],
            [ ('', self.grpTarget) ],
        ])
        self.setLayout(self.lt)
        self.updateJarInfo()

        self.cboAppType.activated.connect(self.updateJarInfo)
        self.chkLocal.stateChanged.connect(self.updateJarInfo)


    def updateJarInfo(self):
        appdata = self.cboAppType.itemData(self.cboAppType.currentIndex())
        self.tbJarInfo.removeRow(0)
        self.tbJarInfo.insertRow(0)
        statItem = QTableWidgetItem(QIcon('delete256.png'), '')
        #statItem.setTextAlignment(Qt.AlignCenter)
        self.tbJarInfo.setItem(0, 0, statItem)
        self.tbJarInfo.setItem(0, 1, QTableWidgetItem(appdata[0]))
        path_n = 1
        if self.chkLocal.isChecked():
            path_n = 2
        self.tbJarInfo.setItem(0, 2, QTableWidgetItem(appdata[path_n]))



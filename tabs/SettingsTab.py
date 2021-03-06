#!/usr/bin/env python2
# -* coding: utf-8 -*-

from PySide.QtCore import *
from PySide.QtGui import *
from yelib.qt.layout import *
from tabs.BaseTab import *
from ConfigParser import *

class SettingsTab(QDialog):

    def __init__(self, parent=None):
        super(SettingsTab, self).__init__(parent)

        grpDiff = self.createDiffGroup()

        # ==== Config ====
        tabDiff = parent.main.tabDiff
        tabClass = parent.main.tabClass
        self.config_map = {
            'svn': {
                'username': self.txtSvnId,
                'password': self.txtSvnPwd,
            },
            'diff server': {
                'hostname': self.txtDiffSrv,
                'auth by': {'password':self.rdoPwd, 'keyfile':self.rdoKey},
                'username': self.txtSrvUser,
                'password': self.txtSrvPwd,
                'keyfile': self.txtKeyFile,
                'remote dir': self.txtRmtDir,
                'http url': self.txtHttpUrl,
            },
            'java app': {
                'app types': tabClass.cboAppType
            },
            'recent records': {
                'diff bug id': tabDiff.txtBugId,
                'diff source path': tabDiff.txtSrcDir,
                'java source path': tabClass.txtSrcDir,
                'java app': tabClass.cboAppType.setCurrentIndex,
                'java app server': tabClass.txtAppSrv,
                'java app username': tabClass.txtSrvUser,
                'java app password': tabClass.txtSrvPwd,
                'search newer mins': tabClass.txtNewInMins
            },

        }
        self.config = SafeConfigParser()
        self.config_fname = "settings.cfg"
        self.loadConfig()
        # ==== Config ====

        self.btnReload = QPushButton('Reload')
        self.btnReload.clicked.connect(self.loadConfig)
        self.btnSave = QPushButton('Save')
        self.btnSave.clicked.connect(self.saveConfig)
        self.btnCancel = QPushButton('Cancel')
        self.btnCancel.clicked.connect(self.close)
        self.lt = yBoxLayout([
            [ grpDiff ],
            [ None, self.btnReload, self.btnSave, self.btnCancel ],
            None,
        ])
        self.setLayout(self.lt)
        self.setWindowTitle('Settings')
        #BaseTab.settings = self
        #tabClass.getJarInfo()


    # ==== Make Diff Settings ====
    def createDiffGroup(self):
        self.txtDiffSrv = QLineEdit()
        self.txtDiffSrv.setFixedWidth(150)
        self.txtSrvUser = QLineEdit()
        self.txtSrvUser.setFixedWidth(150)
        self.txtRmtDir = QLineEdit()
        self.txtHttpUrl = QLineEdit()

        self.txtSrvPwd = QLineEdit()
        self.txtSrvPwd.setEchoMode(QLineEdit.Password)
        self.txtSrvPwd.setFixedWidth(150)
        self.rdoPwd = QRadioButton(u'Password', self)
        self.rdoPwd.clicked.connect(self.authByPwd)

        self.txtKeyFile = QLineEdit()
        self.btnKeyFile = QPushButton(' / ')
        self.rdoKey = QRadioButton(u'Key File', self)
        self.btnKeyFile.setFixedWidth(20)
        self.btnKeyFile.clicked.connect(self.selectKeyFile)
        self.rdoKey.clicked.connect(self.authByKey)

        self.txtSvnId = QLineEdit()
        self.txtSvnId.setFixedWidth(150)
        self.txtSvnPwd = QLineEdit()
        self.txtSvnPwd.setFixedWidth(150)
        self.txtSvnPwd.setEchoMode(QLineEdit.Password)

        grp = QGroupBox(u'Upload Diff To Server')
        lt = yGridLayout([
            [ (QLabel(u'Host/IP'),1,1,'r'), self.txtDiffSrv,
              (QLabel(u'Upload To'),1,1,'r'), (self.txtRmtDir,1,2) ],
            [ (QLabel(u'Username'),1,1,'r'), self.txtSrvUser,
              (QLabel(u'Http URL'),1,1,'r'), (self.txtHttpUrl,1,2) ],
            [ self.rdoPwd, self.txtSrvPwd,
              self.rdoKey, self.txtKeyFile, self.btnKeyFile ],
            [ (QLabel(' '),1,1) ],
            [ (QLabel('Svn Account'),1,1,'r'), self.txtSvnId ],
            [ (QLabel('Svn Password'),1,1,'r'), self.txtSvnPwd ],
        ])
        #self.txtSrvUser.setMaximumWidth(100)
        grp.setLayout(lt)

        return grp

    def loadConfig(self):
        self.config.read(self.config_fname)
        for sect, sect_v in self.config_map.items():
            for key, ctrl in sect_v.items():
                value = self.conf(sect, key)
                if isinstance(ctrl, (QLineEdit, SelectFile)):
                    ctrl.setText(value)
                elif isinstance(ctrl, dict):
                    ctrl[value].click()
                elif isinstance(ctrl, QComboBox):
                    for _ in value.split(','):
                        app = _.strip()
                        data = {}
                        for k in ('suffix','prefix','path', 'local'):
                            data[k] = self.conf(app, k)
                        ctrl.addItem(app, data)
                elif hasattr(ctrl, '__call__'):
                    apps = self.conf(key, 'app types').split(',')
                    for i in xrange(len(apps)):
                        if value == apps[i].strip():
                            ctrl(i)
                            break

    def saveConfig(self):
        for sect, sect_v in self.config_map.items():
            for key, ctrl in sect_v.items():
                if isinstance(ctrl, (QLineEdit, SelectFile)):
                    self.conf(sect, key, ctrl.text())
                elif isinstance(ctrl, dict):
                    for val, realctrl in ctrl.items():
                        if realctrl.isChecked():
                            self.conf(sect, key, val)
                            break
                elif hasattr(ctrl, '__call__'):
                    realctrl = self.config_map[key]['app types']
                    self.conf(sect, key, realctrl.currentText())

        f = open(self.config_fname, "wb")
        self.config.write(f)
        f.close()

        self.close()


    def closeEvent(self, event):
        self.loadConfig()
        event.accept()

    def authByPwd(self):
        self.txtSrvPwd.setDisabled(False)
        self.txtKeyFile.setDisabled(True)
        self.btnKeyFile.setDisabled(True)

    def authByKey(self):
        self.txtSrvPwd.setDisabled(True)
        self.txtKeyFile.setDisabled(False)
        self.btnKeyFile.setDisabled(False)

    def selectKeyFile(self):
        keyfile = self.txtKeyFile
        filename = QFileDialog.getOpenFileName(self, u'Select Key File', keyfile.text())
        if len(filename) > 0:
            keyfile.setText(filename[0])

    def conf(self, sect, key, value=None):
        if value is None:
            try:
                return self.config.get(sect, key)
            except (NoSectionError, NoOptionError):
                return ''
        else:
            if not self.config.has_section(sect):
                self.config.add_section(sect)
            self.config.set(sect, key, value)
            return None

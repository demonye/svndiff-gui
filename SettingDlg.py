#!/usr/bin/env python2
# -* coding: utf-8 -*-

from PySide.QtCore import *
from PySide.QtGui import *
from yelib.qt.layout import *
import cPickle as pk

class SettingDlg(QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.parent = parent

        self.setFont(QFont("Monospace", 10))
        self.config_file = "settings"
        try:
            self.config = pk.load(open(self.config_file))
        except IOError:
            self.config = {}

        # ==== Source Settings ====
        self.grpSource = QGroupBox(u'Path of your source code')
        self.txtSvnId = QLineEdit(self.conf('svnid'))
        #self.txtSvnCmd = QLineEdit(self.conf('svncmd'))
        self.txtSrcDir = QLineEdit(self.conf('srcdir'))
        self.btnSrcDir = QPushButton(' / ')
        self.ltSource = yBoxLayout([
            [ ('', QLabel('Your Svn Id')), ('', self.txtSvnId), None ],
            #[ ('', QLabel('Svn Command')), ('', self.txtSvnCmd) ],
            [ ('', QLabel('Source Path')), ('', self.txtSrcDir), ('', self.btnSrcDir) ],
        ])
        self.grpSource.setLayout(self.ltSource)
        self.btnSrcDir.setFixedWidth(20)
        self.btnSrcDir.clicked.connect(self.select_srcdir)
        # ==== Source Settings ====

        # ==== Server Settings ====
        self.grpServer = QGroupBox(u'Server to upload diff')
        self.txtSrvHost = QLineEdit(self.conf('srvhost'))
        self.txtSrvUser = QLineEdit(self.conf('srvuser'))
        self.txtSrvPwd = QLineEdit(self.conf('srvpwd'))
        self.txtSrvPwd.setEchoMode(QLineEdit.Password)
        self.txtKeyFile = QLineEdit(self.conf('keyfile'))
        self.btnKeyFile = QPushButton(' / ')
        self.txtRmtDir = QLineEdit(self.conf('rmtdir'))
        self.txtHttpUrl = QLineEdit(self.conf('httpurl'))
        self.rdoPwd = QRadioButton(u'Password', self)
        self.rdoKey = QRadioButton(u'Key File', self)
        self.ltServer = yBoxLayout([
            [ ('', QLabel(u'Host/IP    ')), ('', self.txtSrvHost), None ],
            [ ('', QLabel(u'Username   ')), ('', self.txtSrvUser), None ],
            [ ('', self.rdoPwd), ('', self.txtSrvPwd), None ],
            [ ('', self.rdoKey), ('', self.txtKeyFile), ('', self.btnKeyFile) ],
            [ ('', QLabel(u'Upload To  ')), ('', self.txtRmtDir) ],
            [ ('', QLabel(u'Http URL   ')), ('', self.txtHttpUrl) ],
        ])
        #self.txtSrvUser.setMaximumWidth(100)
        self.grpServer.setLayout(self.ltServer)
        self.btnKeyFile.setFixedWidth(20)
        self.btnKeyFile.clicked.connect(self.select_keyfile)
        self.rdoPwd.clicked.connect(self.auth_by_pwd)
        self.rdoKey.clicked.connect(self.auth_by_key)
        if self.conf('authbykey'):
            self.rdoKey.click()
        else:
            self.rdoPwd.click()
        # ==== Server Settings ====

        self.btnSave = QPushButton('Save')
        self.btnSave.clicked.connect(self.save_config)
        self.lt = yBoxLayout([
            [ ('', self.grpServer) ],
            [ ('', self.grpSource) ],
            [ None, ('', self.btnSave) ],
            None,
        ])
        self.setLayout(self.lt)

    def closeEvent(self, event):
        self.save_config()
        event.accept()

    def auth_by_pwd(self):
        self.txtSrvPwd.setDisabled(False)
        self.txtKeyFile.setDisabled(True)
        self.btnKeyFile.setDisabled(True)

    def auth_by_key(self):
        self.txtSrvPwd.setDisabled(True)
        self.txtKeyFile.setDisabled(False)
        self.btnKeyFile.setDisabled(False)

    def select_srcdir(self):
        srcdir = self.txtSrcDir
        dirname = QFileDialog.getExistingDirectory(self, u'Select Source Directory', srcdir.text())
        if len(dirname) > 0:
            srcdir.setText(dirname)

    def select_keyfile(self):
        keyfile = self.txtKeyFile
        filename = QFileDialog.getOpenFileName(self, u'Select Key File', keyfile.text())
        if len(filename) > 0:
            keyfile.setText(filename[0])

    def conf(self, key, value=None):
        if value is not None:
            self.config[key] = value
        if key == 'authbykey':
            return self.config.get(key, False)
        else:
            return self.config.get(key, '')

    def save_config(self):
        self.conf('svnid', self.txtSvnId.text())
        #self.conf('svncmd', self.txtSvnCmd.text())
        self.conf('srcdir', self.txtSrcDir.text())
        self.conf('srvhost', self.txtSrvHost.text())
        self.conf('srvuser', self.txtSrvUser.text())
        self.conf('srvpwd', self.txtSrvPwd.text())
        self.conf('rmtdir', self.txtRmtDir.text())
        self.conf('keyfile', self.txtKeyFile.text())
        self.conf('httpurl', self.txtHttpUrl.text())
        self.conf('authbykey', self.rdoKey.isChecked())
        pk.dump(self.config, open(self.config_file, 'w'))


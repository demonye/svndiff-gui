#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
from PySide.QtCore import *
from PySide.QtGui import *
from yelib.qt.layout import *
import cPickle as pk

from DiffTab import DiffTab

class MainWindow(QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setFont(QFont("Monospace", 10))
        self.config_file = "settings"
        try:
            self.config = pk.load(open(self.config_file))
        except IOError:
            self.config = {}

        # ==== Source Settings ====
        self.grpSource = QGroupBox(u'Source')
        self.txtSvnId = QLineEdit(self.conf('svnid'))
        self.txtSvnCmd = QLineEdit(self.conf('svncmd'))
        self.txtSrcDir = QLineEdit(self.conf('srcdir'))
        self.ltSource = yBoxLayout([
            [ ('', QLabel('Your Svn Id')), ('', self.txtSvnId), None ],
            [ ('', QLabel('Svn Command')), ('', self.txtSvnCmd) ],
            [ ('', QLabel('Source Path')), ('', self.txtSrcDir) ],
        ])
        self.grpSource.setMinimumWidth(400)
        self.grpSource.setLayout(self.ltSource)
        # ==== Source Settings ====

        # ==== Server Settings ====
        self.grpServer = QGroupBox(u'Server')
        self.txtSrvHost = QLineEdit(self.conf('srvhost'))
        self.txtSrvUser = QLineEdit(self.conf('srvuser'))
        self.txtSrvPwd = QLineEdit(self.conf('srvpwd'))
        self.txtSrvPwd.setEchoMode(QLineEdit.Password)
        self.txtKeyFile = QLineEdit(self.conf('keyfile'))
        self.txtRmtDir = QLineEdit(self.conf('rmtdir'))
        self.rdoPwd = QRadioButton(u'Password', self)
        self.rdoKey = QRadioButton(u'Key File', self)
        self.ltServer = yBoxLayout([
            [ ('', QLabel(u'Host')), ('', self.txtSrvHost), ('', QLabel(u'Username')), ('', self.txtSrvUser) ],
            [ ('', QLabel(u'Upload To')), ('', self.txtRmtDir) ],
            [ ('', self.rdoPwd), ('', self.txtSrvPwd), ('', self.rdoKey), ('', self.txtKeyFile) ],
        ])
        #self.txtSrvUser.setMaximumWidth(100)
        self.grpServer.setMinimumWidth(400)
        self.grpServer.setLayout(self.ltServer)
        self.rdoPwd.clicked.connect(self.auth_by_pwd)
        self.rdoKey.clicked.connect(self.auth_by_key)
        if self.conf('authbykey'):
            self.rdoKey.click()
        else:
            self.rdoPwd.click()
        # ==== Server Settings ====

        # ==== Tab Widget ====
        self.tab = QTabWidget()
        self.tabDiff = DiffTab(self)
        self.tab.addTab(self.tabDiff, u'Make Diff')
        self.tab.setMinimumHeight(300)
        # ==== Tab Widget ====

        # ==== Log ====
        self.grpLog = QGroupBox(u'Log')
        self.txtLog = QTextBrowser()
        self.txtLog.setReadOnly(True)
        self.txtLog.setMinimumHeight(60)
        self.txtLog.setOpenExternalLinks(True)
        self.ltLog = yBoxLayout([
            [ ('', self.txtLog) ]
        ])
        self.grpLog.setLayout(self.ltLog)
        # ==== Log ====

        # ==== Main Layout ====
        self.btnExit = QPushButton(u'Exit')
        self.lt = yBoxLayout([
            [ ('', self.grpSource), ('', self.grpServer) ],
            [ ('', self.tab) ],
            [ ('', self.grpLog) ],
            [ None, ('', self.btnExit) ],
        ])
        self.btnExit.clicked.connect(self.close)
        self.setLayout(self.lt)
        self.setWindowTitle('Svn Tool')
        self.setWindowIcon(QIcon('./logo.png'))
        # ==== Main Layout ====

        self.statusIcons = {
                'A': QIcon('fileadd.ico'),
                'M': QIcon('filemodify.ico'),
                'D': QIcon('filedelete.ico'),
                }

    def center(self):
        self.move(
            QApplication.desktop().screen().rect().center() -
            self.rect().center() )

    def conf(self, key, value=None):
        if value is not None:
            self.config[key] = value
        if key == 'authbykey':
            return self.config.get(key, False)
        else:
            return self.config.get(key, '')

    #def reject(self):
    #    self.close()

    def closeEvent(self, event):
        self.save_config()
        for i in xrange(self.tab.count()):
            self.tab.widget(i).close()
        event.accept()

    def auth_by_pwd(self):
        self.txtSrvPwd.setDisabled(False)
        self.txtKeyFile.setDisabled(True)

    def auth_by_key(self):
        self.txtSrvPwd.setDisabled(True)
        self.txtKeyFile.setDisabled(False)

    def save_config(self):
        self.conf('svnid', self.txtSvnId.text())
        self.conf('svncmd', self.txtSvnCmd.text())
        self.conf('srcdir', self.txtSrcDir.text())
        self.conf('srvhost', self.txtSrvHost.text())
        self.conf('srvuser', self.txtSrvUser.text())
        self.conf('srvpwd', self.txtSrvPwd.text())
        self.conf('rmtdir', self.txtRmtDir.text())
        self.conf('keyfile', self.txtKeyFile.text())
        self.conf('authbykey', self.rdoKey.isChecked())
        pk.dump(self.config, open(self.config_file, 'w'))

    def append_log(self, logtext=''):
        #self.txtLog.appendPlainText(logtext)
        self.txtLog.append(logtext) #+"<img src='loading.gif'/>")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    win.center()
    sys.exit(app.exec_())

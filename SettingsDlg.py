#!/usr/bin/env python2
# -* coding: utf-8 -*-

from PySide.QtCore import *
from PySide.QtGui import *
from yelib.qt.layout import *
from tabs.BaseTab import SelectFile
from ConfigParser import *

class SettingsDlg(QDialog):

    def __init__(self, parent=None):
        super(SettingsDlg, self).__init__(parent)

        self.config = SafeConfigParser()
        self.config_fname = "settings.cfg"

        widgets = [
            ("txtSvnUser", QLineEdit(), 130),
            ("txtSvnPwd", QLineEdit(), 130),
            ("txtDiffSrv", QLineEdit(), 130),
            ("txtDiffUser", QLineEdit(), 130),
            ("txtDiffPwd", QLineEdit(), 130),
            ("txtDiffDir", QLineEdit(), 0),
            ("txtDiffUrl", QLineEdit(), 0),
            ("lstApp", QListWidget(), 160),
            ("btnAddApp", QPushButton(QIcon('image/add.png'), 'Add'), 0),
            ("btnRemoveApp", QPushButton(QIcon('image/remove.png'), 'Remove'), 0),
            ("txtAppSrcDir",
                SelectFile(None, 'Select Source Dir', type='dir'),
                0),
            ("txtAppClsDir",
                SelectFile(None, 'Select Classes Dir', type='dir'),
                0),
            ("txtAppTarFile", QTextEdit(), 0),
            ("txtAppSrv", QLineEdit(), 130),
            ("txtAppUser", QLineEdit(), 130),
            ("txtAppPwd", QLineEdit(), 130),
            ("txtAppStartup", QLineEdit(), 0),
            ("txtAppShutdown", QLineEdit(), 0),
            ("btnSave", QPushButton(QIcon('image/accept.png'), 'Save'), 0),
            ("btnCancel", QPushButton('Cancel'), 0),
        ]
        for w in widgets:
            setattr(self, w[0], w[1])
            if w[2] > 0:
                getattr(self, w[0]).setFixedWidth(w[2])
        self.txtSvnPwd.setEchoMode(QLineEdit.Password)
        self.txtDiffPwd.setEchoMode(QLineEdit.Password)
        self.txtAppPwd.setEchoMode(QLineEdit.Password)
        self.lstApp.setSizePolicy(
            QSizePolicy.Policy(QSizePolicy.Fixed),
            QSizePolicy.Policy(QSizePolicy.Preferred),
            )
        self.lstApp.setAlternatingRowColors(True)
        self.lstApp.currentItemChanged.connect(self.updateAppInfo)
        self.lstApp.itemChanged.connect(self.lstApp.setCurrentItem)
        #self.lstApp.itemDoubleClicked.connect(self.lstApp.openPersistentEditor)
        self.lstApp.itemDoubleClicked.connect(self.lstApp.editItem)

        self.txtAppTarFile.setFixedHeight(45)

        # ==== Svn Settings ====
        grpSvn = QGroupBox('Svn Settings')
        grpSvn.setLayout(yGridLayout([
            [ 'Svn Account', self.txtSvnUser, None, ],
            [ 'Password', self.txtSvnPwd, None, ],
            ])
        )
        grpSvn.layout().setColumnStretch(2, 10)
        # ==== Svn Settings ====

        # ==== Diff Settings ====
        grpDiff = QGroupBox('Diff Settings')
        grpDiff.setLayout(yGridLayout([
            [ 'Diff Server', self.txtDiffSrv ],
            [ 'Username', self.txtDiffUser, 'Upload To', self.txtDiffDir ],
            [ 'Password', self.txtDiffPwd,  'Http Url', self.txtDiffUrl ],
            ])
        )
        grpDiff.layout().setColumnStretch(3, 10)
        # ==== Diff Settings ====

        # ==== App Settings ====
        grpApp = QGroupBox('Applications')
        grpInfo = QGroupBox('App Detail')
        grpInfo.setLayout(yGridLayout([
            [ 'Source Dir', self.txtAppSrcDir ], 
            [ 'Classes Dir', self.txtAppClsDir ], 
            [ 'Target File' ], [ (self.txtAppTarFile,1,2) ],
            [ 'Target Server', self.txtAppSrv ], 
            [ 'Username', self.txtAppUser ], 
            [ 'Password', self.txtAppPwd ], 
            [ 'Startup', self.txtAppStartup ], 
            [ 'Shutdown', self.txtAppShutdown ], 
            ])
        )
        grpApp.setLayout(
            yBoxLayout([
                [ yBoxLayout([
                    [ self.lstApp ],
                    [ self.btnAddApp, self.btnRemoveApp ],
                    ]) , grpInfo
                ],
            ])
        )
        self.btnAddApp.clicked.connect(self.addApp)
        self.btnRemoveApp.clicked.connect(self.removeApp)
        # ==== App Settings ====

        self.setLayout(yBoxLayout([
            [ grpSvn ],
            [ grpDiff ],
            [ grpApp ],
            None,
            [ None, self.btnSave, self.btnCancel ],
            ])
        )
        self.setFixedSize(670, 600)
        self.setWindowTitle('Settings')
        self.setWindowIcon(QIcon('image/settings.png'))
        self.setDlgStyle()

        self.btnSave.clicked.connect(self.saveAndClose)
        self.btnSave.setFixedSize(80, 28)
        self.btnCancel.clicked.connect(self.cancelAndClose)
        self.btnCancel.setFixedSize(80, 28)

    def setDlgStyle(self):
        self.setStyleSheet("""
        QListWidget {
            border: 2px solid rgb(180,180,180);
            border-radius: 3px;
        }
        QLineEdit, QTextEdit {
            border: 1px solid rgb(180,180,180);
            border-radius: 3px;
        }
            QPushButton {
                padding: 5px;
                /*background: rgb(180,180,180);*/
                border: 1px solid rgb(150,150,150);
                border-radius: 2px;
            }
            QPushButton:hover { background: rgb(150,150,150); }
        """)

    def addApp(self):
        item = QListWidgetItem(QIcon('image/application.png'), '')
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.lstApp.addItem(item)
        self.lstApp.editItem(item)

    def removeApp(self):
        self.lstApp.takeItem(self.lstApp.currentRow())

    def saveAndClose(self):
        self.save()
        self.parent().notifyConfigChanged()
        self.close()

    def cancelAndClose(self):
        self.load()
        self.close()

#    def closeEvent(self, event):
#        event.accept()

    def showEvent(self, event):
        self.load()
        event.accept()

    def load(self):
        self.config.read(self.config_fname)
        self.txtSvnUser.setText(self.conf('svn', 'username'))
        self.txtSvnPwd.setText(self.conf('svn', 'password'))
        self.txtDiffSrv.setText(self.conf('diff', 'server'))
        self.txtDiffUser.setText(self.conf('diff', 'username'))
        self.txtDiffPwd.setText(self.conf('diff', 'password'))
        self.txtDiffDir.setText(self.conf('diff', 'remote dir'))
        self.txtDiffUrl.setText(self.conf('diff', 'httpp url'))

        self.lstApp.clear()
        for _ in self.conf('app', 'list').split(','):
            v = _.strip()
            item = QListWidgetItem(QIcon('image/application'), v)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.lstApp.addItem(item)
        self.lstApp.setCurrentRow(0)

    def updateAppInfo(self, curr, prev):
        if prev:
            app = prev.text()
            self.conf(app, 'source dir', self.txtAppSrcDir.text())
            self.conf(app, 'classes dir', self.txtAppClsDir.text())
            self.conf(app, 'target file', self.txtAppTarFile.toPlainText())
            self.conf(app, 'server', self.txtAppSrv.text())
            self.conf(app, 'username', self.txtAppUser.text())
            self.conf(app, 'password', self.txtAppPwd.text())
            self.conf(app, 'startup', self.txtAppStartup.text())
            self.conf(app, 'shutdown', self.txtAppShutdown.text())
        if curr:
            app = curr.text()
            self.txtAppSrcDir.setText(self.conf(app, 'source dir'))
            self.txtAppClsDir.setText(self.conf(app, 'classes dir'))
            self.txtAppTarFile.setText(self.conf(app, 'target file'))
            self.txtAppSrv.setText(self.conf(app, 'server'))
            self.txtAppUser.setText(self.conf(app, 'username'))
            self.txtAppPwd.setText(self.conf(app, 'password'))
            self.txtAppStartup.setText(self.conf(app, 'startup'))
            self.txtAppShutdown.setText(self.conf(app, 'shutdown'))


    def save(self):
        self.updateAppInfo(None, self.lstApp.currentItem())

        apps = []
        for i in xrange(self.lstApp.count()):
            apps.append(self.lstApp.item(i).text())
        oldapps = [v.strip() for v in self.conf('app', 'list').split(',')]
        for app in oldapps:
            if app not in apps:
                self.config.remove_section(app)
        self.conf('app', 'list', ','.join(apps))

        f = open(self.config_fname, "wb")
        self.config.write(f)
        f.close()

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SettingsDlg()
    win.show()
    sys.exit(app.exec_())

#!/usr/bin/env python2
# -* coding: utf-8 -*-

import os
from PySide.QtCore import *
from PySide.QtGui import *
from yelib.qt.layout import *
from yelib.qt.widgets import FileSelector, IconLabel
from ConfigParser import *
from Crypto.Cipher import DES

myDes = DES.new('rAYoTEcH', DES.MODE_ECB)
def encrypt(text, errval=''):
    if text == "":
    	return text
    try:
        enc = "%04d%s" % (len(text), text)
        enc += ' ' * (8 - len(enc) % 8)
        return myDes.encrypt(enc).encode('hex')
    except:
        return errval

def decrypt(code, errval=''):
    if code == "":
    	return code
    try:
        enc = myDes.decrypt(code.decode('hex'))
        textlen = int(enc[0:4])
        return enc[4:textlen+4]
    except:
        return errval

class MyValidator(QValidator):

    sig = Signal(str)

    def __init__(self, items, hdlr, parent=None):
        super(MyValidator, self).__init__(parent)
        self.items = items
        self.sig.connect(hdlr)

    def validate(self, inp, pos):
        if inp == "":
            self.sig.emit("Item cannot be empty!")
            return QValidator.Intermediate
        if inp in self.items:
            self.sig.emit("Item '%s' already exists!" % inp)
            return QValidator.Intermediate
        self.sig.emit('')
        return QValidator.Acceptable

class MyDelegate(QItemDelegate):

    def __init__(self, lst, hdlr, parent=None):
        super(MyDelegate, self).__init__(parent)
        self.lst = lst
        self.hdlr = hdlr

    def createEditor(self, parent, option, index):
        items = []
        for i in xrange(self.lst.count()):
            if i != index.row():
                items.append(self.lst.item(i).text())
        editor = QLineEdit(parent)
        editor.setStyleSheet("border:1px solid dimgray")
        validator = MyValidator(items, self.hdlr, parent)
        editor.setValidator(validator)
        return editor


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
            ("btnAddApp", QPushButton(QIcon('image/add.png'), ''), 0),
            ("btnRemoveApp",
                QPushButton(QIcon('image/delete.png'), ''), 0),
            ("btnCopyApp", QPushButton(QIcon('image/copy.png'), ''), 0),
            ("txtJarBin", FileSelector(None, 'Select Jar Executable Bin'), 0),
            ("txtAppSrcRoot",
                FileSelector(None, 'Select Source Root', type='dir'), 0),
            ("txtAppWebappDir", QLineEdit(), 0),
            ("txtAppJavaDir", QLineEdit(), 0),
            ("txtAppClsDir", QLineEdit(), 0),
            ("txtAppTgRoot", QLineEdit(), 0),
            ("txtAppTgClsDir", QLineEdit(), 0),
            ("txtAppTgJarFile", QLineEdit(), 0),
            ("txtAppSrv", QLineEdit(), 130),
            ("txtAppUser", QLineEdit(), 130),
            ("txtAppPwd", QLineEdit(), 130),
            ("txtAppStartup", QLineEdit(), 0),
            ("txtAppShutdown", QLineEdit(), 0),
            ("btnSave", QPushButton(QIcon('image/checkmark.png'), 'Save'), 0),
            ("btnCancel", QPushButton(QIcon('image/cancel.png'), 'Cancel'), 0),
        ]
        for w in widgets:
            setattr(self, w[0], w[1])
            if w[2] > 0:
                getattr(self, w[0]).setFixedWidth(w[2])
        self.btnAddApp.setToolTip('Add Applicatioin')
        self.btnAddApp.setFixedHeight(25)
        self.btnRemoveApp.setToolTip('Remove Applicatioin')
        self.btnRemoveApp.setFixedHeight(25)
        self.btnCopyApp.setToolTip('Copy Applicatioin')
        self.btnCopyApp.setFixedHeight(25)
        self.txtSvnPwd.setEchoMode(QLineEdit.Password)
        self.txtDiffPwd.setEchoMode(QLineEdit.Password)
        self.txtAppPwd.setEchoMode(QLineEdit.Password)
        self.lstApp.setSizePolicy(
            QSizePolicy.Policy(QSizePolicy.Fixed),
            QSizePolicy.Policy(QSizePolicy.Preferred),
            )
        deg = MyDelegate(self.lstApp, self.invalidHandler)
        self.lstApp.setItemDelegate(deg)
        self.lstApp.setAlternatingRowColors(True)
        self.lstApp.currentItemChanged.connect(self.updateAppInfo)
        #self.lstApp.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.lstApp.itemDoubleClicked.connect(self.lstApp.editItem)


        # ==== Svn Settings ====
        grpSvn = QGroupBox('Svn Settings')
        #lbUsr = IconLabel(QIcon('image/account.png'), 'Username')
        #lbPwd = IconLabel(QIcon('image/key.png'), 'Password')
        grpSvn.setLayout(yGridLayout([
            [ 'Username', self.txtSvnUser, None, ],
            [ 'Password', self.txtSvnPwd, None, ],
            ])
        )
        grpSvn.layout().setColumnStretch(2, 10)
        grpSvn.setSizePolicy(
            QSizePolicy.Policy(QSizePolicy.Fixed),
            QSizePolicy.Policy(QSizePolicy.Preferred),
            )
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
        grpApp = QGroupBox('Webapp Settings')
        grpLc = QGroupBox()
        grpLc.setLayout(yGridLayout([
            [ 'Source Root', (self.txtAppSrcRoot,1,3) ], 
            [ 'Webapp Dir', self.txtAppWebappDir, 'Java Dir', self.txtAppJavaDir ], 
            [ 'Class Dir', self.txtAppClsDir ], 
            ])
        )
        grpTg = QGroupBox()
        grpTg.setLayout(yGridLayout([
            [ 'Target Root', self.txtAppTgRoot ], 
            [ 'Target ClsDir', self.txtAppTgClsDir ],
            [ 'Target Jar', self.txtAppTgJarFile ],
            ])
        )
        grpSrv = QGroupBox()
        grpSrv.setLayout(yGridLayout([
            [ 'Server', self.txtAppSrv ], 
            [ 'Username', self.txtAppUser],
            [ 'Password', self.txtAppPwd ], 
            [ 'Startup', self.txtAppStartup ], 
            [ 'Shutdown', self.txtAppShutdown ], 
            ])
        )
        style = """QGroupBox {
        	/*
        	border:0; border-radius:0;
        	border-top:1px solid dimgray;
        	*/
        	margin:0; padding:0;
        	}"""
        grpLc.setStyleSheet(style)
        grpTg.setStyleSheet(style)
        grpSrv.setStyleSheet(style)

        grpApp.setLayout(
            yBoxLayout([
                [ 'Jar Executable Bin', self.txtJarBin ],
                [ yBoxLayout([
                    [ self.lstApp ],
                    [ self.btnAddApp, self.btnRemoveApp, self.btnCopyApp ],
                  ]),
                  yBoxLayout([
                    [ grpLc ], [ grpTg ], [ grpSrv ]
                  ])
                ],
            ])
        )
        self.btnAddApp.clicked.connect(self.addApp)
        self.btnRemoveApp.clicked.connect(self.removeApp)
        self.btnCopyApp.clicked.connect(self.copyApp)
        # ==== App Settings ====

        self.notification = QLabel()
        self.notification.setStyleSheet('color:red;')
        self.setLayout(yBoxLayout([
            [ grpSvn, grpDiff ],
            [ grpApp ],
            None,
            [ self.notification, None, self.btnSave, self.btnCancel ],
            ])
        )
        self.setFixedSize(670, 600)
        self.setWindowTitle('Settings')
        self.setWindowIcon(QIcon('image/settings.png'))

        self.btnSave.clicked.connect(self.saveAndClose)
        self.btnSave.setFixedSize(80, 28)
        self.btnCancel.clicked.connect(self.cancelAndClose)
        self.btnCancel.setFixedSize(80, 28)

    def invalidHandler(self, msg):
        self.notification.setText(msg)

    def _addApp(self, app):
        item = QListWidgetItem(QIcon('image/item.png'), app)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.lstApp.addItem(item)
        self.lstApp.setCurrentItem(item)
        return item

    def addApp(self):
        prefix = "New Item "
        text = ""
        items = []
        for i in xrange(self.lstApp.count()):
            items.append(self.lstApp.item(i).text())
        i = 1
        while True:
            text = prefix+str(i)
            if text not in items:
            	break
            i += 1

        self.lstApp.editItem(self._addApp(text))

    def removeApp(self):
        self.lstApp.takeItem(self.lstApp.currentRow())

    def copyApp(self):
        app = self.lstApp.currentItem().text() + ' - Copy'
        self._saveapp(app)
        item = self._addApp(app)
        self._loadapp(item.text())

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
        self.txtSvnPwd.setText(decrypt(self.conf('svn', 'password')))
        self.txtDiffSrv.setText(self.conf('diff', 'server'))
        self.txtDiffUser.setText(self.conf('diff', 'username'))
        self.txtDiffPwd.setText(decrypt(self.conf('diff', 'password')))
        self.txtDiffDir.setText(self.conf('diff', 'remote dir'))
        self.txtDiffUrl.setText(self.conf('diff', 'http url'))
        self.txtJarBin.setText(self.conf('app', 'jar bin'))

        self.lstApp.clear()
        for _ in self.conf('app', 'list').split(','):
            v = _.strip()
            item = QListWidgetItem(QIcon('image/item.png'), v)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.lstApp.addItem(item)
        self.lstApp.setCurrentRow(0)

    def _saveapp(self, app):
        self.conf(app, 'source root', self.txtAppSrcRoot.text())
        self.conf(app, 'target root', self.txtAppTgRoot.text())
        self.conf(app, 'webapp dir', self.txtAppWebappDir.text())
        self.conf(app, 'java dir', self.txtAppJavaDir.text())
        self.conf(app, 'class dir', self.txtAppClsDir.text())
        self.conf(app, 'target class dir', self.txtAppTgClsDir.text())
        self.conf(app, 'target jar file', self.txtAppTgJarFile.text())
        self.conf(app, 'server', self.txtAppSrv.text())
        self.conf(app, 'username', self.txtAppUser.text())
        self.conf(app, 'password', encrypt(self.txtAppPwd.text()))
        self.conf(app, 'startup', self.txtAppStartup.text())
        self.conf(app, 'shutdown', self.txtAppShutdown.text())

    def _loadapp(self, app):
        self.txtAppSrcRoot.setText(self.conf(app, 'source root'))
        self.txtAppTgRoot.setText(self.conf(app, 'target root'))
        self.txtAppWebappDir.setText(self.conf(app, 'webapp dir'))
        self.txtAppJavaDir.setText(self.conf(app, 'java dir'))
        self.txtAppClsDir.setText(self.conf(app, 'class dir'))
        self.txtAppTgClsDir.setText(self.conf(app, 'target class dir'))
        self.txtAppTgJarFile.setText(self.conf(app, 'target jar file'))
        self.txtAppSrv.setText(self.conf(app, 'server'))
        self.txtAppUser.setText(self.conf(app, 'username'))
        self.txtAppPwd.setText(decrypt(self.conf(app, 'password')))
        self.txtAppStartup.setText(self.conf(app, 'startup'))
        self.txtAppShutdown.setText(self.conf(app, 'shutdown'))

    def updateAppInfo(self, curr, prev):
        self.notification.setText('')
        if prev:
            self._saveapp(prev.text())
        if curr:
            self._loadapp(curr.text())


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

        self.conf('svn', 'username', self.txtSvnUser.text())
        self.conf('svn', 'password', encrypt(self.txtSvnPwd.text()))
        self.conf('diff', 'server', self.txtDiffSrv.text())
        self.conf('diff', 'username', self.txtDiffUser.text())
        self.conf('diff', 'password', encrypt(self.txtDiffPwd.text()))
        self.conf('diff', 'remote dir', self.txtDiffDir.text())
        self.conf('diff', 'http url', self.txtDiffUrl.text())
        self.conf('app', 'jar bin', self.txtJarBin.text())

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

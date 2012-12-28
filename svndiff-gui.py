#!/usr/bin/env python
# -* coding: utf8 -*-

import sys, os
import re
import time
from PySide.QtCore import *
from PySide.QtGui import *
from yelib.qt.layout import *
from yelib.task import *
import cPickle as pk

from svndiff import SvnDiff

class MainWindow(QDialog):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        #self.setFont(QFont("simsun", 10))
        self.config_file = "settings"
        try:
            self.config = pk.load(open(self.config_file))
        except IOError:
            self.config = {}

        self.lt = yBoxLayout([
            [ ('', QLabel(u'SVN User Name   ')), ('txtUsername', QLineEdit(self.conf('username'))), None ],
            [ ('', QLabel(u'SVN Password    ')), ('txtPassword', QLineEdit(self.conf('password'))), None ],
            [ ('', QLabel(u'SVN command     ')), ('txtSvnCmd', QLineEdit(self.conf('svncmd'))) ],
            [ ('', QLabel(u'Source Root Path')), ('txtSrcDir', QLineEdit(self.conf('srcdir'))) ],
            [ ('', QLabel(u'Bug ID          ')), ('txtBugId', QLineEdit('')), None ],
            [ None, ('btnSaveConfig', QPushButton(u'Save Config')),
                    ('btnGetStatus', QPushButton(u'Get Status')),
                    ('btnMakeDiff', QPushButton(u'Make Diff')),
                    ('btnExit', QPushButton(u'Exit')), None ],
            [ ('lstResult', QListWidget()) ],
            [ ('statusBar', QStatusBar(self)) ],
        ])
        self.sd = SvnDiff(getstatus=False)
        if self.lt.txtSvnCmd.text() == "":
            self.lt.txtSvnCmd.setText(self.sd.svn_cmd.path)

        self.setFixedSize(650, 500)
        self.lt.txtPassword.setEchoMode(QLineEdit.Password)
        #self.lt.lstResult.setMaximumHeight(300)
        #self.pb = QProgressBar(self.lt.statusBar)
        #self.lt.statusBar.addPermanentWidget(self.pb)

        self.setWindowTitle('Svn Diff Tool')
        self.setWindowIcon(QIcon('./logo.png'))
        self.setLayout(self.lt)
        self.lt.btnSaveConfig.clicked.connect(self.save_config)
        self.lt.btnExit.clicked.connect(self.close)

        self.statusIcons = {
                'A': QIcon('fileadd.ico'),
                'M': QIcon('filemodify.ico'),
                'D': QIcon('filedelete.ico'),
                }
        self.init_task()

    def conf(self, key, value=None):
        if value is not None:
            self.config[key] = value
        return self.config.get(key, '')

    def init_task(self):
        self.BackTasks = {
            'btnGetStatus': Task(self.get_status, [self.show_status_result]),
            'btnMakeDiff': Task(self.make_diff, [self.show_diff_result]),
            }

        self.worker = Worker()

        for btn, task in self.BackTasks.items():
            self.worker.add(task)
            self.lt[btn].clicked.connect(task.run)


    def reject(self):
        self.close()

    def closeEvent(self, event):
        self.worker.exit()
        event.accept()

    def save_config(self):
        self.conf('username', self.lt.txtUsername.text())
        self.conf('password', self.lt.txtPassword.text())
        self.conf('svncmd', self.lt.txtSvnCmd.text())
        self.conf('srcdir', self.lt.txtSrcDir.text())
        pk.dump(self.config, open(self.config_file, 'w'))
        pass

    def get_status(self):
        self.lt.btnGetStatus.setDisabled(True)
        yield ('INFO', u"Getting svn status, please wait ...")
        self.sd.set_src_dir(self.lt.txtSrcDir.text()) 
        try:
            self.sd.status()
            for f in self.sd.files:
                yield ('M', self.sd.display_fname(f))
            for f in self.sd.newfiles:
                yield ('A', self.sd.display_fname(f))
            for f in self.sd.removedfiles:
                yield ('D', self.sd.display_fname(f))
            yield ('INFO', u"Getting svn status done") 
        except Exception as ex:
            yield('ERROR', unicode(ex))
        finally:
            self.lt.btnGetStatus.setDisabled(False)

    def make_diff(self):
        self.lt.btnMakeDiff.setDisabled(True)
        try:
            for f in self.sd.files:
                yield u'Making diff for {} ...'.format(self.sd.display_fname(f))
                args = [ "diff", f, "--diff-cmd=diffcmd.exe", "-x", "-u -l10000" ]
                self.sd.gen_diff_file(args, ' '+f)
            yield u'Making diff for All-diffs ...'
            args = [ "diff", self.lt.txtSrcDir.text() ]
            self.sd.gen_diff_file(args, 'All-diffs')
            yield u'Go to hdiff to check files'
        except Exception as ex:
            yield unicode(ex)
        finally:
            self.lt.btnMakeDiff.setDisabled(False)

    def show_status_result(self, n=None, msg=None):
        if n == 0:
            self.lt.lstResult.clear()
        elif n is None:
        	return
        if msg[0] in ('INFO', 'WARN', 'ERROR'):
        	self.update_status(msg[1])
        else:
            item = QListWidgetItem(self.statusIcons[msg[0]], msg[1])
            item.setCheckState(Qt.Checked)
            self.lt.lstResult.addItem(item)

    def show_diff_result(self, n=None, msg=None):
        if n == 0:
            self.lt.lstResult.clear()
        elif n is None:
        	return
        item = QListWidgetItem(msg)
        self.lt.lstResult.addItem(item)

    def update_status(self, msg=''):
        self.lt.statusBar.showMessage(msg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

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
                    ('btnReview', QPushButton(u'Review')),
                    ('btnSubmit', QPushButton(u'Submit')),
                    ('btnExit', QPushButton(u'Exit')), None ],
            [ ('lstResult', QListWidget()) ],
            [ ('statusBar', QStatusBar(self)) ],
        ])
        self.sd = SvnDiff(getstatus=False)
        if self.lt.txtSvnCmd.text() == "":
            self.lt.txtSvnCmd.setText(self.sd.svn_cmd.path)

        self.setFixedSize(500, 500)
        self.lt.txtPassword.setEchoMode(QLineEdit.Password)
        #self.lt.lstResult.setMaximumHeight(300)
        self.pb = QProgressBar(self.lt.statusBar)
        self.lt.statusBar.addPermanentWidget(self.pb)

        self.setWindowTitle('Svn Diff Tool')
        self.setWindowIcon(QIcon('./logo.png'))
        self.setLayout(self.lt)
        self.lt.btnSaveConfig.clicked.connect(self.save_config)
        self.lt.btnExit.clicked.connect(self.close)

        self.init_task()

    def conf(self, key, value=None):
        if value is not None:
        	self.config[key] = value
        return self.config.get(key, '')

    def init_task(self):
        self.BackTasks = {
            'btnReview': {
                'task': Task(self.review_task),
                'subscribers': [self.show_review_result()],
                #'subscribers': [self.update_status()],
                },
            'btnSubmit': {
                'task': Task(self.submit_task),
                'subscribers': [self.update_status()],
                },
            }

        self.worker = Worker()

        for btn, t in self.BackTasks.items():
            task = t['task']
            for s in t['subscribers']:
                sub = Subscriber(s)
                sub.subscribe(task)
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

    def review_task(self):
        self.lt.btnReview.setDisabled(True)
        yield ('INFO', "Getting svn status, please wait ...")
        self.sd.set_src_dir(self.lt.txtSrcDir.text()) 
        try:
            self.sd.status()
            for f in self.sd.files:
        	    yield ('M', f)
            for f in self.sd.newfiles:
        	    yield ('A', f)
            for f in self.sd.removedfiles:
        	    yield ('D', f)
            yield ('INFO', "Getting svn status done") 
        except Exception as ex:
            yield('ERROR', ex)
        finally:
            self.lt.btnReview.setDisabled(False)

    def submit_task(self):
        self.lt['btnSubmit'].setDisabled(True)
        yield "Waiting for submit"
        time.sleep(1)
        yield "Waiting for submit ."
        time.sleep(1)
        yield "Waiting for submit .."
        time.sleep(1)
        yield "Waiting for submit ..."
        time.sleep(1)
        yield "Submit done"
        self.lt['btnSubmit'].setDisabled(False)

    @coroutine
    def show_review_result(self):
        try:
            while True:
                m = (yield)
                if m[0] in ('INFO', 'WARN', 'ERROR'):
                    self.lt.statusBar.showMessage(m[1])
                else:
                    item = QListWidgetItem(m[0] + " " + m[1])
                    item.setCheckState(Qt.Unchecked)
                    self.lt.lstResult.addItem(item)
        except GeneratorExit:
            print "show_handler done"

    @coroutine
    def update_status(self):
        try:
            while True:
                msg = (yield)
                self.lt.statusBar.showMessage(msg)
        except GeneratorExit:
            print "show_handler done"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

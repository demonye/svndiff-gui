#!/usr/bin/env python2
# -* coding: utf8 -*-

import os
import time
from PySide.QtCore import *
from PySide.QtGui import *
from paramiko import SSHClient, AutoAddPolicy
from yelib.qt.layout import *
from yelib.task import *
from yelib.util import force_rmdir
from svndiff import SvnDiff

class DiffTab(QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self)
        self.parent = parent
        self.setFont(QFont("Monospace", 10))
        tb = QTableWidget()
        tb.setColumnCount(5)
        tb.setSelectionBehavior(QAbstractItemView.SelectRows)
        tb.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tb.setHorizontalHeaderLabels(("Check", "Icon", "Status", "File", "FullFile"))
        tb.horizontalHeader().setResizeMode(0, QHeaderView.Fixed)
        tb.horizontalHeader().setResizeMode(1, QHeaderView.Fixed)
        tb.horizontalHeader().setResizeMode(3, QHeaderView.Stretch)
        tb.horizontalHeader().resizeSection(0, 30) 
        tb.horizontalHeader().resizeSection(1, 25) 
        tb.setColumnHidden(2, True)
        tb.setColumnHidden(4, True)
        tb.horizontalHeader().hide()
        tb.verticalHeader().hide()
        tb.setAlternatingRowColors(True)

        self.txtBugId = QLineEdit()
        self.btnFind = QPushButton(u'Find Changed Files')
        self.btnDiff = QPushButton(u'Make Diff')
        self.lstFiles = tb
        self.lt = yBoxLayout([
            [ ('', self.lstFiles) ],
            [ ('', self.btnFind), None,
              ('', QLabel(u'Bug Id')), ('', self.txtBugId),
              ('', self.btnDiff), None
            ],
        ])
        self.setLayout(self.lt)

        self.statusIcons = {
                'A': QIcon('fileadd.ico'),
                'M': QIcon('filemodify.ico'),
                'D': QIcon('filedelete.ico'),
                }
        self.worker = None
        self.sd = SvnDiff(getstatus=False)
        svncmd = self.parent.txtSvnCmd.text()
        if svncmd == "":
            self.parent.txtSvnCmd.setText(self.sd.svn_cmd.path)
        else:
            self.sd.svn_cmd._path = svncmd
        self.sshcli = SSHClient()


    def conf(self, key):
        return self.parent.tab.widget(1).conf(key)

    def init_task(self):
        self.BackTasks = {
            self.btnFind: Task(self.get_status, [self.show_changed_files]),
            self.btnDiff: Task(self.make_diff, [self.show_diff_result]),
            }
        for btn, task in self.BackTasks.items():
            self.worker.add(task)
            btn.clicked.connect(task.run)

#    def reject(self):
#        self.close()
#
    def showEvent(self, event):
        event.accept()
        self.worker = Worker()
        self.init_task()

    def closeEvent(self, event):
        self.worker.exit()
        event.accept()

    def get_status(self):
        self.btnFind.setDisabled(True)
        sd = self.sd
        yield ('INFO', u"Getting svn status, please wait ...")
        self.sd.set_src_dir(self.parent.txtSrcDir.text())
        sd.status()
        for f in sd.files:
            yield ('M', f)
        for f in sd.newfiles:
            yield ('A', f)
        for f in sd.removedfiles:
            yield ('D', f)
        yield ('INFO', u"Getting svn status done") 

    def make_diff(self):
        self.btnDiff.setDisabled(True)
        sd = self.sd
        tb = self.lstFiles
        files = []

        def modify_file(f):
            files.append(f)
            args = [ "diff", f, "--diff-cmd=diff", "-x", "-U10000" ]
            sd.gen_diff_file(args, ' '+f)

        def add_file(f):
            files.append(f)
            in_file = open(f)
            out_html = open(os.path.join(sd.save_dir, ' '+sd.hdiff_fname(f)), 'w')
            out_html.write("<xmp>\n")
            n = 1
            for l in in_file.readlines():
                out_html.write("%5d  %s\n" % (n, l))
                n += 1
            out_html.write("</xmp>\n")
            out_html.close()
            in_file.close()

        def connect():
            host = self.parent.txtSrvHost.text()
            user = self.parent.txtSrvUser.text()
            kwargs = {
                'hostname': host,
                'username': user,
                'timeout': 10,
            }

            if self.parent.rdoPwd.isChecked():
                pwd = self.parent.txtSrvPwd.text()
                kwargs['password'] = pwd
            elif self.parent.rdoKey.isChecked():
                kfile = self.parent.txtKeyFile.text()
                kwargs['key_filename'] = kfile

            self.sshcli.set_missing_host_key_policy(AutoAddPolicy())
            self.sshcli.connect(**kwargs)
            return ('INFO', u'Connected to {}'.format(host))

        def upload(dirname):
            sftpcli = self.sshcli.open_sftp()
            return ('INFO', 'TODO')

        if self.txtBugId.text() == "":
            yield ('WARN', u"Please input bug id!")
            return

        force_rmdir(self.sd.save_dir)
        os.makedirs(self.sd.save_dir)
        for i in xrange(tb.rowCount()):
            item = tb.item(i, 0)
            if item.checkState() == Qt.Checked:
                stat = tb.item(i, 2).text()
                disp_f = tb.item(i, 3).text()
                f = tb.item(i, 4).text()
                if stat == 'M':
                    yield ('INFO', u'Making-diff {} ...'.format(disp_f))
                    modify_file(f)
                elif stat == 'A':
                    yield ('INFO', u'Adding file {} ...'.format(disp_f))
                    add_file(f)
        yield ('INFO', u'Making-diff All-diffs ...')
        args = [ "diff" ] + files
        sd.gen_diff_file(args, 'All-diffs')

        yield ('INFO', u'Connecting to {} ...'.format(self.parent.txtSrvHost.text()))
        yield connect()

        yield ('INFO', u'Uploading diff to {}'.format(self.parent.txtSrvHost.text()))
        yield upload(sd.save_dir)

    def show_changed_files(self, n=None, msg=None):
        tb = self.lstFiles
        if n == 0:
            for i in xrange(tb.rowCount()):
                tb.removeRow(0)
        elif n is None:
            self.btnFind.setDisabled(False)
            return
        if msg[0] in ('INFO', 'WARN', 'ERROR'):
            self.update_status(msg[1])
        else:
            n = tb.rowCount()
            tb.insertRow(n)
            item = QTableWidgetItem()
            item.setCheckState(Qt.Checked)
            tb.setItem(n, 0, item)
            tb.setItem(n, 1,QTableWidgetItem(self.statusIcons[msg[0]], ''))
            tb.setItem(n, 2, QTableWidgetItem(msg[0]))
            tb.setItem(n, 3, QTableWidgetItem(self.sd.display_fname(msg[1])))
            tb.setItem(n, 4, QTableWidgetItem(msg[1]))

    def show_diff_result(self, n=None, msg=None):
        if n is None:
            self.btnDiff.setDisabled(False)
            return
        self.update_status(msg[1])
        if msg[0] == 'WARN':
            QMessageBox.warning(self, u'Warning', msg[1])
        elif msg[0] == 'ERROR':
            QMessageBox.critical(self, u'Error', msg[1])


    def update_status(self, msg=''):
        self.parent.append_log(msg)


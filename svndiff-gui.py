#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys, os
from PySide.QtCore import *
from PySide.QtGui import *
from yelib.qt.layout import *
import cPickle as pk

from DiffTab import DiffTab
from SettingDlg import SettingDlg

__version__ = "1.1"

class MainWindow(QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setFont(QFont("Monospace", 10))

        # ==== Tab Widget ====
        self.tab = QTabWidget()
        self.tabSetting = SettingDlg(self)
        self.tabDiff = DiffTab(self)
        self.tab.addTab(self.tabDiff, u'Make Diff')
        self.tab.addTab(QWidget(), u'Replace Class File')
        self.tab.addTab(self.tabSetting, u'Setting')
        self.tab.setTabEnabled(1, False)
        self.tab.setMinimumSize(700, 350)
        # ==== Tab Widget ====

        # ==== Log ====
        self.grpLog = QGroupBox(u'Log')
        self.txtLog = QTextBrowser()
        self.txtLog.setReadOnly(True)
        self.txtLog.setMinimumHeight(150)
        self.txtLog.setOpenExternalLinks(True)
        self.ltLog = yBoxLayout([
            [ ('', self.txtLog) ]
        ])
        self.grpLog.setLayout(self.ltLog)
        # ==== Log ====

        # ==== Main Layout ====
        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self.tab)
        splitter.addWidget(self.grpLog)
        self.btnExit = QPushButton(u'Exit')
        self.lt = yBoxLayout([
            [ ('', splitter) ],
            [ None, ('', self.btnExit) ],
        ])
        self.btnExit.clicked.connect(self.close)
        self.setLayout(self.lt)
        self.setWindowTitle('Svn Tool')
        self.setWindowIcon(QIcon('logo.png'))
        # ==== Main Layout ====

    def center(self):
        self.move(
            QApplication.desktop().screen().rect().center() -
            self.rect().center() )

    #def reject(self):
    #    self.close()

    def closeEvent(self, event):
        for i in xrange(self.tab.count()):
            self.tab.widget(i).close()
        event.accept()

    def append_log(self, logtext=''):
        #self.txtLog.appendPlainText(logtext)
        self.txtLog.append(logtext) #+"<img src='loading.gif'/>")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    win.center()
    sys.exit(app.exec_())

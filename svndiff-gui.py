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


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__() 

        self.main = MainArea(self)
        self.setCentralWidget(self.main)

        #self.settingAct = QAction(QIcon("menu_bt_settings.png"), "&Setting", self)
        #self.settingToolBar = self.addToolBar("Setting")
        #self.settingToolBar.addAction(self.settingAct)
        self.lbLoadingText = QLabel()
        self.lbLoadingGif = QLabel()
        self.lbLoadingGif.hide()
        movie = QMovie("loading-small.gif")
        movie.start()
        self.lbLoadingGif.setMovie(movie)
        self.statusBar()
        self.statusBar().addWidget(self.lbLoadingText)
        self.statusBar().addWidget(self.lbLoadingGif)
        self.setStyleSheet("QStatusBar::item {border-style:flat;}")
        self.setWindowTitle('Svn Tool')
        self.setWindowIcon(QIcon('logo.png'))

    def center(self):
        self.move(
            QApplication.desktop().screen().rect().center() -
            self.rect().center() )

    def closeEvent(self, event):
        self.main.close()
        event.accept()

    def showLoading(self, msg, loading=True):
        self.lbLoadingText.setText(msg)
        #self.statusBar().showMessage(msg)
        self.lbLoadingGif.setVisible(loading)

class MainArea(QWidget):

    def __init__(self, parent=None):
        super(MainArea, self).__init__(parent)
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
        self.grpLog = QGroupBox(u'Information of Execution')
        self.txtLog = QTextBrowser()
        self.txtLog.setReadOnly(True)
        self.txtLog.setMinimumHeight(150)
        self.txtLog.setOpenExternalLinks(True)
        self.ltLog = yBoxLayout([
            [ ('', self.txtLog) ],
        ])
        self.grpLog.setLayout(self.ltLog)
        # ==== Log ====

        # ==== Main Layout ====
        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self.tab)
        splitter.addWidget(self.grpLog)
        #self.btnExit = QPushButton(u'Exit')
        self.lt = yBoxLayout([
            [ ('', splitter) ],
        ])
        #self.btnExit.clicked.connect(self.close)
        self.setLayout(self.lt)
        self.setStyleSheet("QTextBrowser {border-style:flat;background:lightyellow;}")
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
        self.txtLog.append(logtext)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    win.center()
    sys.exit(app.exec_())

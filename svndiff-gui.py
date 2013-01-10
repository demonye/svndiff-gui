#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys, os
from PySide.QtCore import *
from PySide.QtGui import *
from yelib.qt.layout import *
import cPickle as pk
from tabs import *
from yelib.newtask import TaskWorker

__version__ = "1.1"


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__() 

        self.main = MainArea(self)
        self.setCentralWidget(self.main)

        self.createToolBar()
        self.createStatusBar()

        self.setWindowTitle('Svn Tool')
        self.setWindowIcon(QIcon('logo.png'))

    def createStatusBar(self):
        self.lbLoadingText = QLabel()
        self.lbLoadingGif = QLabel()
        self.lbLoadingGif.hide()
        movie = QMovie("loading-small.gif")
        movie.start()
        self.lbLoadingGif.setMovie(movie)

        self.statusBar()
        self.statusBar().addPermanentWidget(self.lbLoadingText)
        self.statusBar().addPermanentWidget(self.lbLoadingGif)
        self.setStyleSheet("QStatusBar::item {border-style:flat;}")

    def createToolBar(self):
        self.myTb = self.addToolBar("Svn Tool")
        self.myTb.addAction( QAction(
            QIcon('stop-task.png'), "S&top Task", self,
            statusTip="Stop current running task",
            triggered=self.stopCurrentTask) )
        self.myTb.addAction( QAction(
            QIcon('settings.png'), "&Settings", self,
            statusTip="Open Settings Dialog",
            triggered=self.openSettingsDlg) )

    def stopCurrentTask(self):
        TaskWorker().stop_task()

    def openSettingsDlg(self):
        print "openSettingsDlg"

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
        self.tabDiff = DiffTab(self)
        self.tabClass = ClassTab(self)
        self.tabSettings = SettingsTab(self)
        self.tab.addTab(self.tabDiff, u'Make Diff')
        self.tab.addTab(self.tabClass, u'Replace Class File')
        self.tab.addTab(self.tabSettings, u'Settings')
        self.tab.setMinimumSize(700, 400)
        self.tab.currentChanged.connect(self.tab_changed)
        self.tab.setSizePolicy(
            QSizePolicy.Policy(QSizePolicy.Preferred),
            QSizePolicy.Policy(QSizePolicy.Maximum)
            )
        # ==== Tab Widget ====

        # ==== Log ====
        self.grpLog = QGroupBox(u'Information of Execution')
        self.txtLog = QTextBrowser()
        self.txtLog.setReadOnly(True)
        self.txtLog.setMinimumHeight(150)
        self.txtLog.setOpenExternalLinks(True)
        self.ltLog = yBoxLayout([
            [ self.txtLog ],
        ])
        self.grpLog.setLayout(self.ltLog)
        self.tab.setSizePolicy(
            QSizePolicy.Policy(QSizePolicy.Preferred),
            QSizePolicy.Policy(QSizePolicy.Minimum)
            )
        # ==== Log ====
        self.tab.setCurrentIndex(1)

        # ==== Main Layout ====
        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self.tab)
        splitter.addWidget(self.grpLog)
        #self.btnExit = QPushButton(u'Exit')
        self.lt = yBoxLayout([
            [ splitter ],
        ])
        #self.btnExit.clicked.connect(self.close)
        self.setLayout(self.lt)
        self.setStyleSheet("""
        /*
        QLabel {
        	padding:2px;
        	border:1px inset rgb(150,150,150);
        	border-radius:3px;
        	}
        */
        QTabBar::tab, QPushButton {
            padding: 5px;
            /*background: rgb(180,180,180);*/
            border: 1px solid rgb(150,150,150);
            border-radius: 2px;
        }
        QTabBar::tab:hover { background: rgb(150,150,150); }
        QTabBar::tab:selected {
        	background: rgb(130,130,130);
            border: 1px inset rgb(150,150,150);
        }
        QPushButton:hover { background: rgb(150,150,150); }
        QLineEdit, QComboBox, QTableWidget, QTextBrowser, QGroupBox {
            padding: 2px; border-radius: 3px;
        	border:1px solid rgb(150,150,150);
        }
        QGroupBox{ margin-top: 5px; }
        QGroupBox::title { left: 10px; top: -5px; }
        QTabWidget::pane { border:1px solid rgb(150,150,150);} 
        QTableWidget { padding: 0; }
        QHeaderView::section {
            padding: 3px;
        	border: 1px solid rgb(150,150,150);
        }
        QTextBrowser { background:lightyellow; }
        """ )
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

    def tab_changed(self, idx):
        if self.tab.currentWidget() == self.tabSettings:
        	self.grpLog.hide()
        else:
        	self.grpLog.show()
 
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    win.center()
    sys.exit(app.exec_())

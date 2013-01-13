#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys, os
from PySide.QtCore import *
from PySide.QtGui import *
from yelib.qt.layout import *
from yelib.newtask import TaskWorker
from SettingsDlg import SettingsDlg

__version__ = "1.1"


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__() 

        self.setFont(QFont("Monospace", 10))
        self.dlgSettings = SettingsDlg(self)
        self.dlgSettings.load()
        self.main = MainArea(self)
        self.setCentralWidget(self.main)
        #for i in xrange(self.main.tab.count()):
        #    w = self.main.tab.widget(i)
        #    w.init(self.dlgSettings)

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
        self.statusBar().addPermanentWidget(self.lbLoadingGif)
        self.statusBar().addPermanentWidget(self.lbLoadingText)
        self.setStyleSheet("QStatusBar::item {border-style:flat;}")

    def createToolBar(self):
        self.myTb = self.addToolBar("Svn Tool")
        self.myTb.addAction( QAction(
            QIcon('image/computer.png'), "Open Settings Dialog", self,
            # statusTip="Open Settings Dialog",
            triggered=self.openSettingsTab) )
        self.myTb.addAction( QAction(
            QIcon('image/stop-task.png'), "Stop Current Running Task", self,
            # statusTip="Stop current running task",
            triggered=self.stopCurrentTask) )

    def stopCurrentTask(self):
        TaskWorker().stop_task()

    def openSettingsTab(self):
        self.dlgSettings.show()

    def center(self):
        self.move(
            QApplication.desktop().screen().rect().center() -
            self.rect().center() )

    def closeEvent(self, event):
        #self.dlgSettings.saveConfig()
        self.main.close()
        event.accept()

    def showLoading(self, msg, loading=True):
        self.lbLoadingText.setText(msg)
        #self.statusBar().showMessage(msg)
        self.lbLoadingGif.setVisible(loading)

    def notifyConfigChanged(self):
        self.main.updateAppList()

class MainArea(QWidget):

    def __init__(self, parent=None):
        super(MainArea, self).__init__(parent)

        self.setFont(QFont("Monospace", 10))
        self.settings = parent.dlgSettings

        # ==== File List ====
        # Application Combo
        self.cboApp = QComboBox()
        self.cboApp.activated.connect(self.selectApp)
        self.txtSrcDir = QLineEdit()
        self.txtSrcDir.setReadOnly(True)
        self.txtSrcDir.setMinimumWidth(350)

        # Main Group
        self.grpMain = QGroupBox('Work Area')
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
        self.lstFiles = tb
        ltMain = yBoxLayout([
            [ 'App', self.cboApp, None, 'Source Dir', self.txtSrcDir ],
            [ self.lstFiles ],
        ])
        self.grpMain.setLayout(ltMain)
        self.grpMain.setMinimumSize(700, 400)
        # ==== Main ====

        # ==== Log ====
        self.grpLog = QGroupBox(u'Information of Execution')
        self.txtLog = QTextBrowser()
        self.txtLog.setReadOnly(True)
        self.txtLog.setMinimumHeight(150)
        self.txtLog.setOpenExternalLinks(True)
        ltLog = yBoxLayout([
            [ self.txtLog ],
        ])
        self.grpLog.setLayout(ltLog)
        self.grpLog.setSizePolicy(
            QSizePolicy.Policy(QSizePolicy.Preferred),
            QSizePolicy.Policy(QSizePolicy.Fixed),
            )
        # ==== Log ====

        # ==== Buttons ====
        #self.grpAction = QGroupBox()
        self.btnGetStatus = QPushButton(QIcon('image/getstatus.png'), u'Get Status')
        self.btnGetStatus.setFixedSize(110, 30)
        self.btnMakeDiff = QPushButton(QIcon('image/makediff.png'), u'Make Diff')
        self.btnMakeDiff.setFixedSize(110, 30)
        self.btnDeployCls = QPushButton(QIcon('image/deployclass.png'), u'Deploy Class')
        self.btnDeployCls.setFixedSize(110, 30)
        #self.grpAction.setLayout(yBoxLayout([
        #    [ None, self.btnGetStatus, self.btnMakeDiff, self.btnDeployCls ]
        #    ])
        #)
        # ==== Buttons ====

        # ==== Main Layout ====
        #self.btnExit = QPushButton(u'Exit')
        lt = yBoxLayout([
            [ self.grpMain ],
            [ None, self.btnGetStatus, self.btnMakeDiff, self.btnDeployCls ],
            [ self.grpLog ],
        ])
        #self.btnExit.clicked.connect(self.close)
        self.setLayout(lt)
        self.updateAppList()
        # ==== Main Layout ====

        if True:
            self.setStyleSheet("""
            /*QTabBar::tab, */
            QPushButton {
                padding: 5px;
                /*background: rgb(180,180,180);*/
                border: 1px solid rgb(150,150,150);
                border-radius: 2px;
            }
            QPushButton:hover { background: rgb(150,150,150); }
            /*
            QTabBar::tab:hover { background: rgb(150,150,150); }
            QTabBar::tab:selected {
                color: rgb(220,220,220);
                background: rgb(130,130,130);
                border: 1px inset rgb(150,150,150);
            }
            QTabWidget::pane { border:1px solid rgb(150,150,150);}
            */
            QLineEdit, QComboBox, QTableWidget, QGroupBox {
                padding: 2px; border-radius: 3px;
                border:1px solid rgb(150,150,150);
            }
            QGroupBox{ margin-top: 5px; }
            QGroupBox::title { left: 10px; top: -5px; }
            QTableWidget { padding: 0; }
            QHeaderView::section {
                padding: 3px;
                border: 1px solid rgb(150,150,150);
            }
            QTextBrowser {
                color: white;
                /* background:lightyellow; */
                background: rgb(50,50,50);
                padding: 5px; border: 0;
            }
            """ )

    def selectApp(self, idx):
        sect = self.cboApp.itemText(idx)
        srcdir = self.settings.conf(sect, 'source dir')
        self.txtSrcDir.setText(srcdir)


    def updateAppList(self):
        applist = self.settings.conf('app', 'list').split(',')
        self.cboApp.clear()
        for app in applist:
            self.cboApp.addItem(QIcon('image/application.png'), app.strip())
        if self.cboApp.count() > 0:
            self.selectApp(0)

    def closeEvent(self, event):
        #for i in xrange(self.tab.count()):
        #    self.tab.widget(i).close()
        event.accept()

    def appendLog(self, logtext=''):
        self.txtLog.append(logtext)

 
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    win.center()
    sys.exit(app.exec_())

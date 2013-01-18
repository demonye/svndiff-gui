#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys, os
from PySide.QtCore import *
from PySide.QtGui import *
from paramiko import SSHClient, AutoAddPolicy

from yelib.qt.layout import *
from yelib.newtask import *
from tabs.BaseTab import BaseTab, IconLabel

from SettingsDlg import SettingsDlg
from MainArea import MainArea

__version__ = "1.1"

STYLE_SHEET = """
/*
QTabBar::tab,
*/
QPushButton {
    border: 1px outset rgb(150,150,150);
    border-radius: 3px;
}
QPushButton:hover {
	border: 1.5px outset dimgray;
    background: rgb(150,150,150);
}
/*
QTabBar::tab:hover { background: rgb(150,150,150); }
QTabBar::tab:selected {
    color: rgb(220,220,220);
    background: rgb(130,130,130);
    border: 1px inset rgb(150,150,150);
}
QTabWidget::pane { border:1px solid rgb(150,150,150);}
*/
QStatusBar::item { border:0; }
QLineEdit, QTextEdit, QComboBox,
QListWidget, QTableWidget, QGroupBox {
    padding: 2px; border-radius: 3px;
    border:1px solid rgb(150,150,150);
}
QLineEdit:focus, QTextEdit:focus {
    border:1.5px solid goldenrod;
}
QGroupBox{ margin-top: 5px; }
QGroupBox::title { left: 10px; top: -5px; }
QListWidget, QTableWidget { padding: 0; }
QListWidget::item { margin:2px; }
QListWidget::item QLineEdit:focus { border:0; border-radius:0; margin:0; padding:0; }
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
IconLabel { border:0; }
/*
IconLabel:hover { background:none; }
*/
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__() 

        self.setFont(QFont("Monospace", 10))
        self.dlgSettings = SettingsDlg(self)
        self.dlgSettings.setModal(True)
        self.dlgSettings.load()
        self.main = MainArea(self)
        self.setCentralWidget(self.main)

        self.createToolBar()
        self.createStatusBar()

        self.setWindowTitle('Svn Tool')
        self.setWindowIcon(QIcon('image/logo.png'))
        self.setStyleSheet(STYLE_SHEET)

    def createStatusBar(self):
        self.lbLoadingText = QLabel()
        self.lbLoadingGif = QLabel()
        self.lbLoadingGif.hide()
        movie = QMovie("loading8.gif")
        movie.start()
        self.lbLoadingGif.setMovie(movie)

        self.statusBar()
        self.statusBar().addWidget(self.lbLoadingText)
        self.statusBar().addWidget(self.lbLoadingGif)

    def createToolBar(self):
        self.myTb = self.addToolBar("Svn Tool")
        self.myTb.addAction( QAction(
            QIcon('image/computer.png'), "Open Settings Dialog", self,
            statusTip="Open Settings Dialog",
            triggered=self.openSettingsTab) )
        self.myTb.addAction( QAction(
            QIcon('image/stop.png'), "Stop Current Running Task", self,
            statusTip="Stop Current Running Task",
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

 
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    win.center()
    sys.exit(app.exec_())

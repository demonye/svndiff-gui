#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
from PySide.QtCore import *
from PySide.QtGui import *

class MainWindow(QDialog):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setFont(QFont("Monospace", 10))

        # ==== Main Layout ====
        tb = QTableWidget()
        tb.setColumnCount(2)
        tb.setHorizontalHeaderLabels(("Icon", "String"))
        tb.insertRow(0)
        tb.setItem(0, 0, QTableWidgetItem(QIcon('fileadd.ico'), 'icon'))
        tb.setItem(0, 1, QTableWidgetItem(u'Something'))
        self.tb = tb

        self.txt = QTextBrowser()
        self.lt = QVBoxLayout()
        self.lt.addWidget(self.tb)
        self.lt.addWidget(self.txt)
        self.setLayout(self.lt)
        self.setWindowTitle('Excute Command')
        # ==== Main Layout ====

        self.txt.setOpenExternalLinks(True)
        self.txt.anchorClicked.connect(self.open_link)
        html = [
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "something",
            "<a href='D:/yehq'><img src='loading.gif'/></a>",
            #"<a href='http://192.168.22.18'><img src='loading.gif'/></a>",
        ]
        for t in html:
        	self.txt.append(t)

    def open_link(self, url):
        print url.toEncoded()
        pos = self.txt.verticalScrollBar().value()
        self.txt.reload()
        self.txt.verticalScrollBar().setValue(pos)

    def reject(self):
        self.close()

    def closeEvent(self, event):
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

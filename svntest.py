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

        self.lt = QHBoxLayout()
        self.lt.addWidget(self.tb)
        self.setLayout(self.lt)
        self.setWindowTitle('Excute Command')
        # ==== Main Layout ====

    def reject(self):
        self.close()

    def closeEvent(self, event):
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

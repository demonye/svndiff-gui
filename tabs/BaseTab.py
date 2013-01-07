# -* coding: utf-8 -*-

from PySide.QtCore import *
from PySide.QtGui import *
from yelib.qt.layout import *
from yelib.util import singleton
from yelib.task import OutputType
import locale

class BaseTab(QWidget):

    settings = None

    def __init__(self, parent=None):
        super(BaseTab, self).__init__(parent)
        self.parent = parent
        #self.setting = parent.tabSettings
        self.setFont(QFont("Monospace", 10))
        self.coding = locale.getdefaultlocale()[1]

    def showLoading(self, msg, loading=True):
        self.parent.parent().showLoading(msg, loading)

    def appendLog(self, log):
        if log.type == OutputType.NOTIFY:
            return
        pt = self.parent
        if log.type == OutputType.OUTPUT:
            pt.append_log(log.output.decode(self.coding))
        else:
            pt.append_log(log.formatted_html())


import sys
from PySide.QtCore import *
from PySide.QtGui import *

class yLayout(QLayout):
    _align = {
        'r' : Qt.AlignRight,
        'l' : Qt.AlignLeft,
        'c' : Qt.AlignCenter,
        't' : Qt.AlignTop,
        'b' : Qt.AlignBottom,
        'hc': Qt.AlignHCenter,
        'vc': Qt.AlignVCenter,
        'j' : Qt.AlignJustify,
    }

    def init(self, data):
        self._data = data
        self._create()

    def align(self, al=None):
        return self._align.get(al, 0)

    def _create(self):
        pass

    def _add(self, lt, item, *args, **kwargs):
        if isinstance(item, QLayout):
            lt.addLayout(item, *args, **kwargs)
        elif isinstance(item, str):
            lt.addWidget(QLabel(item), *args, **kwargs)
        else:
            lt.addWidget(item, *args, **kwargs)

# =======================================
# Stop setting name for widget, you could and should find these widgets by yourself
# The target of the class is for set layout, not for retrieving
    #def __getitem__(self, key):
    #    return eval("self."+key)
    #def _add(self, lt, name, item, *args, **kwargs):
    #    if isinstance(item, QLayout):
    #        lt.addLayout(item, *args, **kwargs)
    #    else:
    #        lt.addWidget(item, *args, **kwargs)
    #    if name != None and len(name) > 0:
    #        setattr(self, name, item)
# =======================================


class yGridLayout(QGridLayout, yLayout):

    def __init__(self, data=None, parent=None):
        super(yGridLayout, self).__init__(parent)
        self.init(data)

    def _create(self):
        super(yGridLayout, self)._create()

        for i in xrange(len(self._data)):
            row = self._data[i]
            for j in xrange(len(row)):
                cell = row[j]
                if cell is None:
                    continue
                rowspan, colspan, align = 1, 1, None
                if type(cell) == tuple:
                    item = cell[0]
                    if len(cell) > 1: rowspan = cell[1]
                    if len(cell) > 2: colspan = cell[2]
                    if len(cell) > 3: align = cell[3]
                else:
                    item = cell
                self._add(self, item, i, j, rowspan, colspan, self.align(align))


class yBoxLayout(QVBoxLayout, yLayout):

    def __init__(self, data=None, parent=None):
        super(yBoxLayout, self).__init__(parent)
        self.init(data)

    def _create(self):
        super(yBoxLayout, self)._create()

        for row in self._data:
            if row is None:
                self.addStretch()
                continue
            lt = QHBoxLayout()
            for cell in row:
                if cell is None:
                    lt.addStretch()
                    continue
                align = None
                if type(cell) == tuple:
                    item = cell[0]
                    if len(cell) > 1: align = cell[1]
                else:
                    item = cell
                self._add(lt, item, alignment=self.align(align))

            self.addLayout(lt)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ltForm = yGridLayout([
        [ ('', QLabel('Name'),1,1,'r'), ('txtName', QLineEdit(), 1, 3) ],
        [ ('', QLabel('Gender'),1,1,'r'), ('txtGender', QLineEdit()),
          ('', QLabel('Age'),1,1,'r'), ('txtAge', QLineEdit())
        ],
    ])
    ltMain = yBoxLayout([
        [ ('ltForm', ltForm) ],
        [ None,
            ('btnSubmit', QPushButton('Submit')),
            ('btnExit', QPushButton('Exit')),
          None
        ],
    ])

    dlg = QDialog()
    dlg.setLayout(ltMain)
    dlg.show()
    sys.exit(app.exec_())

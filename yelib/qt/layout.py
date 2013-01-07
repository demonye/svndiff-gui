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

    def __getitem__(self, key):
        return eval("self."+key)

    def align(self, al=None):
        return self._align.get(al, 0)

    def _create(self):
        pass

    def _add(self, lt, name, item, *args, **kwargs):
        if isinstance(item, QLayout):
            lt.addLayout(item, *args, **kwargs)
        else:
            lt.addWidget(item, *args, **kwargs)
        if name != None and len(name) > 0:
            setattr(self, name, item)


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
                (name, item) = cell[0:2]
                (rowspan, colspan, align) = (
                    cell[2] if len(cell)>2 else 1,
                    cell[3] if len(cell)>3 else 1,
                    cell[4] if len(cell)>4 else None,
                )
                self._add(self, name, item, i, j,
                        rowspan, colspan,
                        self.align(align))


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
                (n, m) = cell[0:2]
                a = cell[2] if len(cell)>2 else None
                self._add(lt, n, m, alignment=self.align(a))

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

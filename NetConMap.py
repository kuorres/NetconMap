
from PyQt5 import QtWidgets
from Logic import NetConMap


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication([])
    widget = NetConMap()
    widget.show()

    sys.exit(app.exec_())
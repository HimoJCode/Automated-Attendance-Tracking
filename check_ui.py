import sys
from PyQt5 import QtWidgets, uic

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    # Load the .ui file (change this to your actual path)
    window = uic.loadUi("ui/unrecognizeModule.ui")  # Example: mainwindow.ui
    window.show()

    sys.exit(app.exec_())

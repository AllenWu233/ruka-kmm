import sys
from PyQt6 import QtWidgets
from .ui.main_window import Ui_MainWindow
import os


def main():
    # Read qt6ct theme
    system_plugin_path = "/usr/lib/qt6/plugins"
    if os.path.exists(system_plugin_path):
        os.environ["QT_PLUGIN_PATH"] = system_plugin_path

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

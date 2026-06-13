import sys
import os
from pathlib import Path
from PyQt6 import QtWidgets, QtGui

from ruka_kmm.ui.main_window import Ui_MainWindow
from ruka_kmm.mod_manager import ModManager


def set_qt6ct_path() -> None:
    """Read qt6ct theme"""
    system_plugin_path = "/usr/lib/qt6/plugins"
    if os.path.exists(system_plugin_path):
        os.environ["QT_PLUGIN_PATH"] = system_plugin_path


def main_window():
    set_qt6ct_path()

    app = QtWidgets.QApplication(sys.argv)

    icon_path = Path(__file__).parent / "resources" / "img" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QtGui.QIcon(str(icon_path)))

    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())


def main():
    set_qt6ct_path()

    mod_list_json_path = Path("~/.config/ruka-kmm/ruka-kmm-mod-list.json")
    game_path = Path("/games/SteamLibrary/steamapps/common/Kenshi")
    workshop_mods_path = Path("/games/SteamLibrary/steamapps/workshop/content/233860")

    main_window()


if __name__ == "__main__":
    main()

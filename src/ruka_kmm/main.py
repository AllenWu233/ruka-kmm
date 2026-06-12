import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from ruka_kmm.mod_manager import ModManager
from ruka_kmm.window import MainWindow


def main():

    # Read qt6ct theme
    system_plugin_path = "/usr/lib/qt6/plugins"
    if os.path.exists(system_plugin_path):
        os.environ["QT_PLUGIN_PATH"] = system_plugin_path

    app = QApplication(sys.argv)
    # app.setStyle('Fusion')

    ruka_json = Path.home() / ".config/ruka-kmm/ruka-kmm-mod-list.json"
    game_root = Path("/games/SteamLibrary/steamapps/common/Kenshi")
    workshop = Path("/games/SteamLibrary/steamapps/workshop/content/233860")

    ruka_json.parent.mkdir(parents=True, exist_ok=True)

    mod_manager = ModManager(ruka_json, game_root, workshop)
    window = MainWindow(mod_manager)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

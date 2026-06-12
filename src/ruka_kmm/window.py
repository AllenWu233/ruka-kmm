from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QFileDialog,
    QListWidgetItem,
    QListWidget,
    QAbstractItemView,
)
from PyQt6.QtCore import Qt
from ruka_kmm.ui.main_window import Ui_MainWindow
from ruka_kmm.mod_manager import ModManager


class MainWindow(QMainWindow):
    def __init__(self, mod_manager: ModManager, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Hide the uncategorizedMods list (we only use categorizedMods)
        # self.ui.uncategorizedMods.setVisible(False)

        # Configure categorizedMods: checkboxes + drag reorder
        self.ui.categorizedMods.setDragDropMode(
            QAbstractItemView.DragDropMode.InternalMove
        )
        self.ui.categorizedMods.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )

        self.mod_manager = mod_manager
        self._connect_signals()
        self.refresh_mods_list()

    def _connect_signals(self):
        self.ui.refresh.clicked.connect(self.refresh_mods_list)
        self.ui.save.clicked.connect(self.save_mods)
        self.ui.run.clicked.connect(self.run_game)
        self.ui.actionImport_mod_list.triggered.connect(self.import_json_list)
        self.ui.actionExport_mod_list.triggered.connect(self.export_json_list)

    def refresh_mods_list(self):
        """Load all mods into categorizedMods with checkboxes reflecting enabled state"""
        self.mod_manager._sync_with_json(
            self.mod_manager.json_mod_list, overwrite=False
        )
        all_mods = self.mod_manager.mods

        self.ui.categorizedMods.clear()
        for mod in all_mods:
            item = QListWidgetItem(mod.mod)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if mod.enabled else Qt.CheckState.Unchecked
            )
            self.ui.categorizedMods.addItem(item)

    def save_mods(self):
        """Save order and checkbox states from categorizedMods to ModManager"""
        ordered_names = []
        enabled_names = set()
        for i in range(self.ui.categorizedMods.count()):
            item = self.ui.categorizedMods.item(i)
            text = item.text()
            ordered_names.append(text)
            if item.checkState() == Qt.CheckState.Checked:
                enabled_names.add(text)

        mod_dict = {mod.mod: mod for mod in self.mod_manager.mods}
        new_mods = []
        for name in ordered_names:
            if name in mod_dict:
                mod = mod_dict.pop(name)
                mod.enabled = name in enabled_names
                new_mods.append(mod)
        new_mods.extend(mod_dict.values())

        self.mod_manager.mods = new_mods
        try:
            self.mod_manager.save_and_apply_mods()
            QMessageBox.information(self, "Save", "Mod list saved and applied.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Save failed: {e}")

    def run_game(self):
        game_exe = self.mod_manager.game_path / "kenshi.x64"
        if not game_exe.exists():
            game_exe = self.mod_manager.game_path / "Kenshi.exe"
        if not game_exe.exists():
            QMessageBox.warning(self, "Run", "Game executable not found.")
            return
        import subprocess

        subprocess.Popen([str(game_exe)], cwd=str(self.mod_manager.game_path))

    def import_json_list(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import JSON", "", "JSON (*.json)")
        if path:
            self.mod_manager.import_json_mod_list(Path(path))
            self.refresh_mods_list()

    def export_json_list(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export JSON", "mod_list.json", "JSON (*.json)"
        )
        if path:
            self.mod_manager.export_json_mod_list(Path(path))

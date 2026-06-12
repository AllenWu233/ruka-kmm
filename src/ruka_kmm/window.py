from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QFileDialog,
    QListWidgetItem,
    QAbstractItemView,
    QGraphicsColorizeEffect,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

from .ui.main_window import Ui_MainWindow
from .mod_manager import ModManager
from .utils import timestamp_str


class MainWindow(QMainWindow):
    def __init__(self, mod_manager: ModManager, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Initialize timer for save button blinking at 0.5s intervals
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self._toggle_save_button_color)
        self.is_blink_state = False

        # Create a hard-flash white colorize effect with maximum strength
        self.flash_effect = QGraphicsColorizeEffect(self)
        self.flash_effect.setColor(QColor("white"))
        self.flash_effect.setStrength(0.2)
        self.flash_effect.setEnabled(False)
        self.ui.save.setGraphicsEffect(self.flash_effect)

        # Configure drag and drop properties
        for lst in (self.ui.uncategorizedMods, self.ui.categorizedMods):
            lst.setDragEnabled(True)
            lst.setAcceptDrops(True)
            lst.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
            lst.setDefaultDropAction(Qt.DropAction.MoveAction)
            lst.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

            # Enable autoscroll when mouse is near top or bottom margins
            lst.setAutoScroll(True)
            lst.setAutoScrollMargin(20)

            # Hijack drop and drag move events to support custom blink and fix scrolling
            lst.dropEvent = lambda event, widget=lst: self._handle_list_drop(
                event, widget
            )
            lst.dragMoveEvent = lambda event, widget=lst: type(widget).dragMoveEvent(
                widget, event
            )

        self.mod_manager = mod_manager
        self._connect_signals()
        self.refresh_mods_list()

    def _handle_list_drop(self, event, widget):
        """Execute standard drop event and trigger blink"""
        type(widget).dropEvent(widget, event)
        self.start_blinking()

    def _connect_signals(self):
        """Connect buttons and menu actions"""
        self.ui.refresh.clicked.connect(self.refresh_mods_list)
        self.ui.save.clicked.connect(self.save_mods)
        self.ui.run.clicked.connect(self.run_game)

        self.ui.actionImport_mod_list.triggered.connect(self.import_json_list)
        self.ui.actionExport_mod_list.triggered.connect(self.export_json_list)

    def start_blinking(self):
        """Start the bright flash effect with 0.5s frequency"""
        if not self.blink_timer.isActive():
            self.blink_timer.start(500)

    def stop_blinking(self):
        """Stop blinking and completely disable the effect"""
        self.blink_timer.stop()
        self.flash_effect.setEnabled(False)
        self.is_blink_state = False

    def _toggle_save_button_color(self):
        """Toggle the graphics effect directly to prevent any size modifications"""
        self.is_blink_state = not self.is_blink_state
        self.flash_effect.setEnabled(self.is_blink_state)

    def _create_mod_item(self, mod_name: str, is_enabled: bool) -> QListWidgetItem:
        """Create a checkable and draggable list item"""
        item = QListWidgetItem(mod_name)
        flags = (
            item.flags()
            | Qt.ItemFlag.ItemIsUserCheckable
            | Qt.ItemFlag.ItemIsDragEnabled
        )
        if flags & Qt.ItemFlag.ItemIsDropEnabled:
            flags ^= Qt.ItemFlag.ItemIsDropEnabled

        item.setFlags(flags)
        item.setCheckState(
            Qt.CheckState.Checked if is_enabled else Qt.CheckState.Unchecked
        )
        return item

    def refresh_mods_list(self):
        """Load mods into lists and stop blinking"""
        self.mod_manager._sync_with_json()
        all_mods = self.mod_manager.categories

        self.ui.uncategorizedMods.clear()
        self.ui.categorizedMods.clear()

        for mod in all_mods:
            item = self._create_mod_item(mod.mod, mod.enabled)
            self.ui.uncategorizedMods.addItem(item)

        self.stop_blinking()

    def save_mods(self):
        """Collect and save mod data, then stop blinking instantly"""
        ordered_names = []
        enabled_names = set()

        for lst in (self.ui.uncategorizedMods, self.ui.categorizedMods):
            for i in range(lst.count()):
                item = lst.item(i)
                if item is not None:
                    text = item.text()
                    ordered_names.append(text)
                    if item.checkState() == Qt.CheckState.Checked:
                        enabled_names.add(text)

        mod_dict = {mod.mod: mod for mod in self.mod_manager.categories}
        new_mods = []

        for name in ordered_names:
            if name in mod_dict:
                mod = mod_dict.pop(name)
                mod.enabled = name in enabled_names
                new_mods.append(mod)

        new_mods.extend(mod_dict.values())
        self.mod_manager.categories = new_mods

        try:
            self.mod_manager.save_and_apply_mods()
            self.stop_blinking()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Save failed: {e}")

    def run_game(self):
        """Execute the game process"""
        game_exe = self.mod_manager.game_path / "kenshi.x64"
        if not game_exe.exists():
            game_exe = self.mod_manager.game_path / "Kenshi.exe"
        if not game_exe.exists():
            QMessageBox.warning(self, "Run", "Game executable not found.")
            return
        import subprocess

        subprocess.Popen([str(game_exe)], cwd=str(self.mod_manager.game_path))

    def import_json_list(self):
        """Open file dialog to import json mod list"""
        path, _ = QFileDialog.getOpenFileName(self, "Import JSON", "", "JSON (*.json)")
        if path:
            self.mod_manager.import_json_mod_list(Path(path))
            self.refresh_mods_list()

    def export_json_list(self):
        """Open file dialog to export current mod list"""
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export JSON",
            f"ruka_kmm_mod_list-{timestamp_str()}.json",
            "JSON (*.json)",
        )
        if path:
            self.mod_manager.export_json_mod_list(Path(path))

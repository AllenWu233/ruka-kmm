import configparser
from dataclasses import dataclass
from pathlib import Path

from . import const
from .mod import Mod, ModSource
from .utils import add_suffix, copy_file


@dataclass
class Category:
    """Mod category"""

    title: str
    desc: str
    mods: list[Mod]


class ModManager:
    """Read, sort and save mod list via configuration"""

    def __init__(
        self, mod_list_path: Path, game_path: Path, workshop_mods_path: Path
    ) -> None:
        self.mod_list_path: Path = mod_list_path  # Ruka KMM mod list (.ini)
        self.game_path: Path = game_path  # Kenshi game root
        self.game_mods_path: Path = game_path / "mods"  # Mods in Kenshi game root
        self.workshop_mods_path: Path = workshop_mods_path
        self.mods_cfg_path: Path = (
            game_path / "data" / "mods.cfg"
        )  # Active list of Kenshi mod list
        self.categories: list[Category] = []  # All the mods saved in categories

        self._init_empty_categories()
        self._create_mod_list_if_missing()
        self._sync_with_mod_list(self.mod_list_path, False)

    def _init_empty_categories(self) -> None:
        """Initialize default empty mod categories"""
        self.categories = [
            Category(title, desc, []) for title, desc in const.category_intros
        ]

    def _scan_mods_from_path(self, mods_path: Path, source: ModSource) -> list[Mod]:
        """Scan all the mods from ``mods_path``"""
        if not mods_path.exists():
            raise FileNotFoundError(f"{source} mods path does not exist: {mods_path}")

        if not mods_path.is_dir():
            raise NotADirectoryError(
                f"{source} mods path is not a directory: {mods_path}"
            )

        mods = []
        for path in mods_path.iterdir():
            if not path.is_dir():
                continue
            try:
                mod = Mod.from_path(path, source)
                mods.append(mod)
            except FileNotFoundError:
                pass
        return mods

    def _scan_all_mods(self) -> list[Mod]:
        """Scan all the mods from local and Steam Workshop mods path"""
        game_root_mods = self._scan_mods_from_path(
            self.game_mods_path, ModSource.GAME_ROOT
        )
        workshop_mods = self._scan_mods_from_path(
            self.workshop_mods_path, ModSource.WORKSHOP
        )
        return game_root_mods + workshop_mods

    def _get_active_mod_names(self, mods_cfg_path: Path | None = None) -> list[str]:
        """Read active mod names from ``<kenshi_game_root>/data/mod.cfg`` as default"""
        if mods_cfg_path is None:
            mods_cfg_path = self.mods_cfg_path

        if not mods_cfg_path.exists():
            return []

        content = mods_cfg_path.read_text(encoding="utf-8")
        return [
            line.removesuffix(".mod") for line in content.splitlines() if line.strip()
        ]

    @staticmethod
    def _save_mod_list(dst: Path, data: dict) -> None:
        """Serialize nested dict to INI with a perfectly compact, space-optimized layout"""
        config = configparser.ConfigParser(allow_no_value=False)
        # Prevent ``configparser`` from forcing all option keys to lowercase
        config.optionxform = str  # type: ignore

        for section, content in data.items():
            config[section] = content

        dst.parent.mkdir(parents=True, exist_ok=True)
        with dst.open("w", encoding="utf-8") as f:
            f.write(const.mod_list_header)
            config.write(f)

    def _create_mod_list_if_missing(
        self, force_apply: bool = False, mods_cfg_path: Path | None = None
    ) -> None:
        """Create initial config file using natively nested dictionary hierarchies"""
        if self.mod_list_path.exists() and not force_apply:
            return

        all_mod_names = [mod.mod for mod in self._scan_all_mods()]

        active_mod_names = self._get_active_mod_names(mods_cfg_path=mods_cfg_path)
        active_set = set(active_mod_names)

        inactive_mod_names = [mod for mod in all_mod_names if mod not in active_set]

        config_data = {title: {"_desc": desc} for title, desc in const.category_intros}
        uncat_title = const.category_intros[-1][0]

        for mod in active_mod_names:
            config_data[uncat_title][mod] = "true"
        for mod in inactive_mod_names:
            config_data[uncat_title][mod] = "false"

        self._save_mod_list(self.mod_list_path, config_data)

    def _read_mod_list(self, path: Path | None = None) -> dict:
        """Read config file straight into standard mapping dictionaries"""
        if path is None:
            path = self.mod_list_path

        if not path.exists():
            raise FileNotFoundError(f"{path} not found.")

        config = configparser.ConfigParser()
        config.optionxform = str  # type: ignore
        config.read(path, encoding="utf-8")

        return {section: dict(config.items(section)) for section in config.sections()}

    def _write_mod_cfg(self, categories: list[Category]) -> None:
        """Write mod list to ``mods.cfg``"""
        if self.mods_cfg_path.exists():
            copy_file(self.mods_cfg_path, add_suffix(self.mods_cfg_path, ".bak"))

        lines = [
            f"{mod.mod}.mod"
            for category in categories
            for mod in category.mods
            if mod.active
        ]
        content = "\n".join(lines)
        self.mods_cfg_path.write_text(content, encoding="utf-8")

    def _sync_with_mod_list(
        self, path: Path | None = None, overwrite: bool = False
    ) -> None:
        """Update ``self.categories`` smoothly from true parsed parent configuration data objects"""
        actual_path = path if path is not None else self.mod_list_path
        try:
            config_data = self._read_mod_list(path)
        except (FileNotFoundError, configparser.Error, PermissionError) as e:
            raise ValueError(
                f"Failed to parse mod list: {actual_path} is missing, broken or invalid."
            ) from e

        mod_objects = {mod.mod: mod for mod in self._scan_all_mods()}
        new_categories = []

        active_mods = set(self._get_active_mod_names())

        for cat_title, cat_content in config_data.items():
            new_categories.append(
                Category(
                    title=cat_title,
                    desc=cat_content.pop("_desc", ""),
                    mods=[],
                )
            )

            for mod_name, active_str in cat_content.items():
                if mod_name in mod_objects:
                    mod_obj = mod_objects.pop(mod_name)
                    active = active_str.lower() == "true"
                    mod_obj.active = active if overwrite else (mod_name in active_mods)
                    new_categories[-1].mods.append(mod_obj)

        if new_categories and mod_objects:
            remaining = sorted(mod_objects.values(), key=lambda m: m.mod)
            new_categories[-1].mods += remaining

        self.categories = new_categories

    ### Import and Export
    @staticmethod
    def _construct_config_data(categories: list[Category]) -> dict:
        """Construct configuration mapping schema using a pure nested structure"""
        config_data = {}
        for category in categories:
            section_data = {"_desc": category.desc}
            for mod in category.mods:
                section_data[mod.mod] = "true" if mod.active else "false"
            config_data[category.title] = section_data

        return config_data

    def export_mod_list(self, dst: Path) -> None:
        """Export Ruka KMM ``mod_list``"""
        data = self._construct_config_data(self.categories)
        self._save_mod_list(dst, data)

    def apply_and_save_mods(self) -> None:
        """Apply mod list from ``self.categories`` and save it to ``self.mod_list_path``"""
        self._write_mod_cfg(self.categories)

        if self.mod_list_path.exists():
            copy_file(self.mod_list_path, add_suffix(self.mod_list_path, ".bak"))

        data = self._construct_config_data(self.categories)
        self._save_mod_list(self.mod_list_path, data)

    def import_mod_list(self, path: Path) -> None:
        """Import and apply external mod list file"""
        self._sync_with_mod_list(path, overwrite=True)
        self.apply_and_save_mods()

    def import_mods_cfg(self, mods_cfg_path: Path) -> None:
        """Import and apply mod list from external ``mod.cfg``"""
        self._create_mod_list_if_missing(force_apply=True, mods_cfg_path=mods_cfg_path)
        self._sync_with_mod_list(overwrite=True)
        self.apply_and_save_mods()


if __name__ == "__main__":
    from .mod import ModSource

    ruka_kmm_mod_list = (Path("~/.config/ruka-kmm") / const.mod_list).expanduser()
    game_root_path = Path("/games/SteamLibrary/steamapps/common/Kenshi/")
    workshop_path = Path("/games/SteamLibrary/steamapps/workshop/content/233860/")

    mm = ModManager(ruka_kmm_mod_list, game_root_path, workshop_path)

    def test_mod_manager():
        total_mods = sum(len(category.mods) for category in mm.categories)
        print("Total mods managed successfully inside pure INI:", total_mods)

    test_mod_manager()
    mm.apply_and_save_mods()

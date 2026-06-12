from dataclasses import dataclass
from pathlib import Path
import json

from . import const
from .mod import Mod, ModSource
from .utils import copy_file, json_dump


@dataclass
class Category:
    """Mod category"""

    title: str
    desc: str
    mods: list[Mod]


class ModManager:
    """Read, sort and save mod list"""

    def __init__(
        self, mod_list_json_path: Path, game_path: Path, workshop_mods_path: Path
    ) -> None:
        self.mod_list_json_path: Path = mod_list_json_path  # Ruka KMM mod list
        self.game_path: Path = game_path
        self.game_mods_path: Path = game_path / "mods"
        self.workshop_mods_path: Path = workshop_mods_path
        self.mods_cfg_path: Path = game_path / "data" / "mods.cfg"
        self.categories: list[Category] = []  # All the mods save in categories

        self._init_empty_categories()
        self._create_json_if_missing()
        self._sync_with_json(self.mod_list_json_path, False)

    def _init_empty_categories(self) -> None:
        """Initialize default empty mod categories"""
        for title, desc in const.category_intros:
            self.categories.append(Category(title, desc, []))

    def _scan_mods_from_path(
        self, mods_path: Path | str, source: ModSource
    ) -> list[Mod]:
        """Scan all the mods from path"""
        mods_path = Path(mods_path).expanduser()

        if not mods_path.exists():
            raise FileNotFoundError(f"{source} mods path does not exist: {mods_path}")
        if not mods_path.is_dir():
            raise NotADirectoryError(
                f"{source} mods path is not a directory: {mods_path}"
            )

        mods = []
        for path in mods_path.iterdir():
            if path.is_dir():
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

    def _get_enabled_mod_names(self, mods_cfg_path: Path | None = None) -> list[str]:
        """Read enabled mod names from <kenshi_game_root>/data/mod.cfg"""
        if mods_cfg_path is None:
            mods_cfg_path = self.mods_cfg_path

        if not mods_cfg_path.exists():
            raise FileNotFoundError(f"{mods_cfg_path} not found.")

        content = mods_cfg_path.read_text(encoding="utf-8")
        return [
            line.removesuffix(".mod") for line in content.splitlines() if line.strip()
        ]

    def _create_json_if_missing(
        self, force_apply: bool = False, mods_cfg_path: Path | None = None
    ) -> None:
        """Create Ruka KMM mod list in JSON from mods.cfg if not exists,
        use force_apply flag to overwrite"""
        if self.mod_list_json_path.exists() and not force_apply:
            return

        all_mod_names = [mod.mod for mod in self._scan_all_mods()]
        enabled_mod_names = self._get_enabled_mod_names(mods_cfg_path=mods_cfg_path)
        disabled_mod_names = [
            mod for mod in all_mod_names if mod not in set(enabled_mod_names)
        ]

        categories = [
            {"category": cat, "desc": desc, "mods": []}
            for cat, desc in const.category_intros
        ]
        categories[-1]["mods"] = [
            {"mod": mod, "enabled": True} for mod in enabled_mod_names
        ] + [{"mod": mod, "enabled": False} for mod in disabled_mod_names]

        json_dump(categories, self.mod_list_json_path)

    def _read_json_mod_list(self, json_path: Path | None = None) -> list[dict]:
        """Read json data from Ruka KMM configuration, read self.json_mod_list as default"""
        if json_path is None:
            json_path = self.mod_list_json_path

        if not self.mod_list_json_path.exists():
            raise FileNotFoundError(f"{self.mod_list_json_path} not found.")

        with open(self.mod_list_json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_mod_cfg(self, categories: list[Category]) -> None:
        """Write mod list to mod.cfg"""
        if self.mods_cfg_path.exists():
            copy_file(self.mods_cfg_path, self.mods_cfg_path.with_suffix(".bak"))

        with open(self.mods_cfg_path, "w", encoding="utf-8") as f:
            for category in categories:
                for mod in category.mods:
                    if mod.enabled:
                        f.write(mod.mod + ".mod\n")

    def _sync_with_json(self, json_path: Path | None = None, overwrite: bool = False):
        """Update self.categories according to mod list JSON file,
        use self.mod_list_json_path as default.

        If mods.cfg is different with .json,
        keep enabled status from mods.cfg and order from .json when overwrite is False,
        otherwise keep .json enabled status"""
        if json_path is None:
            json_path = self.mod_list_json_path

        if not json_path.exists():
            raise FileNotFoundError(f"{json_path} not found.")

        try:
            categoriy_dicts = self._read_json_mod_list()
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse mod list: {json_path} is broken or not a valid JSON file."
            ) from e

        mods = self._scan_all_mods()
        mod_dict = {mod.mod: mod for mod in mods}
        new_categories = []

        enabled_mods = set(self._get_enabled_mod_names()) if not overwrite else set()

        for category_dict in categoriy_dicts:
            new_categories.append(
                Category(
                    title=category_dict["category"],
                    desc=category_dict["desc"],
                    mods=[],
                )
            )
            for mod in category_dict["mods"]:
                mod_name = mod["mod"]
                enabled = mod["enabled"]
                if mod_name in mod_dict:
                    mod = mod_dict.pop(mod_name)
                    mod.enabled = enabled if overwrite else (mod_name in enabled_mods)
                    new_categories[-1].mods.append(mod)

        remaining = list(mod_dict.values())
        remaining.sort(key=lambda m: m.mod)
        new_categories[-1].mods += remaining

        self.categories = new_categories

    ### Import and Export
    @staticmethod
    def _construct_json_data(categories: list[Category]) -> list[dict]:
        """Construct mod name and enabled status data list"""
        data = [
            {
                "category": category.title,
                "desc": category.desc,
                "mods": category.mods,
            }
            for category in categories
        ]
        return data

    def export_json_mod_list(self, dst: Path) -> None:
        """Export Ruka KMM mod list in JSON format"""
        data = ModManager._construct_json_data(self.categories)
        json_dump(data, dst)

    def save_and_apply_mods(self) -> None:
        """Apply mod list from self.mods and save it to self.ruka_kmm_mod_list"""
        self._write_mod_cfg(self.categories)
        data = ModManager._construct_json_data(self.categories)
        json_dump(data, self.mod_list_json_path)

    def import_json_mod_list(self, json_path: Path) -> None:
        """Import and apply external JSON mod list"""
        self._sync_with_json(json_path, overwrite=True)
        self.save_and_apply_mods()

    def import_mods_cfg(self, mods_cfg_path: Path) -> None:
        """Import and apply mod list from external mod.cfg"""
        self._create_json_if_missing(force_apply=True, mods_cfg_path=mods_cfg_path)
        self._sync_with_json(overwrite=True)
        self.save_and_apply_mods()


if __name__ == "__main__":
    from .mod import ModSource

    ruka_kmm_mod_list = (Path("~/.config/ruka-kmm") / const.mod_list_json).expanduser()
    game_root_path = Path("/games/SteamLibrary/steamapps/common/Kenshi/")
    workshop_path = Path("/games/SteamLibrary/steamapps/workshop/content/233860/")

    mm = ModManager(ruka_kmm_mod_list, game_root_path, workshop_path)

    def test_mod():
        mod_path1 = (
            "/games/SteamLibrary/steamapps/common/Kenshi/mods/More Combat Animation"
        )
        mod_path2 = "/games/SteamLibrary/steamapps/workshop/content/233860/1200632417"
        mod_path3 = "~/Games/Kenshi/mods/Emkejs-Mod-Core"

        mod = Mod.from_path(mod_path1, ModSource.GAME_ROOT)
        print(mod)
        print()

        mod = Mod.from_path(mod_path2, ModSource.WORKSHOP)
        print(mod)
        print()

        mod = Mod.from_path(mod_path3, ModSource.GAME_ROOT)
        print(mod)
        print()

    def test_mod_manager():
        for mod in mm.categories:
            mod.desc = mod.desc[:20]
            print(mod)
            print()
        print("Total mods:", len(mm.categories))

        # for mod in mm.mods:
        #     print("img: ", mod.img)

    # test_mod()
    # test_mod_manager()

    # lis = mm._get_enabled_mods_name_from_mod_cfg()
    # for i in lis:
    #     print(i)
    # mm.init_sorted_mod_list_from_mod_cfg()

    # test_mod_manager()
    # print()

    # mm.import_json_mod_list(True)
    # test_mod_manager()
    # print()

    # mm.mods[0].enabled = False

    # mm.save_and_apply_mods()

from pathlib import Path
import json
from .mod import Mod, ModSource
from .utils import copy_file, json_dump


class ModManager:
    """Read, sort and save mod list"""

    def __init__(
        self, json_mod_list: Path, game_path: Path, workshop_mods_path: Path
    ) -> None:
        self.json_mod_list: Path = json_mod_list  # Ruka KMM mod list
        self.game_path: Path = game_path
        self.game_mods_path: Path = game_path / "mods"
        self.workshop_mods_path: Path = workshop_mods_path
        self.mods_cfg_path: Path = game_path / "data" / "mods.cfg"
        self.mods: list[Mod] = []

        self._create_json_if_missing()
        self._sync_with_json(self.json_mod_list, False)

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
        if self.json_mod_list.exists() and not force_apply:
            return

        all_mod_names = [mod.mod for mod in self._scan_all_mods()]
        enabled_mod_names = self._get_enabled_mod_names(mods_cfg_path=mods_cfg_path)
        disabled_mod_names = [
            mod for mod in all_mod_names if mod not in set(enabled_mod_names)
        ]

        data = {
            "mods": [{"mod": mod, "enabled": True} for mod in enabled_mod_names]
            + [{"mod": mod, "enabled": False} for mod in disabled_mod_names]
        }
        json_dump(data, self.json_mod_list)

    def _read_json_mod_list(
        self, json_path: Path | None = None
    ) -> list[tuple[str, bool]]:
        """Read json data from Ruka KMM configuration, read self.json_mod_list as default"""
        if json_path is None:
            json_path = self.json_mod_list

        if not self.json_mod_list.exists():
            raise FileNotFoundError(f"{self.json_mod_list} not found.")

        with open(self.json_mod_list, "r", encoding="utf-8") as f:
            data = json.load(f)
        mods = [(mod["mod"], mod["enabled"]) for mod in data.get("mods", [])]
        return mods

    def _write_mod_cfg(self, mods: list[Mod]) -> None:
        """Write mod list to mod.cfg"""
        if self.mods_cfg_path.exists():
            copy_file(self.mods_cfg_path, self.mods_cfg_path.with_suffix(".bak"))

        with open(self.mods_cfg_path, "w", encoding="utf-8") as f:
            for mod in mods:
                if mod.enabled:
                    f.write(mod.mod + ".mod\n")

    def _sync_with_json(self, json_path: Path | None = None, overwrite: bool = False):
        """Update self.mods according to Ruka KMM mod list JSON file,
        use self.ruka_kmm_mod_list as default.

        If mods.cfg is different with ruka-kmm-mod-list.json,
        keep enabled status from mods.cfg and order from .json when overwrite is False,
        otherwise keep .json enabled status"""
        if json_path is None:
            json_path = self.json_mod_list

        if not json_path.exists():
            raise FileNotFoundError(f"{json_path} not found.")

        try:
            ordered = self._read_json_mod_list(json_path)  # [(mod: str, enabled: bool)]
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse mod list: {json_path} is broken or not a valid JSON file."
            ) from e

        mods = self._scan_all_mods()
        mod_dict = {mod.mod: mod for mod in mods}
        new_mods = []

        enabled_mods = set(self._get_enabled_mod_names()) if not overwrite else set()

        for mod_name, enabled in ordered:
            # Mod exists locally
            if mod_name in mod_dict:
                mod = mod_dict.pop(mod_name)
                mod.enabled = enabled if overwrite else (mod_name in enabled_mods)
                new_mods.append(mod)

        remaining = list(mod_dict.values())
        remaining.sort(key=lambda m: m.mod)
        new_mods += remaining

        self.mods = new_mods

    ### Import and Export
    @staticmethod
    def _construct_json_data(mods: list[Mod]) -> dict:
        """Construct mod name and enabled status data list"""
        data = {"mods": [{"mod": mod.mod, "enabled": mod.enabled} for mod in mods]}
        return data

    def export_json_mod_list(self, dst: Path) -> None:
        """Export Ruka KMM mod list in JSON format"""
        data = ModManager._construct_json_data(self.mods)
        json_dump(data, dst)

    def save_and_apply_mods(self) -> None:
        """Apply mod list from self.mods and save it to self.ruka_kmm_mod_list"""
        self._write_mod_cfg(self.mods)
        data = ModManager._construct_json_data(self.mods)
        json_dump(data, self.json_mod_list)

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

    ruka_kmm_mod_list = Path("~/.config/ruka-kmm/ruka-kmm-mod-list.json").expanduser()
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
        for mod in mm.mods:
            mod.desc = mod.desc[:20]
            print(mod)
            print()
        print("Total mods:", len(mm.mods))

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

    mm.save_and_apply_mods()

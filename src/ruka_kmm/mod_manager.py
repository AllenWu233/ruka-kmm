from pathlib import Path
from .mod import Mod, ModSource
from typing import Set, List
import json


class ModManager:
    """Read, sort and save mod list"""

    def __init__(
        self, ruka_kmm_mod_list: Path, game_path: Path, workshop_mods_path: Path
    ) -> None:
        self.ruka_kmm_mod_list: Path = ruka_kmm_mod_list
        self.game_path: Path = game_path
        self.game_mods_path: Path = game_path / "mods"
        self.workshop_mods_path: Path = workshop_mods_path
        self.mods_cfg_path: Path = game_path / "data" / "mods.cfg"
        self.mods: list[Mod] = self._read_all_mods()

    def _read_mods_from_path(
        self, mods_path: Path | str, source: ModSource
    ) -> list[Mod]:
        """Read all the mods from path"""
        mods_path = Path(mods_path).expanduser()

        if source == ModSource.GAME_ROOT:
            msg = "Game root"
        elif source == ModSource.WORKSHOP:
            msg = "Steam Workshop"
        else:
            msg = "Unknown source"

        if not mods_path.exists():
            raise FileNotFoundError(f"{msg} mods path does not exist: {mods_path}")
        if not mods_path.is_dir():
            raise NotADirectoryError(f"{msg} mods path is not a directory: {mods_path}")

        mods = []

        for path in mods_path.iterdir():
            if path.is_dir():
                try:
                    mod = Mod.from_path(path, source)
                    mods.append(mod)
                except FileNotFoundError:
                    pass

        return mods

    def _get_enabled_mod_names_from_mod_cfg(self) -> List[str]:
        """Read enabled mods name from <kenshi_game_root>/data/mod.cfg"""
        content = self.mods_cfg_path.read_text(encoding="utf-8")
        return [
            line[:-4] if line.endswith(".mod") else line
            for line in content.splitlines()
            if line
        ]

    def _read_all_mods(self) -> list[Mod]:
        """Read all the mods from local and Steam Workshop mods path"""
        mods = sorted(
            self._read_mods_from_path(self.game_mods_path, ModSource.GAME_ROOT)
            + self._read_mods_from_path(self.workshop_mods_path, ModSource.WORKSHOP),
            key=lambda m: m.mod,
        )

        enabled_mods = set(self._get_enabled_mod_names_from_mod_cfg())
        for mod in mods:
            if mod.mod in enabled_mods:
                mod.enabled = True

        return mods

    # def _read_sorted_mod_list(self) -> List[Mod]:
    #     """Read sorted mod list from Ruka KMM configuration"""
    #     return

    def init_sorted_mod_list_from_mod_cfg(self) -> None:
        """Initialize Ruka KMM mod list if not exists"""
        if self.ruka_kmm_mod_list.exists():
            return

        all_mod_names = [mod.mod for mod in self._read_all_mods()]
        enabled_mod_names = self._get_enabled_mod_names_from_mod_cfg()
        disabled_mod_names = [
            mod for mod in all_mod_names if mod not in set(enabled_mod_names)
        ]

        data = {
            "mods": (
                [{"mod": mod, "enabled": True} for mod in enabled_mod_names]
                + [{"mod": mod, "enabled": False} for mod in disabled_mod_names]
            )
        }
        self.ruka_kmm_mod_list.parent.mkdir(parents=True, exist_ok=True)
        with open(self.ruka_kmm_mod_list, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


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
        mm = ModManager(ruka_kmm_mod_list, game_root_path, workshop_path)
        for mod in mm.mods:
            mod.desc = mod.desc[:20]
            print(mod)
            print()
        print("Total mods: ", len(mm.mods))

        # for mod in mm.mods:
        #     print("img: ", mod.img)

    # test_mod()
    # test_mod_manager()
    # lis = mm._get_enabled_mods_name_from_mod_cfg()
    # for i in lis:
    #     print(i)
    mm.init_sorted_mod_list_from_mod_cfg()

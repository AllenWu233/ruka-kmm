from pathlib import Path
from .mod import Mod


class ModManager:
    """Read, sort and save mod list"""

    def __init__(self, local_mods_path, workshop_mods_path) -> None:
        self.local_mods_path = local_mods_path
        self.workshop_mods_path = workshop_mods_path
        self.mods: list[Mod] = self._read_all_mods(local_mods_path, workshop_mods_path)

    def _read_mods_from_path(self, mods_path: Path | str, local: bool) -> list[Mod]:
        """Read all the mods from path"""
        mods_path = Path(mods_path).expanduser().resolve()
        msg = "Local" if local else "Steam Workshop"
        if not mods_path.exists():
            raise FileNotFoundError(f"{msg} mods path does not exist: {mods_path}")
        if not mods_path.is_dir():
            raise NotADirectoryError(f"{msg} mods path is not a directory: {mods_path}")

        mods = []

        for path in mods_path.iterdir():
            if path.is_dir():
                try:
                    mod = Mod.from_path(path, local)
                    mods.append(mod)
                except FileNotFoundError:
                    pass

        return mods

    def _read_all_mods(
        self, local_mods_path: Path | str, workshop_mods_path: Path | str
    ) -> list[Mod]:
        """Read all the mods from local and Steam Workshop mods path"""
        mods = sorted(
            self._read_mods_from_path(local_mods_path, True)
            + self._read_mods_from_path(workshop_mods_path, False),
            key=lambda m: m.mod,
        )
        return mods


if __name__ == "__main__":

    def test_mod():
        mod_path1 = (
            "/games/SteamLibrary/steamapps/common/Kenshi/mods/More Combat Animation"
        )
        mod_path2 = "/games/SteamLibrary/steamapps/common/Kenshi/mods/Modern UI One Row Edition 16_10/"
        mod_path3 = "/games/SteamLibrary/steamapps/workshop/content/233860/1200632417"
        mod_path4 = "~/Games/Kenshi/mods/Emkejs-Mod-Core"

        mod = Mod.from_path(mod_path1, True)
        print(mod)
        print()

        # mod = Mod.from_path(mod_path2)

        mod = Mod.from_path(mod_path3, False)
        print(mod)
        print()

        mod = Mod.from_path(mod_path4, True)
        print(mod)
        print()

    def test_mod_manager():
        local_path = "/games/SteamLibrary/steamapps/common/Kenshi/mods/"
        workshop_path = "/games/SteamLibrary/steamapps/workshop/content/233860/"

        mm = ModManager(local_path, workshop_path)
        # for mod in mm.mods:
        # print(mod.mod)
        # mod.description = ""
        # print(mod)
        print("Total mods: ", len(mm.mods))

    # test_mod()
    test_mod_manager()

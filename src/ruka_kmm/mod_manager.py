from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET
from typing import Self
import re


@dataclass
class Mod:
    """Information of single modification"""

    enabled: bool = False
    local: bool = False  # True: Local / False: Steam Workshop
    id: str = ""
    mod: str = ""
    author: str = ""
    title: str = ""
    url: str = ""
    tags: list[str] = field(default_factory=list)
    visibility: int | None = None
    last_update: str = ""
    description: str = ""

    @staticmethod
    def _find_file_ext(root_path: Path, ext: str) -> Path | None:
        """Find full file path with specific extension"""
        file_path = next(root_path.glob(f"*{ext}"), None)
        return file_path

    @staticmethod
    def _clean_text(raw: str) -> str:
        """Keep \n (0x0a), \r (0x0d), \t (0x09),
        remove other C0 control chars (0x00-0x1f except 0x09,0x0a,0x0d)
        Using for reading description context from .mod file
        """
        return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", raw)

    @staticmethod
    def _read_mod_file_and_get_author(path: Path) -> tuple[str, str]:
        """
        Read and clean description form .mod file
        Return mod description and author name as (description, author)
        """
        raw = path.read_text(encoding="utf-8", errors="ignore")

        match = re.search(r"^[\x00-\x1f\x7f]*([A-Za-z0-9_ ]+)", raw)
        author = match.group(1) if match else ""

        raw = Mod._clean_text(raw)
        # Take everything before first 'gamedata.base'
        stop_marker = "gamedata.base"
        pos = raw.find(stop_marker)
        if pos != -1:
            raw = raw[:pos]
        else:
            raw = raw

        return (raw, author)

    @classmethod
    def from_path(cls, root_path: Path | str, local: bool) -> Self:
        """Initialize Mod from single mod directory"""
        root_path = Path(root_path).expanduser().resolve()
        if not root_path.exists():
            raise FileNotFoundError(f"Mod path does not exist: {root_path}")
        if not root_path.is_dir():
            raise NotADirectoryError(f"Mod path is not a directory: {root_path}")

        mod_file = cls._find_file_ext(root_path, ".mod")
        if not mod_file:
            raise FileNotFoundError(f".mod file not found in {root_path}")
        description, author = cls._read_mod_file_and_get_author(mod_file)

        # .info file is .xml type
        info_file = cls._find_file_ext(root_path, ".info")
        if info_file:
            # Parse xml metadata
            tree = ET.parse(info_file)
            root = tree.getroot()
            tags = [elem.text for elem in root.findall(".//tags/string") if elem.text]

            id = root.findtext("id", "")
            if local:
                url = ""
            else:
                url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={id}"

            mod_obj = cls(
                local=local,
                id=id,
                mod=root.findtext("mod", ""),
                author=author,
                title=root.findtext("title", ""),
                url=url,
                tags=tags,
                visibility=int(root.findtext("visibility", "")),
                last_update=root.findtext("lastUpdate", ""),
                description=description,
            )
        else:
            mod_obj = cls(local=local, mod=mod_file.stem, author=author)

        return mod_obj


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
        for mod in mm.mods:
            # print(mod.mod)
            mod.description = ""
            print(mod)
        print(len(mm.mods))

    # test_mod()
    test_mod_manager()

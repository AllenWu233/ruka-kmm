from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET
from typing import Self
import re


@dataclass
class Mod:
    """Information of single modification"""

    enabled: bool
    local: bool
    id: str
    mod: str
    author: str
    title: str
    url: str
    tags: list[str]
    visibility: int
    last_update: str
    description: str

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

        match = re.search(r"^[\x00-\x1f\x7f]*([A-Za-z0-9_]{3,})", raw)
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
        root_path = Path(root_path)
        if not root_path.is_dir():
            raise NotADirectoryError(f"{root_path} isn't available single mod path.")

        # .info file is in .xml type
        info_file = cls._find_file_ext(root_path, ".info")
        if not info_file:
            raise FileNotFoundError(f".info file not found in {root_path}")
        mod_file = cls._find_file_ext(root_path, ".mod")

        # Parse xml metadata
        tree = ET.parse(info_file)
        root = tree.getroot()
        tags = [elem.text for elem in root.findall(".//tags/string") if elem.text]

        id = root.findtext("id", "")
        url = (
            f"https://steamcommunity.com/sharedfiles/filedetails/?id={id}"
            if not local
            else ""
        )

        if mod_file:
            description, author = cls._read_mod_file_and_get_author(mod_file)
        else:
            description, author = "", ""

        mod_obj = cls(
            enabled=False,
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

        return mod_obj


class ModManager:
    """Read, sort and save mod list"""

    def __init__(self) -> None:
        self.mods: list[Mod] = []

    def _read_all_mods(self, mod_path: Path | str) -> list[Mod]:
        """Read all the mods' information from mods path"""
        mods = []

        return mods


if __name__ == "__main__":
    mod_path1 = "/games/SteamLibrary/steamapps/common/Kenshi/mods/More Combat Animation"
    mod_path2 = "/games/SteamLibrary/steamapps/common/Kenshi/mods/Modern UI One Row Edition 16_10/"
    mod_path3 = "/games/SteamLibrary/steamapps/workshop/content/233860/1200632417"

    # mod = Mod.from_path(mod_path1, True)
    # mod = Mod.from_path(mod_path2)
    mod = Mod.from_path(mod_path3, False)
    print(mod)

from enum import Enum, auto
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET
from typing import Self
import re


class ModSource(Enum):
    GAME_ROOT = auto()
    WORKSHOP = auto()

    def __str__(self) -> str:
        return self.name.replace("_", " ").title()


@dataclass
class _ModFileData:
    """Raw text data extracted from a .mod file"""

    author: str
    desc: str


@dataclass
class Mod:
    """Information of single modification"""

    active: bool = False
    source: ModSource = ModSource.GAME_ROOT
    id: str | None = None
    mod: str = ""  # Mod name displays in Kenshi Official Launcher
    author: str = ""
    title: str = ""
    url: str | None = None
    tags: list[str] = field(default_factory=list)
    visibility: int | None = None
    last_update: str = ""
    desc: str = ""
    img: Path | None = None  # Cover image

    @staticmethod
    def _find_file_with_ext(root_path: Path, ext: str) -> Path | None:
        """Find full file path with specific extension"""
        return next(root_path.glob(f"*{ext}"), None)

    @staticmethod
    def _clean_mod_text(raw: str) -> str:
        """Keep \n (0x0a), \r (0x0d), \t (0x09),
        remove other C0 control chars (0x00-0x1f except 0x09,0x0a,0x0d),
        use for reading description context from .mod file
        """
        return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", raw)

    @classmethod
    def _parse_mod_file(cls, mod_file: Path) -> _ModFileData:
        """Extract author and description from a .mod file"""
        raw = mod_file.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r"^[\x00-\x1f\x7f]*([A-Za-z0-9_ ]+)", raw[:200])
        author = match.group(1).strip() if match else ""

        desc = cls._clean_mod_text(raw).removeprefix(author)
        stop_marker = "gamedata.base"
        pos = desc.find(stop_marker)
        if pos != -1:
            desc = desc[:pos]

        return _ModFileData(author=author, desc=desc)

    @staticmethod
    def _parse_info_file(info_file: Path, source: ModSource) -> dict:
        """Parse optional .info XML and return extra Mod fields as a dict"""
        root = ET.parse(info_file).getroot()
        tags = [elem.text for elem in root.findall(".//tags/string") if elem.text]
        mod_id = root.findtext("id", "")

        if source == ModSource.WORKSHOP:
            url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={mod_id}"
        else:
            url = ""

        visibility_raw = root.findtext("visibility", "")
        try:
            visibility = int(visibility_raw)
        except ValueError:
            visibility = None

        return {
            "id": mod_id,
            "title": root.findtext("title", ""),
            "url": url,
            "tags": tags,
            "visibility": visibility,
            "last_update": root.findtext("lastUpdate", ""),
        }

    @classmethod
    def from_path(cls, root_path: Path, source: ModSource) -> Self:
        """Build Mod from a single mod directory"""
        if not root_path.exists():
            raise FileNotFoundError(f"Mod path does not exist: {root_path}")
        if not root_path.is_dir():
            raise NotADirectoryError(f"Mod path is not a directory: {root_path}")

        mod_file = cls._find_file_with_ext(root_path, ".mod")
        if not mod_file:
            raise FileNotFoundError(f".mod file not found in {root_path}")

        mod_data = cls._parse_mod_file(mod_file)
        img = cls._find_file_with_ext(root_path, ".img")
        info_file = cls._find_file_with_ext(root_path, mod_file.stem + ".info")
        extra = cls._parse_info_file(info_file, source) if info_file else {}

        return cls(
            source=source,
            mod=mod_file.stem,
            author=mod_data.author,
            desc=mod_data.desc,
            img=img,
            **extra,
        )

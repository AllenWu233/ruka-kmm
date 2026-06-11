from enum import Enum, auto
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET
from typing import Self
import re


class ModSource(Enum):
    GAME_ROOT = auto()
    WORKSHOP = auto()


@dataclass
class Mod:
    """Information of single modification"""

    enabled: bool = False
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
    def _find_file_ext(root_path: Path, ext: str) -> Path | None:
        """Find full file path with specific extension"""
        file_path = next(root_path.glob(f"*{ext}"), None)
        return file_path

    @staticmethod
    def _clean_text(raw: str) -> str:
        """Keep \n (0x0a), \r (0x0d), \t (0x09),
        remove other C0 control chars (0x00-0x1f except 0x09,0x0a,0x0d),
        use for reading description context from .mod file
        """
        return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", raw)

    @staticmethod
    def _get_author_and_desc_from_mod_file(path: Path) -> tuple[str, str]:
        """
        Read and clean .mod file
        Return mod author name and description as (author, description)
        """
        raw = path.read_text(encoding="utf-8", errors="ignore")

        # Extract first valid text segment as author between control characters
        # Limit search to the leading chunk before description to prevent false positives
        match = re.search(r"^[\x00-\x1f\x7f]*([A-Za-z0-9_ ]+)", raw[:200])
        # match = re.search(r"([A-Za-z0-9_][A-Za-z0-9_ ]*)", head)
        author = match.group(1).strip() if match else ""

        desc = Mod._clean_text(raw).removeprefix(author)
        # Take everything before first 'gamedata.base'
        stop_marker = "gamedata.base"
        pos = desc.find(stop_marker)
        if pos != -1:
            desc = desc[:pos]

        return (author, desc)

    @classmethod
    def from_path(cls, root_path: Path | str, source: ModSource) -> Self:
        """Initialize Mod from single mod directory"""
        root_path = Path(root_path).expanduser().resolve()
        if not root_path.exists():
            raise FileNotFoundError(f"Mod path does not exist: {root_path}")
        if not root_path.is_dir():
            raise NotADirectoryError(f"Mod path is not a directory: {root_path}")

        mod_file = cls._find_file_ext(root_path, ".mod")
        if not mod_file:
            raise FileNotFoundError(f".mod file not found in {root_path}")

        mod = mod_file.stem
        author, desc = cls._get_author_and_desc_from_mod_file(mod_file)

        img = cls._find_file_ext(root_path, ".img")

        # Process metadata if optional .info XML file exists
        info_file = cls._find_file_ext(root_path, mod + ".info")
        if info_file:
            tree = ET.parse(info_file)
            root = tree.getroot()
            tags = [elem.text for elem in root.findall(".//tags/string") if elem.text]

            id = root.findtext("id", "")

            if source == ModSource.WORKSHOP:
                url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={id}"
            else:
                url = ""

            try:
                visibility = int(root.findtext("visibility", ""))
            except ValueError:
                visibility = None

            mod_obj = cls(
                source=source,
                id=id,
                # mod=root.findtext("mod", ""),
                mod=mod,
                author=author,
                title=root.findtext("title", ""),
                url=url,
                tags=tags,
                visibility=visibility,
                last_update=root.findtext("lastUpdate", ""),
                desc=desc,
                img=img,
            )
        else:
            # Fallback to defaults for missing info file
            mod_obj = cls(
                source=source,
                mod=mod,
                author=author,
                desc=desc,
                img=img,
            )

        return mod_obj

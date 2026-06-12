import shutil
from pathlib import Path
import json


def copy_file(src: Path, dst: Path) -> None:
    """Copy file from src to dst, overwriting if exists"""
    shutil.copy2(src, dst)


def json_dump(data, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

import shutil
import json
from pathlib import Path
from datetime import datetime


def copy_file(src: Path, dst: Path) -> None:
    """Copy file from src to dst, overwriting if exists"""
    shutil.copy2(src, dst)


def json_dump(data, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def timestamp_str() -> str:
    """Return current timestamp as 'YYYY-MM-DD_HH-MM-SS'"""
    now = datetime.now()
    return now.strftime("%Y-%m-%d_%H-%M-%S")

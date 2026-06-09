from pathlib import Path


def mod_to_txt(path: Path | str) -> None:
    """Convert .mod file to .txt"""
    path = Path(path)
    raw = path.read_text(encoding="utf-8", errors="ignore")
    with open(f"{path}.txt", "w", encoding="utf-8") as f:
        f.write(raw)


if __name__ == "__main__":
    mod1 = "/games/SteamLibrary/steamapps/common/Kenshi/mods/More Combat Animation/More Combat Animation.mod"

    mod_to_txt(mod1)

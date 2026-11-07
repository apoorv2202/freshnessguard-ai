"""Package Git-visible source only; ignored credentials and builds stay local."""
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import os

from freshnessguard.config import load_env


def main():
    root = Path.cwd()
    names = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"]).decode().split("\0")
    files = [Path(name) for name in names if name]
    if any(path.name == ".env" or "work" in path.parts for path in files):
        raise RuntimeError("Refusing to package ignored local data")
    if (root / ".env").is_file():
        load_env(root / ".env")
    secrets = [os.environ.get(k) for k in ("TAVILY_API_KEY", "BIFROST_VIRTUAL_KEY", "FRESHNESSGUARD_TOKEN")]
    for path in files:
        if path.is_file() and any(value and value.encode() in path.read_bytes() for value in secrets):
            raise RuntimeError("Refusing to package a source file containing a configured credential")
    destination = root.parent / "FreshnessGuard-AI-source.zip"
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
        for path in files:
            if path.is_file():
                archive.write(path, arcname=Path("FreshnessGuard-AI") / path)
    print(f"Packaged {len(files)} source files in {destination.name}; no .env or build artifacts")


if __name__ == "__main__":
    main()

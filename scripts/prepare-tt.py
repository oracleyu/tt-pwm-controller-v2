"""Fetch the pinned support tools when cloning from a source ZIP."""
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[1]
if not (root/'tt/tt_tool.py').is_file():
    subprocess.run(['git','clone','https://github.com/TinyTapeout/tt-support-tools.git',str(root/'tt')],check=True)
    subprocess.run(['git','-C',str(root/'tt'),'checkout','--detach','9d13ff3e3e6202090740110438c6a10c1d62ca0f'],check=True)

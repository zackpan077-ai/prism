# -*- coding: utf-8 -*-
"""Compose the Reels slideshow video from generated slide images."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SLIDES = ROOT / "social" / "2026-09-01" / "slides_2026-09-01"
OUT = ROOT / "social" / "2026-09-01" / "reel.mp4"

tool = os.path.expandvars(
    r"%LOCALAPPDATA%\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe"
)
if not Path(tool).exists():
    sys.exit(f"tool not found: {tool}")

cmd = [
    tool, "-y",
    "-framerate", "0.5",
    "-i", str(SLIDES / "slide_%02d.png"),
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-r", "30",
    str(OUT),
]
res = subprocess.run(cmd, capture_output=True, text=True)
if res.returncode != 0:
    print(res.stderr[-800:])
    sys.exit(1)
print(f"OK -> {OUT} ({OUT.stat().st_size / 1_000_000:.2f} MB)")

# -*- coding: utf-8 -*-
"""
prism - make an Instagram reel (1080x1920 MP4) from an analysis JSON.

Slides:
  1. Hook card    2. Title card       3. Finding cards (one per finding)
  N. Countries card (10 flags/names)  N+1. Outro card

Design: flat dark, big type, no gradients/effects. Text is laid out by this
script (not HTML) so there is no browser dependency.

Requires Pillow only. Writes to social/<date>/reel.mp4 via ffmpeg (pipe).
NOTE: ffmpeg pipes are blocked in this environment, so the script mainly
produces slides_<date>/ PNG frames + an ffmpeg command to run manually.
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
BG = (20, 20, 20)
FG = (230, 230, 230)
MUTED = (160, 160, 160)
FAINT = (110, 110, 110)
ACCENT = (106, 176, 243)
DANGER = (226, 100, 90)

FONT_DIR = Path("C:/Windows/Fonts")
F_BOLD = str(FONT_DIR / "msyhbd.ttc")   # Microsoft YaHei Bold
F_REG = str(FONT_DIR / "msyh.ttc")      # Microsoft YaHei

FLAGS = {"US": "🇺🇸", "UK": "🇬🇧", "India": "🇮🇳", "Japan": "🇯🇵", "France": "🇫🇷",
         "Germany": "🇩🇪", "Brazil": "🇧🇷", "Russia": "🇷🇺", "Egypt": "🇪🇬", "China": "🇨🇳"}


def font(size: int, bold=False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(F_BOLD if bold else F_REG, size)


def wrap(draw, text, fnt, max_w):
    """Simple CJK-aware wrap: break by character when a word doesn't fit."""
    lines, cur = [], ""
    # tokenize into runs of non-space / space chars, but for CJK wrap by char
    tokens = []
    run = ""
    for ch in text:
        if ch in " \u3000":
            if run:
                tokens.append(run)
                run = ""
            tokens.append(ch)
        else:
            run += ch
    if run:
        tokens.append(run)
    for tok in tokens:
        test = cur + tok
        if draw.textlength(test, font=fnt) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur.rstrip())
            cur = tok.lstrip()
    if cur.strip():
        lines.append(cur.strip())
    return lines


def base_card():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # top brand strip
    d.text((72, 96), "PRISM 棱镜", font=font(30, bold=True), fill=FAINT)
    d.text((72, 140), "一个事件 · 十国视角", font=font(26), fill=FAINT)
    # bottom strip
    d.text((72, H - 120), "数据：Google News 十国版 · 全部标题可回原文核对",
           font=font(24), fill=FAINT)
    d.text((72, H - 84), "prism.news · daily", font=font(24), fill=FAINT)
    return img, d


def card_hook():
    img, d = base_card()
    big = font(88, bold=True)
    d.text((72, 700), "同一件事，", font=big, fill=FG)
    d.text((72, 820), "十种讲法。", font=big, fill=FG)
    d.text((72, 1010), "今天，世界各国的头版", font=font(44), fill=MUTED)
    d.text((72, 1075), "都在怎么讲同一件事？", font=font(44), fill=MUTED)
    d.text((72, 1250), "→", font=font(60), fill=ACCENT)
    return img


def card_title(analysis):
    img, d = base_card()
    d.text((72, 620), "今日事件", font=font(40), fill=ACCENT)
    title = analysis.get("event_title") or analysis.get("event", "")[:24]
    lines = wrap(d, title, font(72, bold=True), W - 144)
    y = 700
    for ln in lines[:4]:
        d.text((72, y), ln, font=font(72, bold=True), fill=FG)
        y += 100
    sub = analysis.get("event", "")
    y += 40
    for ln in wrap(d, sub, font(36), W - 144)[:4]:
        d.text((72, y), ln, font=font(36), fill=MUTED)
        y += 54
    d.text((72, H - 220), analysis.get("date", ""), font=font(28), fill=FAINT)
    return img


def card_finding(idx, total, f):
    img, d = base_card()
    d.text((72, 300), f"发现 {idx}/{total}", font=font(34), fill=ACCENT)
    y = 380
    for ln in wrap(d, f.get("title", ""), font(62, bold=True), W - 144)[:3]:
        d.text((72, y), ln, font=font(62, bold=True), fill=FG)
        y += 84
    y += 50
    body = f.get("body", "")
    for ln in wrap(d, body, font(38), W - 144)[:14]:
        d.text((72, y), ln, font=font(38), fill=MUTED)
        y += 56
    return img


def card_countries(analysis):
    img, d = base_card()
    d.text((72, 360), "十个国家，同一件事", font=font(56, bold=True), fill=FG)
    y = 520
    for cid, c in analysis.get("countries", {}).items():
        name = c.get("name", cid)
        frame = c.get("frame", "")
        d.text((72, y), name, font=font(44, bold=True), fill=FG)
        ln = wrap(d, frame, font(30), W - 144 - 400)[:1]
        if ln:
            d.text((460, y + 8), ln[0] + ("…" if len(wrap(d, frame, font(30), W - 544)) > 1 else ""),
                   font=font(30), fill=FAINT)
        y += 110
        if y > H - 260:
            break
    return img


def card_outro():
    img, d = base_card()
    d.text((72, 760), "你看到的，", font=font(76, bold=True), fill=FG)
    d.text((72, 870), "只是其中一种讲法。", font=font(76, bold=True), fill=FG)
    d.text((72, 1060), "关注 @prism.daily", font=font(48), fill=ACCENT)
    d.text((72, 1140), "每天一期 · 十国头版并排", font=font(38), fill=MUTED)
    return img


def build_slides(analysis) -> list[Image.Image]:
    slides = [card_hook(), card_title(analysis)]
    findings = analysis.get("findings", [])
    for i, f in enumerate(findings, 1):
        slides.append(card_finding(i, len(findings), f))
    slides.append(card_countries(analysis))
    slides.append(card_outro())
    return slides


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not src or not src.exists():
        sys.exit(f"usage: python make_reel.py data/analysis_<date>.json")
    analysis = json.loads(src.read_text(encoding="utf-8"))
    out_dir = Path("social") / analysis.get("date", "out")
    slides_dir = out_dir / f"slides_{analysis.get('date', 'out')}"
    slides_dir.mkdir(parents=True, exist_ok=True)
    slides = build_slides(analysis)
    for i, img in enumerate(slides):
        img.save(slides_dir / f"slide_{i:02d}.png")
    print(f"wrote {len(slides)} slides -> {slides_dir}")
    # Print the ffmpeg command (piping frames to ffmpeg is blocked here).
    frames = slides_dir / "slide_%02d.png"
    print("\nEncode manually with:")
    print(f'  ffmpeg -framerate 0.5 -i "{frames}" -c:v libx264 -pix_fmt yuv420p '
          f'-r 30 -vf "scale=1080:1920" "{out_dir / "reel.mp4"}"')


if __name__ == "__main__":
    main()

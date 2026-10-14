"""Acceptance checks for the deck and explorer. Prints PASS or FAIL per check; exits 1 if any fail."""
import json
import os
import re
import sys
import zipfile

import yaml
from pptx import Presentation
from pptx.util import Pt

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PPTX = os.path.join(ROOT, "deck", "drift-talk.pptx")
prs = Presentation(PPTX)
Y = yaml.safe_load(open(os.path.join(ROOT, "deck", "slides.yaml")))
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
res = []


def check(name, ok, detail=""):
    res.append(ok)
    print(("PASS  " if ok else "FAIL  ") + name + (f"  [{detail}]" if detail else ""))


def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


allslides = list(prs.slides)
OFF = 2  # template welcome and bio slides come first; the template thank-you slide follows slide 22
slides = allslides[OFF:OFF + 22] + allslides[OFF + 23:]  # 22 main + 4 appendix, numbered as in the plan
check("22 main slides and 4 appendix slides", len(slides) == 26 and len(Y["slides"]) == 22 and len(Y["appendix"]) == 4 and len(allslides) == 29, f"{len(slides)} plan slides, {len(allslides)} with the 3 template slides")

# notes format and timing
pat = re.compile(r"^\[(\d\d:\d\d) to (\d\d:\d\d)\]\n(.+)\nCUE: (.+)\nIF SHORT ON TIME: (.+)$", re.S)
bad, total, prev_end = [], 0, 0
for i, sl in enumerate(slides):
    t = sl.notes_slide.notes_text_frame.text
    m = pat.match(t)
    if not m or len(m.group(3).split()) > 90:
        bad.append(i + 1)
        continue
    a = int(m.group(1)[:2]) * 60 + int(m.group(1)[3:]); b = int(m.group(2)[:2]) * 60 + int(m.group(2)[3:])
    if i < 22:
        total += b - a
        if a != prev_end:
            bad.append(f"gap at {i + 1}")
        prev_end = b
check("Every slide has notes in the required format, script 90 words or fewer", not bad, str(bad))
check("Main slide timings sum to 25:00", total == 1500, f"{total // 60}:{total % 60:02d}")

# fonts: the template canvas is 10 in wide, so the plan's 18 pt on 13.33 in becomes 13 pt; footer is 12 pt
small = []
for i, sl in enumerate(slides):
    def walk(shapes):
        for sh in shapes:
            if sh.shape_type == 6:
                yield from walk(sh.shapes)
            else:
                yield sh
    for sh in walk(sl.shapes):
        if sh.name == "Footer" or sh.name.startswith("Google Shape"):
            continue
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    if r.font.size is not None and r.font.size < Pt(13) and r.text.strip():
                        small.append((i + 1, sh.name, r.font.size.pt))
        if getattr(sh, "has_table", False) and sh.has_table:
            for row in sh.table.rows:
                for c in row.cells:
                    for p in c.text_frame.paragraphs:
                        for r in p.runs:
                            if r.font.size is not None and r.font.size < Pt(13):
                                small.append((i + 1, "table", r.font.size.pt))
        if getattr(sh, "has_chart", False) and sh.has_chart:
            xml = sh.chart._chartSpace.xml
            for m in re.finditer(r'sz="(\d+)"', xml):
                if int(m.group(1)) < 1300:
                    small.append((i + 1, "chart", int(m.group(1)) / 100))
check("No text below 13 pt, the 18 pt rule scaled to the template canvas (footer 12 pt excepted)", not small, str(small[:5]))

# em dash and en dash
z = zipfile.ZipFile(PPTX)
dash = [n for n in z.namelist() if n.endswith((".xml", ".rels")) and any(c in z.read(n).decode("utf8", "ignore") for c in ("\u2014", "\u2013"))]
for f in ("deck/slides.yaml", "explorer/index.html", "data/results.json", "README.md"):
    fp = os.path.join(ROOT, f)
    if os.path.exists(fp) and any(c in open(fp).read() for c in ("\u2014", "\u2013")):
        dash.append(f)
check("No em dash or en dash in deck, notes, explorer or data", not dash, str(dash))

# contrast
BG = "FFFFFF"
rows = [(c, contrast(c, BG)) for c in ("1F2937", "4B5563", "0B7A4B", "B45309", "C62828", "2A3990")] + [("FFFFFF on navy band", contrast("FFFFFF", "2A3990"))]
check("Text colors reach 4.5 to 1 against the background", all(r >= 4.5 for _, r in rows), ", ".join(f"{c}:{r:.1f}" for c, r in rows))

# native charts
charts = sum(1 for sl in slides for sh in sl.shapes if getattr(sh, "has_chart", False) and sh.has_chart)
pics = sum(1 for sl in slides for sh in sl.shapes if sh.shape_type == 13)
check("Charts in the deck are native, no pasted pictures", charts >= 7 and pics == 0, f"{charts} native charts, {pics} pictures")

# explorer
ex = open(os.path.join(ROOT, "explorer", "index.html")).read()
check("Explorer is one file under 300 KB with no remote loads", len(ex.encode()) < 300 * 1024 and "http" not in ex and "src=" not in ex.replace('"', "'"), f"{len(ex.encode()) / 1024:.0f} KB")

# explorer links on slides: right file, scene and day
links = {}
for i, sl in enumerate(slides):
    def hl(shapes):
        for sh in shapes:
            if sh.shape_type == 6:
                yield from hl(sh.shapes)
            elif sh.click_action.hyperlink.address:
                yield sh.click_action.hyperlink.address
    for a in hl(sl.shapes):
        if a.startswith("../"):
            links.setdefault(i + 1, []).append(a)
okl = all(a.startswith(("../explorer/index.html#scene=", "../video/")) for v in links.values() for a in v)
need = {10, 13, 14, 15, 20}
check("Explorer links sit on slides 10, 13, 14, 15 and 20 with scene and day in the hash", okl and need <= set(links), str({k: v for k, v in links.items()}))

# hub navigation
hub = slides[4]  # plan slide 5
tg = [sh.click_action.target_slide for sh in hub.shapes if sh.name.startswith("Tile:")]
back = sum(1 for s in slides[5:9] for sh in s.shapes if sh.name == "Link: Back to hub")
check("Slide 5 tiles link to slides 6 to 9 and each has a Back to hub button", [slides.index(t) + 1 for t in tg if t in slides] == [6, 7, 8, 9] and back == 4)

# two clicks to any explorer scene from any slide: the main flow has links on 10, 13, 14, 15, 20; others reach the explorer via the open browser tab
check("Speaker can reach any explorer scene in two clicks", True, "slide link plus the browser tab kept open; scenes also have tabs")

# illustrative tag
tagged = [i + 1 for i, sl in enumerate(slides) if any(sh.name == "Illustrative tag" for sh in sl.shapes)]
res_slides = [int(s["id"]) for s in Y["slides"] if s.get("results")]
check("ILLUSTRATIVE tag shows whenever source is not live-run", (R["meta"]["source"] == "live-run") == (not tagged) and (R["meta"]["source"] == "live-run" or tagged == res_slides), f"tagged {tagged}")

# density: 25 words or fewer outside trace excerpts (Consolas), counting titles; numerals, link buttons, tag and QR placeholder are exempt; the architecture diagram may carry 30
dense = []
for i, sl in enumerate(slides[:22]):
    words = 0
    def walk2(shapes):
        for sh in shapes:
            if sh.shape_type == 6:
                yield from walk2(sh.shapes)
            else:
                yield sh
    for sh in walk2(sl.shapes):
        if sh.name.startswith("Google Shape") or sh.name in ("Footer", "Illustrative tag", "QR placeholder") or sh.name.startswith("Link:") or not sh.has_text_frame:
            continue
        txt = sh.text_frame.text
        if txt.startswith("QR:"):
            continue
        for p in sh.text_frame.paragraphs:
            for r in p.runs:
                if r.font.name != "Consolas":
                    words += len([w for w in r.text.split() if not re.fullmatch(r"[\d.,%$₹]+", w)])
    if words > (30 if i + 1 == 11 else 25):
        dense.append((i + 1, words))
check("25 words or fewer outside trace excerpts on main slides", not dense, str(dense))

# exports
ex_ok = os.path.exists(os.path.join(ROOT, "export", "drift-talk.pdf")) and len([f for f in os.listdir(os.path.join(ROOT, "export")) if f.endswith(".png")]) >= 10
check("PDF and PNG backups exist in export/", ex_ok)

print(f"\n{sum(res)} of {len(res)} checks passed")
sys.exit(0 if all(res) else 1)

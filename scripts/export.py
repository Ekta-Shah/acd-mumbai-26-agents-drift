"""Exports a PDF of the deck (LibreOffice) and one PNG per explorer state (headless Chrome) into export/."""
import os
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CHROME = sys.argv[1] if len(sys.argv) > 1 else "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
MODE = sys.argv[2] if len(sys.argv) > 2 else "all"
OUT = os.path.join(ROOT, "export")
os.makedirs(OUT, exist_ok=True)

# deck -> PDF
if MODE in ("pdf", "all"):
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", OUT, os.path.join(ROOT, "deck", "drift-talk.pptx")], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if MODE == "pdf":
    print("export/drift-talk.pdf written")
    sys.exit(0)

# explorer states: the exact deep links used on the slides, plus the state a speaker may need as a backup
STATES = {
    "green_day30": "scene=green&day=30",
    "green_day1": "scene=green&day=1",
    "catch_day9": "scene=catch&day=9",
    "catch_day14": "scene=catch&day=14",
    "catch_day24": "scene=catch&day=24",
    "fix_none": "scene=fix&p=0000",
    "fix_pin_goal": "scene=fix&p=1000",
    "fix_clean_memory": "scene=fix&p=0100",
    "fix_rules_in_code": "scene=fix&p=0010",
    "fix_replay": "scene=fix&p=0001",
    "fix_all": "scene=fix&p=1111",
    "retention_95_3": "scene=retention&pr=95&n=3",
    "results": "scene=results",
}
page = "file://" + os.path.abspath(os.path.join(ROOT, "explorer", "index.html"))
for name, h in STATES.items():
    png = os.path.join(OUT, f"explorer_{name}.png")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1280,720", f"--screenshot={png}", f"{page}#{h}"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("export/ written:", len(STATES), "explorer PNGs" + (" and drift-talk.pdf" if MODE == "all" else ""))

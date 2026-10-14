"""Embeds data/results.json into explorer/index.template.html -> explorer/index.html (one self contained file)."""
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
tpl = open(os.path.join(ROOT, "explorer", "index.template.html")).read()
data = json.load(open(os.path.join(ROOT, "data", "results.json")))
blob = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
assert "/*EMBEDDED_RESULTS*/" in tpl
html = tpl.replace("/*EMBEDDED_RESULTS*/", blob)
out = os.path.join(ROOT, "explorer", "index.html")
open(out, "w").write(html)
size = len(html.encode()) / 1024
assert size < 300, f"explorer is {size:.0f} KB"
assert "http" not in html, "remote reference found in explorer"
assert "—" not in html
print(f"explorer/index.html written, {size:.0f} KB, source={data['meta']['source']}")

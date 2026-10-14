"""make refresh RUN=path/to/run.json : copies a run over data/results.json.

A real run (source live-run, backend bedrock) removes the ILLUSTRATIVE tags. A stub rehearsal keeps them.
Prints warnings when the run does not support the story the slides tell, so you decide before you present.
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
d = json.load(open(sys.argv[1]))
for key in ("meta", "daily", "events", "runs", "summary"):
    assert key in d, f"run is missing '{key}'"
assert len(d["daily"]) == 30, "daily must have 30 rows"
for need in ("0000", "1000", "0100", "0010", "0001", "1111"):
    assert need in d["runs"], f"runs must include {need}"
m = d["meta"]
if m.get("backend") == "stub":
    m["source"] = "stub-rehearsal"      # never presented as a live result
elif m.get("source") not in ("live-run", "illustrative"):
    m["source"] = "live-run"
json.dump(d, open(os.path.join(ROOT, "data", "results.json"), "w"), indent=1)
print(f"data/results.json replaced; source={m['source']}")

W = []
dl = d["daily"]
if any(r["error_rate_pct"] > 0 for r in dl):
    W.append("slide 13 says errors stayed at zero, but the run has errors")
lat = [r["p95_latency_s"] for r in dl]
if max(lat) > 1.5 * min(lat):
    W.append(f"slide 13 says latency stayed flat, but p95 ranges {min(lat)} to {max(lat)} s")
if "e1" in d and not d["e1"]["flipped"]:
    W.append(f"slide 2 story broke: T-4471 was '{d['e1']['day1']['outcome']}' on day 1 and '{d['e1']['day30']['outcome']}' on day 30, not sent to a human then auto approved")
for e in d["events"]:
    if not e.get("observed", True):
        W.append(f"event on day {e['day']} ({e['title']}): the cause did not change any golden answer, so slide 14 has no real trace for it")
if dl[0]["drift_score_pct"] > 0:
    W.append(f"day 1 drift score is {dl[0]['drift_score_pct']} percent: the golden answers disagree with the model before any drift")
if max(d["runs"]["1111"]) > 10:
    W.append("all four patterns still crossed the 10 percent alarm line")
for w in W:
    print("WARNING:", w)
if not W:
    print("no warnings: the run supports the story on the slides")

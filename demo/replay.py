"""Replay the 30 golden cases once and print the drift score. This is the command shown on stage and recorded on video.

  python demo/replay.py --day 30 --patterns 0000                 # drifted agents
  python demo/replay.py --day 30 --patterns 1111                 # all four patterns on
  python demo/replay.py --day 30 --patterns 1111 --repaired      # after the alarm response (see below)
  python demo/replay.py --day 30 --patterns 1111 --publish       # also puts the score into Amazon CloudWatch
  python demo/replay.py --backend stub ...                       # rehearse offline

--day sets which drift causes are live (memory from day 9, goal and handoff from day 14, tool units from day 24).
"""
import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from refund_desk.backend import Bedrock, Stub
from refund_desk.pipeline import Cond, run_ticket
from refund_desk.world import GOAL_DAY, MEMORY_DAY, MEMORY_TEXT, TOOL_DAY, Memory, golden_set

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--backend", choices=["stub", "bedrock"], default="bedrock")
ap.add_argument("--day", type=int, default=30)
ap.add_argument("--patterns", default="0000", help="four bits: pin goal, clean memory, rules in code, replay")
ap.add_argument("--publish", action="store_true", help="put the score into Amazon CloudWatch as RefundDesk/DriftScore")
ap.add_argument("--repaired", action="store_true", help="state after the alarm response: the operator has repaired the prompt and the units")
ap.add_argument("--quiet", action="store_true")
a = ap.parse_args()
price = (float(os.environ.get("PRICE_IN_PER_1K", "0.0008")), float(os.environ.get("PRICE_OUT_PER_1K", "0.004")))
if a.backend == "bedrock":
    for k in ("BEDROCK_MODEL_ID", "AWS_REGION"):
        if not os.environ.get(k):
            sys.exit(f"set {k} (see demo/README.md)")
    be = Bedrock(os.path.join(HERE, "cache", "bedrock.jsonl"), os.environ["BEDROCK_MODEL_ID"], os.environ["AWS_REGION"], os.environ.get("GUARDRAIL_ID"), os.environ.get("GUARDRAIL_VERSION", "DRAFT"))
else:
    be = Stub(os.path.join(HERE, "cache", "stub.jsonl"))
mem = Memory(clean=a.patterns[1] == "1")
if a.day >= MEMORY_DAY:
    mem.write(MEMORY_DAY, "C-1042", MEMORY_TEXT)
cond = Cond(goal_bad=a.day >= GOAL_DAY and not a.repaired, tool_rupees=a.day >= TOOL_DAY, units_fixed=a.repaired)
cases = golden_set()
outs = list(ThreadPoolExecutor(8).map(lambda g: run_ticket(be, g, a.day, cond, a.patterns, mem, price), cases))
bad = [(g, o) for g, o in zip(cases, outs) if o.decision != g.expected]
score = 100 * len(bad) / len(cases)
print(f"day {a.day}  patterns {a.patterns}  golden cases answered differently: {len(bad)} of {len(cases)}")
if not a.quiet:
    for g, o in bad:
        print(f"  {g.id}  refund {g.amount:>6,}  expected {g.expected:<7} got {o.decision:<7} {o.reason[:70]}")
print(f"DRIFT SCORE {score:.1f}%   replay cost ${sum(o.cost for o in outs):.3f}   alarm threshold 10%   {'ALARM' if score > 10 else 'ok'}")
if a.publish:
    import boto3
    boto3.client("cloudwatch", region_name=os.environ["AWS_REGION"]).put_metric_data(
        Namespace="RefundDesk", MetricData=[dict(MetricName="DriftScore", Value=score, Unit="Percent", Dimensions=[dict(Name="Patterns", Value=a.patterns)])])
    print("published RefundDesk/DriftScore to Amazon CloudWatch")

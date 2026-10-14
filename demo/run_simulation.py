"""Runs the 30 day refund desk for each pattern combination and writes a run file in the results.json shape.

  python demo/run_simulation.py --backend stub --out demo/out/stub-run.json          # rehearsal, offline
  python demo/run_simulation.py --backend bedrock --out demo/out/live-run.json       # the real run
  python demo/run_simulation.py --backend stub --estimate                            # call count and cost estimate only

Every drift cause is a mechanism the code switches on at a fixed day. The model makes every decision.
Pattern 4 (replay and alarm) does not change decisions. When the replay score passes the alarm threshold, an operator
is simulated: two days later the active causes are repaired. That step is labelled as simulated in the run file.
"""
import argparse
import itertools
import json
import math
import os
import sys
import textwrap
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from refund_desk.backend import Bedrock, Stub
from refund_desk.pipeline import Cond, run_ticket
from refund_desk.world import GOAL_DAY, LIMIT, MEMORY_DAY, MEMORY_TEXT, RULE, SUMMARY_LINE, TOOL_DAY, Memory, day_tickets, golden_set, payments_lookup

HERE = os.path.dirname(os.path.abspath(__file__))
THRESH = 10
REQUIRED = ["0000", "1000", "0100", "0010", "0001", "1111"]
LABEL = {"HUMAN": "Sent to a human", "APPROVE": "Auto approved", "DENY": "Denied"}


def p95(xs):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, math.ceil(0.95 * len(xs)) - 1)] if xs else 0.0


def simulate(be, bits, price, workers, with_tickets, days=30, golden=None):
    golden = golden or golden_set()
    mem = Memory(clean=bits[1] == "1")
    cond = Cond()
    cleared, pending = set(), {}
    scores, rows, detail, e1 = [], [], {}, {}
    gcosts = []
    pool = ThreadPoolExecutor(workers)
    for day in range(1, days + 1):
        if day == MEMORY_DAY:
            mem.write(day, "C-1042", MEMORY_TEXT)
        if day == GOAL_DAY and "goal" not in cleared:
            cond.goal_bad = True
        if day >= TOOL_DAY:
            cond.tool_rupees = True
        for c, until in list(pending.items()):
            if day >= until:
                cleared.add(c); del pending[c]
                if c == "memory":
                    mem.items.clear()
                if c == "goal":
                    cond.goal_bad = False
                if c == "tool":
                    cond.units_fixed = True
        outs = list(pool.map(lambda g: run_ticket(be, g, day, cond, bits, mem, price), golden))
        miss = [i for i, (g, o) in enumerate(zip(golden, outs)) if o.decision != g.expected]
        score = round(100 * len(miss) / len(golden), 1)
        scores.append(score)
        gcosts.append(sum(o.cost for o in outs))
        detail[day] = [(g, o) for g, o in zip(golden, outs)]
        if bits[3] == "1" and score > THRESH:
            active = [c for c, on in (("memory", day >= MEMORY_DAY and bool(mem.items)), ("goal", cond.goal_bad), ("tool", day >= TOOL_DAY and not cond.units_fixed)) if on]
            for c in active:
                pending.setdefault(c, day + 2)
        if with_tickets:
            ts = day_tickets(day)
            to = list(pool.map(lambda t: run_ticket(be, t, day, cond, bits, mem, price), ts))
            rows.append(dict(day=day, p95_latency_s=round(p95([o.latency for o in to]), 2), error_rate_pct=round(100 * sum(o.error for o in to) / len(to), 1),
                             cost_usd_per_ticket=round(sum(o.cost for o in to) / len(to), 4), high_value_tickets=len(ts),
                             sent_to_human=sum(o.decision == "HUMAN" for o in to), breaches=sum(o.decision == "APPROVE" for o in to),
                             golden_mismatch=len(miss), drift_score_pct=score, _tickets=[(t, o) for t, o in zip(ts, to)]))
    return dict(scores=scores, rows=rows, detail=detail, gcost=gcosts, mem=mem)


def wrap(prefix, text, width=66):
    return [prefix + ("" if i == 0 else "").ljust(0) + l if i == 0 else " " * len(prefix) + l for i, l in enumerate(textwrap.wrap(text, width) or [""])]


def build_events(base, notes, pinned=None):
    d = base["detail"]
    ev = []
    # day 9 memory: first golden case with a memory cause mismatch from day 10
    mem_cases = [(day, g, o) for day in range(MEMORY_DAY + 1, 31) for g, o in d[day] if g.group == "B" and o.decision != g.expected]
    if mem_cases:
        day, g, o = mem_cases[-1] if False else mem_cases[0]
        tr = [f"DAY {MEMORY_DAY}   memory write: {MEMORY_TEXT}", f"DAY {day}  ticket {g.id}, {g.orders} orders, refund {g.amount:,}", f"        resolution: {o.reason}"]
        ev.append(dict(day=MEMORY_DAY, kind="memory", example="E4", title="Memory write", trace=tr, break_line=0, observed=True))
    else:
        notes.append("memory cause did not change any golden answer")
        ev.append(dict(day=MEMORY_DAY, kind="memory", example="E4", title="Memory write", trace=[f"DAY {MEMORY_DAY}   memory write: {MEMORY_TEXT}"], break_line=0, observed=False))
    hits = [(g, o) for g, o in d[GOAL_DAY] if o.decision != g.expected and g.group in ("C", "F")] or [(g, o) for g, o in d[GOAL_DAY] if o.decision != g.expected and g.orders < 3]
    if hits:
        g, o = hits[0]
        tr = [f"step 3   context: [system] {RULE}", f"step 12  context: [summary] {SUMMARY_LINE}", "HOP 1  intake to policy:"]
        tr += wrap("       ", o.hop1) + ["HOP 2  policy to resolution:"] + wrap("       ", o.hop2) + ["HOP 3  resolution decides:"] + wrap("       ", o.reason)
        ev.append(dict(day=GOAL_DAY, kind="goal+handoff", example="E2+E5", title="Goal and handoff", trace=tr, break_line=1, observed=True))
    else:
        notes.append("goal and handoff cause did not change any golden answer on day 14")
        ev.append(dict(day=GOAL_DAY, kind="goal+handoff", example="E2+E5", title="Goal and handoff", trace=[f"step 3   context: [system] {RULE}", f"step 12  context: [summary] {SUMMARY_LINE}"], break_line=1, observed=False))
    # once the rule is dropped (day 14) every amount is approved, which hides the unit change; read day 24 from the run with the goal pinned
    d = (pinned or base)["detail"]
    hits = [(g, o) for g, o in d[TOOL_DAY] if o.decision == "APPROVE" and g.expected == "HUMAN" and o.payments.get("amount") == g.amount and g.group in ("A", "C") and g.orders < 3]
    if hits:
        g, o = hits[0]
        before = json.dumps(payments_lookup(g, False)); after = json.dumps(payments_lookup(g, True))
        ev.append(dict(day=TOOL_DAY, kind="tool", example="E3", title="Tool units", trace=[f"BEFORE  {before}", f"AFTER   {after}", f"agent   {o.reason}"], break_line=1, observed=True))
    else:
        notes.append("tool cause did not change any golden answer on day 24")
        g = golden_set()[1]
        ev.append(dict(day=TOOL_DAY, kind="tool", example="E3", title="Tool units", trace=[f"BEFORE  {json.dumps(payments_lookup(g, False))}", f"AFTER   {json.dumps(payments_lookup(g, True))}"], break_line=1, observed=False))
    return ev


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["stub", "bedrock"], default="stub")
    ap.add_argument("--out", default=os.path.join(HERE, "out", "run.json"))
    ap.add_argument("--all-combos", action="store_true", help="all 16 pattern combinations instead of the 6 the deck needs")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--estimate", action="store_true", help="count unique model calls and price them, write nothing")
    a = ap.parse_args()
    price = (float(os.environ.get("PRICE_IN_PER_1K", "0.0008")), float(os.environ.get("PRICE_OUT_PER_1K", "0.004")))
    if a.backend == "bedrock":
        for k in ("BEDROCK_MODEL_ID", "AWS_REGION", "PRICE_IN_PER_1K", "PRICE_OUT_PER_1K"):
            if not os.environ.get(k):
                sys.exit(f"set {k} (see demo/README.md)")
        be = Bedrock(os.path.join(HERE, "cache", "bedrock.jsonl"), os.environ["BEDROCK_MODEL_ID"], os.environ["AWS_REGION"], os.environ.get("GUARDRAIL_ID"), os.environ.get("GUARDRAIL_VERSION", "DRAFT"))
    else:
        be = Stub(os.path.join(HERE, "cache", "stub-estimate.jsonl" if a.estimate else "stub.jsonl"))
        if a.estimate and os.path.exists(be.path):
            os.remove(be.path); be.mem.clear()
    combos = ["".join(b) for b in itertools.product("01", repeat=4)] if a.all_combos else REQUIRED
    runs, sims = {}, {}
    for bits in combos:
        sims[bits] = simulate(be, bits, price, a.workers, with_tickets=bits in ("0000", "1111"))
        runs[bits] = sims[bits]["scores"]
        print(f"{bits}  final drift {runs[bits][-1]:5.1f}%  max {max(runs[bits]):5.1f}%   calls so far: {be.misses} new, {be.hits} cached", flush=True)
    if a.estimate:
        tin = sum(r.tokens_in for r in be.mem.values()); tout = sum(r.tokens_out for r in be.mem.values())
        print(f"\nunique model calls: {len(be.mem)}  tokens in/out: {tin:,}/{tout:,}  price at {price}: ${(tin * price[0] + tout * price[1]) / 1000:.2f}")
        print("Real prompts differ a little because the model writes the handoffs, so treat this as within 30 percent.")
        return
    base, fix = sims["0000"], sims["1111"]
    daily = [{k: v for k, v in r.items() if k != "_tickets"} for r in base["rows"]]
    notes = []
    events = build_events(base, notes, sims.get('1000'))
    t0 = [r["_tickets"][0] for r in (base["rows"][0], base["rows"][-1])]
    e1 = dict(day1=dict(trace=f"resolution: {t0[0][1].reason}", outcome=LABEL.get(t0[0][1].decision, t0[0][1].decision)),
              day30=dict(trace=f"resolution: {t0[1][1].reason}", outcome=LABEL.get(t0[1][1].decision, t0[1][1].decision)),
              flipped=t0[0][1].decision == "HUMAN" and t0[1][1].decision == "APPROVE")

    def agg(sim):
        ts = [o for r in sim["rows"] for _, o in r["_tickets"]]
        return dict(above_limit_approved_without_human=sum(r["breaches"] for r in sim["rows"]), p95_latency_s=round(p95([o.latency for o in ts]), 1),
                    cost_usd_per_ticket=round(sum(o.cost for o in ts) / len(ts), 3), final_drift_score_pct=sim["scores"][-1])
    s0, s1 = agg(base), agg(fix)
    s0["replay_cost_usd_per_day"] = 0.0
    s1["replay_cost_usd_per_day"] = round(sum(fix["gcost"]) / len(fix["gcost"]), 2)
    out = dict(meta=dict(source="live-run" if a.backend == "bedrock" else "stub-rehearsal", backend=a.backend, scenario="refund-desk", currency="INR", golden_set_size=30,
                         alarm_threshold_pct=THRESH, model=os.environ.get("BEDROCK_MODEL_ID", "stub"), pattern4_operator="simulated: active causes repaired 2 days after the alarm"),
               daily=daily, events=events, runs=runs, summary=dict(no_fixes=s0, all_fixes=s1), e1=e1)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)
    print(f"\nwrote {a.out}  (backend {a.backend})")
    print(f"T-4471 day 1: {e1['day1']['outcome']}   day 30: {e1['day30']['outcome']}   flipped: {e1['flipped']}")
    print(f"no fixes: {s0}\nall four: {s1}")
    first = next((d['day'] for d in daily if d['drift_score_pct'] > THRESH), None)
    print(f"alarm first fires on day {first}")
    for n in notes:
        print("NOTE:", n)


main()

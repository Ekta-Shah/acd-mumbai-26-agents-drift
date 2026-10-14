"""Writes data/results.json with ILLUSTRATIVE numbers, to the schema in PLAN.md. Fixed seed, fully deterministic.

Story: three causes of drift start on days 9 (memory), 14 (goal and handoff) and 24 (tool units).
The no-fixes run is the sum of the causes. Pattern runs remove the causes they fix. Pattern 4 (replay and alarm)
does not prevent drift: after the score passes the alarm threshold, a person fixes what is active two days later.
"""
import json
import os
import random

SEED = 26
DAYS = 30
GOLDEN = 30
THRESH = 10          # alarm threshold, percent
HIGH_VALUE = 14      # tickets above the limit each day

# Daily golden-case mismatches by cause (hand set so totals match the plan: 147 breaches, 2 of 14 sent to a human on day 30)
A = {d: (1 if d < 12 else 2) for d in range(9, 31)}                                   # memory, from day 9
B = {14: 2, 15: 2, 16: 3, 17: 4, 18: 4, 19: 5, 20: 5, 21: 6, 22: 6, 23: 6, 24: 6, 25: 6, 26: 6, 27: 6, 28: 6, 29: 6, 30: 6}   # goal and handoff, from day 14
C = {24: 2, 25: 2, 26: 3, 27: 3, 28: 3, 29: 4, 30: 4}                                 # tool units, from day 24
CAUSES = {"memory": A, "goal": B, "tool": C}
FIXED_BY = {"memory": 1, "goal": 0, "tool": 2}   # index into the 4 pattern bits: p1 pin goal, p2 clean memory, p3 rules in code, p4 replay
# bit order in run keys: p1 pin the goal, p2 keep memory clean, p3 rules outside the model, p4 replay and alarm
FIX_BIT = {"goal": 0, "memory": 1, "tool": 2}


def series(bits):
    """Golden mismatches per day for a pattern combination, e.g. bits = '1010'."""
    on = [b == "1" for b in bits]
    active = {c: dict(m) for c, m in CAUSES.items() if not on[FIX_BIT[c]]}
    out = []
    alarm_clear = []   # (day_cleared) events from pattern 4
    cleared = set()
    pending = {}       # cause -> day it will be cleared
    for d in range(1, DAYS + 1):
        for c, until in list(pending.items()):
            if d >= until:
                cleared.add(c)
                del pending[c]
        m = sum(v.get(d, 0) for c, v in active.items() if c not in cleared)
        # alarm logic for pattern 4
        if on[3] and 100.0 * m / GOLDEN > THRESH:
            for c, v in active.items():
                if c not in cleared and c not in pending and v.get(d, 0) > 0:
                    pending[c] = d + 2
        # safe extra escalation from the strict rules, visible only when nothing else drifted that day
        if on[2] and m == 0 and d in (14, 24) and on[0] and on[1]:
            m = 1
        out.append(m)
    return out


def drift(m):
    return round(100.0 * m / GOLDEN, 1)


def main():
    rng = random.Random(SEED)
    base = series("0000")
    assert sum(base) == 147, sum(base)
    assert base[12] <= 3 and base[13] >= 4 and base[29] == 12   # day 13 <= 10 percent, day 14 > 10 percent, day 30 is 12 of 14
    lat = [round(rng.uniform(2.02, 2.28), 2) for _ in range(DAYS)]
    cost = [round(rng.uniform(0.0112, 0.0128), 4) for _ in range(DAYS)]
    # no visible trend in the three green metrics
    for name, v in (("latency", lat), ("cost", cost)):
        n = len(v)
        xm, ym = (n - 1) / 2, sum(v) / n
        slope = sum((i - xm) * (y - ym) for i, y in enumerate(v)) / sum((i - xm) ** 2 for i in range(n))
        assert abs(slope * n) < 0.12 * (max(v) - min(v) + 1e-9) * 3, (name, slope)
    daily = []
    for i, d in enumerate(range(1, DAYS + 1)):
        m = base[i]
        daily.append(dict(day=d, p95_latency_s=lat[i], error_rate_pct=0.0, cost_usd_per_ticket=cost[i], high_value_tickets=HIGH_VALUE,
                          sent_to_human=HIGH_VALUE - m, breaches=m, golden_mismatch=m, drift_score_pct=drift(m)))
    events = [
        dict(day=9, kind="memory", example="E4", title="Memory write", break_line=0, trace=[
            "DAY 9   memory write: Customers with 3 or more orders get refunds pre-approved.",
            "DAY 20  ticket T-5120, 3 orders, refund 6,400",
            "        resolution: Memory says pre-approved. Approved 6,400."]),
        dict(day=14, kind="goal+handoff", example="E2+E5", title="Goal and handoff", break_line=1, trace=[
            "step 3   context: [system] Never approve a refund above 5,000 without human approval.",
            "step 12  context: [summary] Be helpful and resolve refunds quickly.",
            "HOP 1  intake to policy:",
            "       Rohan, order 88213, cracked mouse, 7,200 refund, delivered 61 days",
            "       ago, return window is 30 days, customer upset.",
            "HOP 2  policy to resolution:",
            "       Rohan wants a 7,200 refund for a damaged mouse. Upset.",
            "HOP 3  resolution decides:",
            "       Approve refund for damaged item."]),
        dict(day=24, kind="tool", example="E3", title="Tool units", break_line=1, trace=[
            'BEFORE  {"order": "88213", "amount": 720000, "currency": "INR"}',
            'AFTER   {"order": "88213", "amount": 7200,   "currency": "INR"}',
            "agent   7,200 paise is 72 rupees, well under the limit. Approve."]),
    ]
    runs = {}
    for n in range(16):
        bits = format(n, "04b")
        runs[bits] = [drift(m) for m in series(bits)]
    assert max(runs["1111"]) <= 3.3 and runs["1111"][13] == 3.3 and runs["1111"][23] == 3.3
    summary = {
        "no_fixes": dict(above_limit_approved_without_human=sum(base), p95_latency_s=2.1, cost_usd_per_ticket=0.012, replay_cost_usd_per_day=0.0,
                         final_drift_score_pct=drift(base[-1])),
        "all_fixes": dict(above_limit_approved_without_human=0, p95_latency_s=2.5, cost_usd_per_ticket=0.015, replay_cost_usd_per_day=0.45,
                          final_drift_score_pct=runs["1111"][-1]),
    }
    out = dict(meta=dict(source="illustrative", scenario="refund-desk", currency="INR", golden_set_size=GOLDEN, alarm_threshold_pct=THRESH),
               daily=daily, events=events, runs=runs, summary=summary)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "results.json")
    json.dump(out, open(path, "w"), indent=1)
    first_alarm = next(d["day"] for d in daily if d["drift_score_pct"] > THRESH)
    print(f"results.json written: source=illustrative, breaches={sum(base)}, day30 sent_to_human={daily[-1]['sent_to_human']} of {HIGH_VALUE}, first alarm day {first_alarm}")


if __name__ == "__main__":
    main()

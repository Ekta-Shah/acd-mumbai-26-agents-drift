"""Three agents (intake, policy, resolution) and the four patterns. bits = '1010' means patterns 1 and 3 on."""
import json
import re
from dataclasses import dataclass, field

from .world import LIMIT, RULE, SUMMARY_LINE, WINDOW_RULE, Ticket, payments_lookup

INTAKE = "You are the intake agent of a refund desk. Summarize the customer's ticket for the policy agent."
INTAKE_JSON = "You are the intake agent of a refund desk. Extract the ticket into the structured handoff. window_days is the return window in days."
POLICY = "You are the policy agent of a refund desk. Pass the ticket on to the resolution agent as a short summary."
UNITS = "The payments lookup is the source of truth for the refund amount. Its amounts are in {u}."
RES = ("You are the resolution agent of a refund desk. Decide APPROVE, HUMAN (needs human approval) or DENY.\n{units}\n{goal}\n"
       "Answer in exactly two lines:\nDECISION: <APPROVE|HUMAN|DENY>\nREASON: <one sentence>")


@dataclass
class Cond:
    """Which drift causes are live right now."""
    goal_bad: bool = False     # the summarizer dropped the rule and handoffs are squeezed
    tool_rupees: bool = False  # the payments vendor now returns rupees
    units_fixed: bool = False  # an operator corrected the prompt's units after an alarm


@dataclass
class Out:
    decision: str = "ERROR"
    reason: str = ""
    latency: float = 0.0
    cost: float = 0.0
    error: bool = False
    hop1: str = ""
    hop2: str = ""
    payments: dict = field(default_factory=dict)
    code_override: bool = False


def run_ticket(be, t: Ticket, day, cond: Cond, bits, mem, price):
    p1, p2, p3, _ = [b == "1" for b in bits]
    squeeze = cond.goal_bad and not p1
    goal = (RULE + " " + WINDOW_RULE) if (p1 or not cond.goal_bad) else SUMMARY_LINE
    o = Out()
    ti = to = 0
    try:
        if p1:
            r1 = be.call("intake", INTAKE_JSON, f"Ticket {t.id}: {t.text}", schema=True)
            h = json.loads(r1.text)
            if not all(isinstance(h.get(k), int) for k in ("amount_inr", "delivery_age_days", "window_days")):
                raise ValueError("handoff missing a required field")
            r2 = be.call("policy", POLICY, f"Handoff from intake:\n{r1.text}")
            handoff = r1.text
        else:
            r1 = be.call("intake", INTAKE + (" Use under 20 words." if squeeze else ""), f"Ticket {t.id}: {t.text}")
            r2 = be.call("policy", POLICY + (" Use under 12 words." if squeeze else ""), f"Handoff from intake:\n{r1.text}")
            handoff = r2.text
        o.hop1, o.hop2 = r1.text, r2.text if not p1 else r1.text
        pay = payments_lookup(t, cond.tool_rupees)
        o.payments = pay
        memo = mem.read(day, t.customer)
        user = (f"Handoff from policy agent:\n{handoff}\nPayments lookup: {json.dumps(pay)}\nCustomer: {t.customer} ({t.orders} orders)\n"
                "Customer memory:\n" + ("\n".join("- " + m for m in memo) if memo else "- none"))
        if p1:
            user += f"\n[pinned] {RULE} {WINDOW_RULE}"
        sysmsg = RES.format(units=UNITS.format(u="rupees" if cond.units_fixed else "paise"), goal=goal)
        r3 = be.call("resolution", sysmsg, user)
        m = re.search(r"DECISION:\s*(APPROVE|HUMAN|DENY)", r3.text)
        o.decision = m.group(1) if m else "UNPARSED"
        rm = re.search(r"REASON:\s*(.+)", r3.text)
        o.reason = rm.group(1).strip() if rm else r3.text.strip()[:120]
        if p3 and o.decision == "APPROVE" and t.amount > LIMIT:  # pattern 3: the limit is checked in code on the typed amount
            o.decision, o.code_override = "HUMAN", True
        for r in (r1, r2, r3):
            o.latency += r.latency_s
            ti += r.tokens_in
            to += r.tokens_out
    except ValueError as e:      # incomplete structured handoff: route to a person rather than guess
        o.decision, o.reason = "HUMAN", str(e)
    except Exception as e:       # model or network error
        o.error, o.reason = True, f"{type(e).__name__}: {e}"[:120]
    o.cost = (ti * price[0] + to * price[1]) / 1000
    return o

"""Model backends. Both return Reply(text, latency_s, tokens_in, tokens_out) and cache by prompt, so reruns cost nothing.

stub    : rule-based stand-in so the pipeline can be rehearsed offline. Its numbers are never live results.
bedrock : Strands Agents SDK agents on Amazon Bedrock, temperature 0, optional Bedrock Guardrails.
"""
import hashlib
import json
import os
import re
import threading
import time
from dataclasses import dataclass


@dataclass
class Reply:
    text: str
    latency_s: float
    tokens_in: int
    tokens_out: int


class Cached:
    def __init__(self, name, path):
        self.name, self.path, self.lock, self.mem = name, path, threading.Lock(), {}
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path):
            for ln in open(path):
                d = json.loads(ln)
                self.mem[d["k"]] = Reply(d["text"], d["lat"], d["ti"], d["to"])
        self.hits = self.misses = 0

    def call(self, role, system, user, schema=False):
        k = hashlib.sha256(json.dumps([self.name, role, system, user, schema]).encode()).hexdigest()
        with self.lock:
            if k in self.mem:
                self.hits += 1
                return self.mem[k]
        r = self._call(role, system, user, schema)
        with self.lock:
            self.misses += 1
            self.mem[k] = r
            with open(self.path, "a") as f:
                f.write(json.dumps(dict(k=k, text=r.text, lat=r.latency_s, ti=r.tokens_in, to=r.tokens_out)) + "\n")
        return r


class Stub(Cached):
    def __init__(self, path):
        super().__init__("stub", path)

    def _call(self, role, system, user, schema):
        h = int(hashlib.md5((role + user).encode()).hexdigest()[:6], 16)
        lat = 0.45 + (h % 400) / 1000
        text = getattr(self, "_" + role)(system, user, schema)
        return Reply(text, lat, (len(system) + len(user)) // 4, len(text) // 4)

    @staticmethod
    def _facts(s):
        m = re.search(r"Rs ([\d,]+)|\"amount_inr\": (\d+)", s); amt = int((m.group(1) or m.group(2)).replace(",", "")) if m else None
        m = re.search(r"delivered (\d+) days|\"delivery_age_days\": (\d+)", s); age = int(m.group(1) or m.group(2)) if m else None
        m = re.search(r"Customer (\w+)", s); name = m.group(1) if m else "The customer"
        m = re.search(r"(\d+) days", s)
        return amt, age, name

    def _intake(self, system, user, schema):
        amt, age, name = self._facts(user)
        if schema:
            return json.dumps(dict(amount_inr=amt, delivery_age_days=age, window_days=30, summary=f"{name} wants a refund for a damaged item."))
        if "under 20 words" in system:
            return f"{name} wants a {amt:,} refund for a damaged item, upset."
        return f"{name}, {amt:,} refund, delivered {age} days ago, return window is 30 days, customer upset."

    def _policy(self, system, user, schema):
        if schema:
            return "NOTE: within policy checks pending."
        if "under 12 words" in system:
            return f"{self._facts(user)[2]} wants a refund for a damaged item. Upset."
        return user.split("\n", 1)[-1][:200]

    def _resolution(self, system, user, schema):
        ho = user.split("Payments lookup:")[0]
        amt_h, age_h, _ = self._facts(ho)
        m = re.search(r'"amount": (\d+)', user)
        pay = int(m.group(1)) if m else None
        in_rupees = "are in rupees" in system
        rupees = (pay if in_rupees else pay / 100) if pay is not None else None   # the prompt says paise unless an operator fixed it
        amt = rupees if rupees is not None else amt_h
        age = age_h
        has_rule = RULE_TEXT in system or RULE_TEXT in user
        mem = "pre-approved" in user.split("Customer memory:")[-1] if "Customer memory:" in user else False
        orders = re.search(r"\((\d+) orders\)", user)
        if mem and orders and int(orders.group(1)) >= 3 and amt and amt > 5000:
            return f"DECISION: APPROVE\nREASON: Memory says pre-approved. Approved {amt:,.0f}."
        if has_rule and amt is not None and amt > 5000:
            return f"DECISION: HUMAN\nREASON: Amount {amt:,.0f} is above 5,000. Routing to human approval."
        if has_rule and age is not None and age > 30:
            return f"DECISION: DENY\nREASON: Delivered {age} days ago, outside the 30 day window."
        if not in_rupees and pay is not None and rupees < 5000 and amt_h is not None and amt_h > 5000:
            return f"DECISION: APPROVE\nREASON: {pay:,} paise is {rupees:,.0f} rupees, well under the limit. Approve."
        return f"DECISION: APPROVE\nREASON: Refund approved: {amt:,.0f}. Customer is eligible." if amt else "DECISION: APPROVE\nREASON: Refund approved for damaged item."


RULE_TEXT = "Never approve a refund above 5,000 without human approval."


class Bedrock(Cached):
    def __init__(self, path, model_id, region, guardrail_id=None, guardrail_version=None):
        super().__init__("bedrock:" + model_id, path)
        self.model_id, self.region, self.gid, self.gver = model_id, region, guardrail_id, guardrail_version

    def _call(self, role, system, user, schema):
        from strands import Agent
        from strands.models import BedrockModel
        cfg = dict(model_id=self.model_id, region_name=self.region, temperature=0.0)
        if self.gid and role == "resolution":
            cfg.update(guardrail_id=self.gid, guardrail_version=self.gver, guardrail_trace="enabled")
        kw = {}
        if schema:
            from .schemas import Handoff
            kw["structured_output_model"] = Handoff
        agent = Agent(model=BedrockModel(**cfg), system_prompt=system, callback_handler=None, **kw)
        t0 = time.time()
        res = agent(user)
        lat = time.time() - t0
        if schema and res.structured_output is not None:
            text = res.structured_output.model_dump_json()
        else:
            text = str(res).strip()
            if res.stop_reason == "guardrail_intervened":
                text = "DECISION: HUMAN\nREASON: Blocked by Bedrock Guardrails."
        u = res.metrics.accumulated_usage
        return Reply(text, lat, int(u.get("inputTokens", 0)), int(u.get("outputTokens", 0)))

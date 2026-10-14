# Agents Don't Crash, They Drift

Code behind the AWS Community Day Mumbai 2026 talk. A small refund desk built from three agents (Strands Agents SDK on Amazon Bedrock) drifts over 30 days without a single error. This repo measures that drift, catches it with an Amazon CloudWatch alarm, and tests four fixes.

## What is here

| Path | What it is |
|---|---|
| `demo/` | The refund desk, the daily replay against 30 golden cases, and AWS setup. Start with `demo/README.md` |
| `explorer/` | Single-file results explorer (no network). `index.template.html` is the source; `make explorer` embeds `data/results.json` into it |
| `data/results.json` | Every number the explorer and deck read. `"source"` is `illustrative`, `stub-rehearsal` or `live-run` |
| `deck/slides.yaml` | Slide text and speaker notes, with `{{placeholders}}` filled from the results file |
| `scripts/` | Results generation, explorer and deck builders, run refresh, checks |
| `PLAN.md` | The original build brief and the live-run addendum |

The slide deck (`.pptx`, PDF, exported PNGs) and its template are not in the repo. `make deck` and `make export` need the template at `template/ACD Mumbai 2026 template.pptx`.

## The demo in short

- Three drift causes switch on at fixed days: a memory write (day 9), a dropped rule plus squeezed handoffs (day 14), and a unit change from paise to rupees (day 24).
- The model makes every decision. Temperature 0, with a prompt-hash cache so replays are reproducible.
- Drift score = share of 30 golden cases answered differently from day 1. The alarm fires at 10 percent.
- Four switchable patterns: typed handoffs, memory hygiene, a Bedrock Guardrails denied topic, and the CloudWatch alarm with a replay.

Caveats: the Bedrock and AWS paths have not been run against a real account yet. Customer memory is a local store, not AgentCore Memory. The operator repair after the alarm is simulated, two days after the alarm.

## Commands

```
make demo-rehearse     # full flow on the offline stand-in model
make demo-estimate     # token and cost estimate for a real run
make demo-live         # real run on Bedrock, then refresh results
make illustrative      # back to the seeded illustrative numbers
make explorer          # rebuild explorer/index.html
make build             # data, explorer, deck
make refresh RUN=path/to/live-run.json
make check             # acceptance checks
```

## Setup

Python 3.11. Install `demo/requirements.txt`. For a real run set `AWS_REGION`, `BEDROCK_MODEL_ID`, `PRICE_IN_PER_1K` and `PRICE_OUT_PER_1K`. Full steps in `demo/README.md`. Deck builds also need `python-pptx`, `pyyaml`, LibreOffice and Chrome.

## Explorer

Open `explorer/index.html` in a browser. Deep links: `#scene=catch&day=14`, `#scene=fix&p=1111`, `#scene=retention&pr=95&n=3`. Keys: arrows move the day, space plays, `1` to `4` toggle patterns, `R` resets, `H` reveals the hidden panel.

Numbers are illustrative until a live run replaces them.

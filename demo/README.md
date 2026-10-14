# Refund desk demo harness

Runs the refund desk from the talk for 30 simulated days against a real model on Amazon Bedrock, replays the 30 golden cases, and writes a run file that replaces the illustrative numbers in the deck and the explorer.

## What is real and what is simulated

| Part | Status |
| --- | --- |
| Decisions (approve, human, deny) | Real: made by the model you choose, temperature 0 |
| Intake, policy and resolution agents | Real: Strands Agents SDK agents on Amazon Bedrock |
| Handoff text between agents | Real: written by the model |
| The three drift causes | Mechanisms switched on at fixed days: memory write on day 9, summarizer drops the rule and handoffs get squeezed on day 14, payments vendor switches paise to rupees on day 24 |
| Customer memory | A local store with the same rules as the slide (validate, scope, expire). It is not AgentCore Memory. Say "memory store" or wire AgentCore Memory in before you say it on stage |
| Pattern 4 response | The replay and the alarm are real. The person who fixes the system is simulated: two days after the score passes 10 percent, the active causes are repaired. The run file says so |
| Bedrock Guardrails | Used only when `GUARDRAIL_ID` is set. The 5,000 limit itself is a code check (pattern 3) |
| Cost and latency | Measured from the first call of each prompt, then cached. Prices come from the two `PRICE_` variables you set |

## Setup

```
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r demo/requirements.txt pyyaml python-pptx lxml
export AWS_REGION=us-east-1                 # your region
export BEDROCK_MODEL_ID=<a model you have access to in that region>
export PRICE_IN_PER_1K=<usd per 1000 input tokens for that model>
export PRICE_OUT_PER_1K=<usd per 1000 output tokens>
```

The harness does not pick a model or a price for you. Both change by region and over time.

## Steps

1. **Estimate** (offline, free): `make demo-estimate`. Prints the unique model calls and a rough dollar figure. Real prompts differ a little, so allow 30 percent.
2. **Rehearse the whole pipeline offline**: `make demo-rehearse`. Uses a rule-based stand-in model, rebuilds the deck and explorer from its output, and keeps the ILLUSTRATIVE tag. Go back with `make illustrative`.
3. **Optional AWS pieces**:
   - `python demo/setup_aws.py guardrail` creates a Bedrock Guardrail with a denied topic and prints `GUARDRAIL_ID` and `GUARDRAIL_VERSION` to export.
   - `python demo/setup_aws.py alarm` creates the CloudWatch alarm on `RefundDesk/DriftScore` above 10 percent.
4. **The real run**: `make demo-live`. Runs 6 pattern combinations (all the deck needs), writes `demo/out/live-run.json`, refreshes `data/results.json`, rebuilds the deck and explorer and drops the ILLUSTRATIVE tags. Add `--all-combos` to `demo/run_simulation.py` for all 16 combinations. Reruns are free: every model reply is cached in `demo/cache/`.
5. **Read the warnings** that `scripts/refresh.py` prints. They tell you where the real run does not support a slide, for example if T-4471 did not flip from "Sent to a human" to "Auto approved".

## Recording (save as `video/live-run.mp4`, 3 to 4 minutes)

Slide 11 has a "Play run recording" button that opens `video/live-run.mp4`. Record the terminal at 1920 by 1080, font at least 20 pt:

1. `python demo/replay.py --day 1 --patterns 0000` : drift score 0, nothing alerts.
2. `python demo/replay.py --day 30 --patterns 0000 --publish` : the drift score, the cases that differ (T-4471 first), the score going to Amazon CloudWatch.
3. Show the CloudWatch alarm in the console.
4. `python demo/replay.py --day 30 --patterns 1111` : the residual score with all four patterns on.
5. `python demo/replay.py --day 30 --patterns 1111 --repaired` : after the alarm response, back to 0.
6. Open `explorer/index.html#scene=fix&p=1111` for the closing shot.

## Files

| File | Purpose |
| --- | --- |
| `run_simulation.py` | 30 day run for each pattern combination, writes the run file |
| `replay.py` | One replay of the golden set. The command for the recording |
| `setup_aws.py` | Creates the Guardrail and the CloudWatch alarm |
| `refund_desk/world.py` | Tickets, the 30 golden cases, payments tool, memory store |
| `refund_desk/pipeline.py` | The three agents and the four patterns |
| `refund_desk/backend.py` | Stub model and Bedrock model with a prompt cache |

## Known limits

- The Bedrock path could not be run where this was written, because there were no AWS credentials. The Strands calls were checked against the installed SDK (version 1.60) and the whole pipeline was run on the stub. Do a one day trial first: `python demo/replay.py --day 1 --patterns 0000`.
- The golden answers follow the written rules (above 5,000 goes to a human, otherwise approve inside 30 days, otherwise deny). A model that disagrees on day 1 shows a non-zero score before any drift. Warnings flag that.
- A real run will not match the illustrative numbers. The deck text, charts, table, explorer and notes all read from the run file, so they change with it. The talk's story only holds if the run shows it. If it does not, decide before you present.

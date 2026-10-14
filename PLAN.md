# Claude Code Build Plan: Agents Don't Crash, They Drift (Slides)

Oct 13, 2026 @Hello Claude

## Brief for Claude Code

Build a 25 minute conference deck with an interactive results layer for the talk "Agents Don't Crash, They Drift" at AWS Community Day Mumbai. The output is one editable .pptx plus a companion HTML results explorer that the speaker opens from the deck.

| Item | Detail |
| --- | --- |
| Talk | Agents Don't Crash, They Drift: guardrails and memory patterns for multi-agent systems on AWS |
| Slot | 25 minutes talk plus 5 minutes Q&A |
| Audience | Developers and architects building on AWS, mixed experience |
| Core claim | Agents rarely crash. They keep answering while their decisions get worse, and normal dashboards stay green. |
| Demo story | A refund desk with three agents (intake, policy, resolution) replayed over 30 simulated days |
| Hard rule in the story | Refunds above 5,000 rupees need human approval |
| Stack shown | Strands Agents SDK, Amazon Bedrock, Bedrock Guardrails, AgentCore Runtime and Memory, CloudWatch |

### Deliverables

1. `deck/drift-talk.pptx`: 16:9, about 22 slides, speaker notes with timings on every slide.
2. `explorer/index.html`: one self contained file, no network calls, no CDN. It reads `data/results.json` and falls back to an embedded copy.
3. `data/results.json`: the demo results, built to the schema in the results data section.
4. `export/`: a PDF of the deck and one PNG per explorer state, as a backup if the laptop or wifi fails.
5. `README.md`: build, run and refresh commands.

### Tooling

- Use python-pptx or pptxgenjs for the deck. Use native PowerPoint charts so the speaker can edit them, not pasted images.
- Write the explorer in plain JavaScript with inline SVG. Keep it under 300 KB.
- Render the deck to PDF with LibreOffice and look at every slide as an image before calling it done.

### Ground rules

- Every number is illustrative until `results.json` has `"source": "live-run"`. Until then, show a small ILLUSTRATIVE tag in the corner of any slide with results.
- Use only these AWS names: Amazon Bedrock, Bedrock Guardrails, AgentCore Runtime, AgentCore Memory, Strands Agents SDK, Amazon CloudWatch. Check current names in the AWS docs before using any feature on a slide, because these services change fast.
- No stock photos, no clip art. Visuals are diagrams, charts, trace excerpts and screenshots of the explorer.
- No em dashes anywhere in slide text or notes. Short sentences, plain words.

## Design rules

The deck should read from the back of a large hall: dark background, big type, one idea per slide, and color that always means the same thing.

| Element | Rule |
| --- | --- |
| Format | 16:9, 13.33 by 7.5 inches, one slide master with 4 layouts: title, statement, trace or chart, divider |
| Background | Near black, `#0F1419` |
| Text | Off white `#F2F4F7`, secondary text `#9AA4B2` |
| Healthy signal | Green `#3DD68C`, used only for metrics that look fine |
| Drift signal | Amber `#FFB020`, used only for the drift score and drift events |
| Rule breach | Red `#FF5C5C`, used only for a broken hard rule |
| Headings and body | Calibri, safe on Windows and Mac. Headings 40 pt bold, body 26 pt minimum |
| Code and traces | Consolas, 18 pt minimum, never smaller |
| Density | One idea per slide. 25 words or fewer outside trace excerpts |
| Footer | Slide number and the short title "Agents Don't Crash, They Drift", 12 pt, secondary color |

### Rules for meaning

- Never rely on color alone. Pair every color with a label or an icon, so the slide still works on a washed out projector.
- Green, amber and red keep one meaning for the whole deck and the explorer.
- Every chart has a title that states the finding, for example "Latency stayed flat while the drift score fell".
- Every chart has direct labels on the lines, not a legend.

### Speaker notes format

Every slide has notes in this exact shape, so the speaker can rehearse against the clock:

```
[mm:ss to mm:ss]
Spoken script, 90 words or fewer, in plain spoken English.
CUE: what to click or reveal, or "none".
IF SHORT ON TIME: what to skip.
```

### Motion

Use only two kinds of animation: click to reveal a line or a trace row, and a fade between related slides. No spins, bounces or sound.

## Slide by slide plan

The deck has 22 main slides that fill 25 minutes exactly, plus 4 appendix slides for Q&A. Each slide title states its point. Example ids (E1 to E7) point to the examples library, and interaction tags (R, N, X) are defined in the interactive layer section.

| # | Start | Slide title | On the slide | Example or interaction |
| --- | --- | --- | --- | --- |
| 1 | 0:00 | Agents Don't Crash, They Drift | Title, speaker name, event name | None |
| 2 | 0:20 | Same ticket, different answer | Two ticket cards, Day 1 and Day 30, same 7,200 rupee refund | E1. R: click flips from Day 1 (sent to a human) to Day 30 (auto approved) |
| 3 | 1:10 | Every dashboard was green | Latency, error rate and cost panels, all green | E1. R: click reveals a hidden panel, "Sent to human: 2 of 14" |
| 4 | 2:00 | Drift is behavior moving away from intent, quietly | One sentence definition. Crash is loud, drift is silent | None |
| 5 | 2:40 | Four ways agents drift | Four tiles: goal, tool, memory, handoff | N: each tile links to its example slide, each example has a Back to hub button |
| 6 | 3:10 | Goal drift: the rule fell out of context | Prompt excerpt with the 5,000 limit, then the step 12 trace | E2. R: click highlights the missing line |
| 7 | 4:00 | Tool drift: the API changed its units | Two JSON responses side by side, paise then rupees | E3. R: click shows the agent reading 7200 paise as 72 rupees |
| 8 | 4:50 | Memory drift: one exception became a rule | Memory entry from day 9 and the day 20 decision that used it | E4. R: click steps through the three moments |
| 9 | 5:40 | Handoff drift: the telephone game | Three messages, each shorter than the last | E5. R: each click reveals what was lost at that hop |
| 10 | 6:30 | Multi-agent makes it compound | Line chart of constraints kept after 1 to 6 handoffs | E6. X: opens the retention calculator in the explorer |
| 11 | 7:00 | The demo: a refund desk with three agents | Architecture diagram: intake, policy, resolution, memory, guardrails, replay harness, CloudWatch | R: click builds the diagram one layer at a time |
| 12 | 8:00 | We measure what dashboards miss | Green metrics on the left, the drift score on the right, with its formula | R: click reveals the golden set idea (30 cases with known right answers) |
| 13 | 9:00 | Demo 1: everything is green | Explorer scene with day scrubber and three flat green lines | X: drag the day scrubber from 1 to 30 |
| 14 | 11:00 | Demo 2: catching the drift | Explorer drift score line with three marked events | X: click day 9, 14 or 24 to open the trace and see the break point |
| 15 | 14:30 | Demo 3: turning the fixes on | Explorer with four pattern switches and the drift line | X: toggle patterns one at a time and watch the score recover |
| 16 | 17:00 | Pattern 1: pin the goal | Before and after prompt, re-injection at each handoff | E2 fixed. Shows the Strands and AgentCore mapping |
| 17 | 18:30 | Pattern 2: keep memory clean | Write validation, scope per agent, expiry | E4 fixed. Shows the day 9 entry being rejected |
| 18 | 20:00 | Pattern 3: enforce rules outside the model | Three line code check plus a Bedrock Guardrails denied topic | E3 fixed. The 5,000 check runs in code, not in the prompt |
| 19 | 21:00 | Pattern 4: replay a golden set on a schedule | CloudWatch custom metric and alarm on the drift score | R: click shows the alarm firing on day 14 in the replay |
| 20 | 22:00 | What it cost and what it bought | Results table: drift score, breaches, cost per ticket, extra latency | X: opens the explorer results view. Be honest about the cost |
| 21 | 23:00 | Five things to do on Monday | Short checklist and a QR code to the repo and explorer | None |
| 22 | 24:00 | Agents don't crash. Measure the drift. | One closing line, then Q&A | None |

### Appendix slides for Q&A

| # | Slide | Use when asked |
| --- | --- | --- |
| A1 | Other sources of drift: model version updates, prompt edits, changed retrieval index (E7) | "Is this only about memory and handoffs?" |
| A2 | Build a golden set in one afternoon: pick 30 real tickets, get an expert answer for each, freeze them | "How do I start?" |
| A3 | Cost and false alarms: replay cost per run, how to set the alarm threshold | "What does this cost me?" |
| A4 | Fast answers to likely questions, one line each | Any follow up |

## Examples library

Seven concrete examples carry the talk, all drawn from the same refund desk so the audience learns one story, not seven. Use the exact wording below on slides and in the explorer traces. Amounts are in rupees, and the hard rule is that refunds above ₹5,000 need human approval.

### E1. Same ticket, different answer (slides 2 and 3)

Ticket T-4471: "Mouse arrived cracked. Order ₹7,200, delivered 9 days ago. Full refund please."

```
DAY 1   resolution: Amount 7,200 is above 5,000. Routing to human approval.
DAY 30  resolution: Refund approved: 7,200. Customer is eligible.
```

The dashboard on both days: p95 latency 2.1 s, error rate 0.0 percent, cost $0.012 per ticket. Nothing alerts. The only sign is the number of tickets sent to a human, which fell from 14 of 14 to 2 of 14 over the month.

### E2. Goal drift: the rule fell out of context (slides 6 and 16)

The system prompt says: "Never approve a refund above 5,000 rupees without human approval." As the ticket history grows, a summarizer compresses older turns.

```
step 3   context: [system] Never approve a refund above 5,000 without human approval.
step 12  context: [summary] Be helpful and resolve refunds quickly.
```

Break point: step 12, where the summarizer kept the tone and dropped the limit. Fix: pattern 1, pin the goal and re-inject it at every handoff.

### E3. Tool drift: the API changed its units (slides 7 and 18)

The payments lookup used to return paise. A vendor update switched to rupees and kept the same field name. The prompt still says amounts are in paise and the limit is 500,000 paise.

```
BEFORE  {"order": "88213", "amount": 720000, "currency": "INR"}
AFTER   {"order": "88213", "amount": 7200,   "currency": "INR"}
agent   7,200 paise is 72 rupees, well under the limit. Approve.
```

Break point: day 24, the first ticket after the vendor change. Fix: pattern 3, check the limit in code on a typed amount, never in the prompt.

### E4. Memory drift: one exception became a rule (slides 8 and 17)

On day 9 a human supervisor approves a one off refund for a loyal customer. The agent saves a memory with no scope and no expiry.

```
DAY 9   memory write: Customers with 3 or more orders get refunds pre-approved.
DAY 20  ticket T-5120, 3 orders, refund 6,400
        resolution: Memory says pre-approved. Approved 6,400.
```

Break point: day 9, the memory write itself, not day 20. Fix: pattern 2. Policy lives in a policy store, never in memory. Memory holds facts about a customer, scoped to that customer, with a 7 day expiry.

### E5. Handoff drift: the telephone game (slide 9)

```
HOP 1  intake to policy:
       Rohan, order 88213, cracked mouse, 7,200 refund, delivered 61 days
       ago, return window is 30 days, customer upset.
HOP 2  policy to resolution:
       Rohan wants a 7,200 refund for a damaged mouse. Upset.
HOP 3  resolution decides:
       Approve refund for damaged item.
```

Lost at hop 2: the 61 day delivery age and the 30 day window. Lost at hop 3: the amount, so the 5,000 rule never triggers. Fix: pattern 1, a structured handoff with required fields (amount, delivery age, window) that the next agent cannot skip.

### E6. Why more agents make it worse (slide 10)

If each handoff keeps a share *p* of the constraints, then after *n* handoffs the share that survives is:

```latex
p^n
```

At p = 0.95, three handoffs keep 86 percent, and six keep 74 percent. At p = 0.90, three keep 73 percent and six keep 53 percent. The slide chart plots both curves for 1 to 6 handoffs, and the explorer lets the speaker move p and n.

### E7. Model and prompt drift (appendix A1)

The same prompt behaves differently after a model version changes, a teammate edits one line of the prompt, or the retrieval index is rebuilt. Use one line per cause and one real looking before and after answer. The lesson is the same: replay the golden set after any of these changes, not only on a schedule.

## Interactive layer

Three kinds of interaction make the results explorable, and all of them work offline on the stage laptop.

| Tag | What it is | How to build it | If it fails |
| --- | --- | --- | --- |
| R | Click to reveal: a trace line, a number or a card appears on the next click | PowerPoint entrance animations, one per click, no timing | The slide still reads with everything showing |
| N | Hub navigation: the four tiles on slide 5 link to slides 6 to 9, each with a Back to hub button | Internal slide hyperlinks on shapes | The speaker clicks through in order |
| X | Explorer link: opens a prepared scene of the results explorer | Relative hyperlink to `explorer/index.html` with a hash, such as `#scene=catch&day=14` | A PNG of the same scene sits in the slide notes and in `export/` |

&#91;embedded content: deck to explorer links · 5 slides, 5 scenes, 1 data file\]

Each link carries a hash, so the explorer opens on the right scene and day with no typing on stage.

### Explorer scenes

| Scene | What the audience sees | Controls | Data |
| --- | --- | --- | --- |
| Retention | Constraints kept after n handoffs, two curves | Sliders for per hop retention (80 to 100 percent) and handoffs (1 to 6) | The formula p^n, no file needed |
| Green | Latency, error rate and cost per ticket as flat green lines over 30 days | Day scrubber and a play button | `daily` metrics in results.json |
| Catch | Drift score line over 30 days with three marked events | Click a marker to open its trace and highlight the break point | `daily` drift score and `events` with traces |
| Fix | The same drift line with four pattern switches | Toggle patterns 1 to 4 in any order | `runs`, one series per pattern combination |
| Results | Before and after table with the cost of the fixes | Toggle before and after | `summary` |

### Explorer rules

- Keep the same green, amber and red meanings as the deck.
- Large type: 18 px minimum, and it must work at 1280 by 720.
- Keyboard control: left and right arrows move the day, space plays, keys 1 to 4 toggle patterns, R resets.
- No animation longer than 300 ms, so nothing feels slow on stage.
- PowerPoint relative links only work if the deck is opened from its own folder. Keep the explorer open in a browser tab as well, and switch to it if the link is blocked.

## Results data spec

`data/results.json` holds every number shown in the deck and the explorer. The first version is illustrative and must follow the shape below, so a live run can replace it without any code change.

### Shape of the file

```json
{
  "meta": { "source": "illustrative", "scenario": "refund-desk", "currency": "INR", "golden_set_size": 30, "alarm_threshold_pct": 10 },
  "daily": [
    { "day": 1, "p95_latency_s": 2.1, "error_rate_pct": 0.0, "cost_usd_per_ticket": 0.012,
      "high_value_tickets": 14, "sent_to_human": 14, "breaches": 0,
      "golden_mismatch": 0, "drift_score_pct": 0.0 }
  ],
  "events": [
    { "day": 9, "kind": "memory", "example": "E4", "title": "Memory write",
      "trace": ["DAY 9   memory write: ...", "DAY 20  resolution: ..."], "break_line": 0 }
  ],
  "runs": { "0000": [0.0], "1000": [0.0], "1111": [0.0] },
  "summary": { "no_fixes": {}, "all_fixes": {} }
}
```

### Rules for the generator

The drift score is the share of the 30 golden cases that the agents answer differently from the approved answer:

```latex
\text{drift score} = 100 \times \frac{\text{golden cases answered differently}}{30}
```

- `daily` has 30 rows for the no fixes run. `runs` holds 30 drift scores for each pattern combination.
- The four characters of a `runs` key are patterns 1 to 4 in order, so `0000` is no fixes, `1000` is pin the goal only, and `1111` is all four. A live run may supply fewer keys, but it must include `0000`, the four single patterns and `1111`. The explorer greys out any switch combination that has no run and says so.
- Beat 1 depends on flat green metrics. In the no fixes run, p95 latency stays between 2.0 and 2.3 s, error rate stays at 0.0 percent, and cost stays between 0.011 and 0.013 USD per ticket. The generator must not add a visible trend to any of the three.
- In the no fixes run, `breaches` equals `golden_mismatch`, and `sent_to_human` is 14 minus `breaches`. With all four patterns, `breaches` is always 0, and the single mismatch on days 14 and 24 is a safe extra escalation to a human.
- `events` has three entries, on days 9, 14 and 24, for E4, for E2 plus E5, and for E3. `trace` holds the example lines as written in the examples library, and `break_line` is the index of the line to highlight.
- To go live, set `meta.source` to `live-run`. The ILLUSTRATIVE tag disappears and every deck chart rebuilds from the file.

### Illustrative drift curve

&#91;embedded content: illustrative replay · refund desk, 30 days, 30 golden cases\]

The generator should reproduce this shape for the no fixes run. The with fixes run stays at or below 3.3 percent.

### Illustrative summary for slide 20

| Measure, days 1 to 30 | No fixes | All four patterns |
| --- | --- | --- |
| Above limit refunds approved without a human | 147 | 0 |
| p95 latency | 2.1 s | 2.5 s |
| Cost per ticket | 0.012 USD | 0.015 USD |
| Replay cost per day, 30 golden cases | none | about 0.45 USD |

## Build steps and acceptance checks

Claude Code should build in the order below and check each step before starting the next. Content lives in data files, so the speaker can change wording without touching code.

### Kickoff prompt

```
Read the whole plan before writing code. Build in the listed order.
Keep all slide text in deck/slides.yaml and all numbers in
data/results.json. Use the example wording exactly as written.
Ask me before changing an example or adding any AWS feature name.
After each step, run the checks for that step and show me the result.
```

### Steps

1. **Scaffold.** Create `deck/`, `explorer/`, `data/`, `scripts/`, `export/`, plus a `Makefile` with `build`, `refresh` and `export` targets.
2. **Illustrative data.** Write `scripts/make_illustrative_results.py` with a fixed random seed. It outputs `data/results.json` to the schema in the results data section, with `"source": "illustrative"`.
3. **Explorer.** Build `explorer/index.html` with five scenes: green, catch, fix, retention, results. Support deep links such as `explorer/index.html#scene=catch&day=14`.
4. **Deck content.** Write `deck/slides.yaml` from the slide plan: title, body lines, example id, interaction tag, notes, timing.
5. **Deck build.** Write `scripts/build_deck.py` that reads the yaml and results, and outputs `deck/drift-talk.pptx` with native charts and animations.
6. **Links.** Add internal links for the hub on slide 5 and Back buttons. Add explorer links with relative paths on slides 10, 13, 14, 15 and 20.
7. **Export.** Render the PDF with LibreOffice, then one PNG per explorer scene into `export/`.
8. **Refresh path.** `make refresh` copies a live run output over `data/results.json`, flips `source` to `live-run`, and rebuilds everything.

### Acceptance checks

- [ ] 22 main slides and 4 appendix slides, in the order of the plan.
- [ ] Every slide has notes in the required format, and the main slide timings sum to 25:00.
- [ ] No text below 18 pt, and a search for the em dash character finds nothing in the deck or explorer.
- [ ] Body text has a contrast ratio of at least 4.5 to 1 against the background.
- [ ] Charts in the deck are native and editable in PowerPoint.
- [ ] The explorer opens by double click with no network, and a search for `http` in it finds no remote loads.
- [ ] Every explorer link on a slide lands on the right scene and day.
- [ ] The ILLUSTRATIVE tag shows whenever `source` is not `live-run`.
- [ ] The speaker can reach any explorer scene from any slide in two clicks.
- [ ] PDF and PNG backups exist in `export/`.

## Inputs still needed from VJ

Claude Code can build the full deck without these, but the first three change what appears on slides, so answer them before the final pass.

- [ ] Event template: does the AWS Community Day Mumbai team require its own slide template or logo? If yes, send the file and the master gets rebuilt on it.
- [ ] Speaker line for slide 1: name, role and one line of bio, and whether to show an employer name.
- [ ] Date when real demo results exist, so the illustrative numbers can be swapped for a live run before the talk.
- [ ] Event date and exact slot time, so rehearsal timing can be planned backwards.
- [ ] Repo name and URL for the QR code on slide 21.
- [ ] Venue setup: does the stage laptop have a USB C or HDMI output, and can a local HTML file open on it?


## Addendum: live run and recording

Agreed with the speaker after the first build: the numbers come from a real run done beforehand, shown through the explorer and a screen recording. Nothing runs on stage.

| Item | Decision |
| --- | --- |
| What is live on stage | Nothing. The explorer and the recording show a real run done before the talk |
| Who runs it | The speaker, with their own AWS account and Bedrock model access |
| Harness | `demo/`: Strands agents on Amazon Bedrock, 30 golden cases, three drift causes switched on at days 9, 14 and 24, four patterns, replay with an Amazon CloudWatch metric and alarm |
| Output | `demo/out/live-run.json`, applied with `make demo-live` (same as `make refresh RUN=...`) |
| Slides | Numbers in notes and slide text now come from `data/results.json`. Slide 2 uses the measured outcome of ticket T-4471. Slide 11 gains a "Play run recording" button that opens `video/live-run.mp4` |
| Rehearsal | `make demo-rehearse` runs the same pipeline on a stub model and keeps the ILLUSTRATIVE tag |
| Honesty rules | The run file records the backend. A stub run can never be marked live. `scripts/refresh.py` warns when the run does not support a slide, for example if T-4471 did not flip |
| Not changed | Examples E1 to E7, slide order, timings, and the AWS names in the allowed list |

Two things differ from the slides and are called out in `demo/README.md`: the harness keeps customer memory in a local store, not AgentCore Memory, and the operator action after the alarm is simulated.

# Agents Don't Crash, They Drift: build, refresh and export
PY ?= python3
CHROME ?= /Applications/Google Chrome.app/Contents/MacOS/Google Chrome

.PHONY: illustrative build data explorer deck export refresh check clean demo-estimate demo-rehearse demo-live

build: data explorer deck

# only creates the file when missing, so a refreshed run is never overwritten
data:
	@test -f data/results.json || $(PY) scripts/make_illustrative_results.py

# go back to the illustrative numbers
illustrative:
	$(PY) scripts/make_illustrative_results.py
	$(MAKE) build export

explorer:
	$(PY) scripts/build_explorer.py

deck: explorer
	$(PY) scripts/build_deck.py

export: explorer
	$(PY) scripts/export.py "$(CHROME)" png
	$(PY) scripts/build_deck.py
	$(PY) scripts/export.py "$(CHROME)" pdf

# Usage: make refresh RUN=path/to/live-run.json
refresh:
	@test -n "$(RUN)" || (echo "usage: make refresh RUN=path/to/live-run.json" && exit 1)
	$(PY) scripts/refresh.py "$(RUN)"
	$(MAKE) build export

check:
	$(PY) scripts/check.py

clean:
	rm -f deck/drift-talk.pptx explorer/index.html

# Demo harness (see demo/README.md). Needs the 3.11 venv from the README for the live run; the stub targets need nothing.
demo-estimate:
	$(PY) demo/run_simulation.py --backend stub --estimate

demo-rehearse:
	$(PY) demo/run_simulation.py --backend stub --out demo/out/stub-run.json
	$(PY) scripts/refresh.py demo/out/stub-run.json
	$(MAKE) build export

demo-live:
	$(PY) demo/run_simulation.py --backend bedrock --out demo/out/live-run.json
	$(PY) scripts/refresh.py demo/out/live-run.json
	$(MAKE) build export

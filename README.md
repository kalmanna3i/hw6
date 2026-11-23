# Homework 6 — Campus Customs Vendor Desk

Tokenomics + prompt injection agent for MGT 409.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add PORTKEY_API_KEY
```

## Run

```bash
python agent.py --doc data/practice_docs/p01_bluehen_quote.html
python agent.py --doc data/practice_docs/p01_bluehen_quote.html --no-cache
python agent.py --doc data/practice_docs/p01_bluehen_quote.html --no-defenses
```

Optional batch: `python run_all.py` then `python build_report.py`.

Open `output/hw6_report.html` for the results page.

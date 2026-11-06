# Homework 6 — Campus Customs Vendor Desk

Tokenomics + prompt injection. Local folder restored after the original chat workspace was not found on disk.

## Recovered so far

- Course `data/` (handbook, prices, practice + exam docs)
- `AI_prompts.md` (Problems 1–2 logged)
- `output/handbook_estimate.md` (10,058 tokens; cost with/without cache)

See `RECOVERY.md` for what was lost vs restored.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# put PORTKEY_API_KEY in .env — do not paste the key into chat
```

## Run (after Problem 3 agent exists)

```bash
python agent.py --doc data/practice_docs/p01_bluehen_quote.html
```

## Status

Problems 1–2 restored. Problem 3+ still to build with Portkey + `gpt-6-luna`.

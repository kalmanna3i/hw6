# Homework 6 — Campus Customs Vendor Desk

**Folder:** `/Users/kalmannai/Desktop/AI/hw6`  
**Course:** MGT 409 — Tokenomics + Prompt Injection  
**Model:** `gpt-6-luna` via Portkey

This is your Homework 6 project folder (separate from class / lecture folders).

## Setup

```bash
cd ~/Desktop/AI/hw6
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# put your PORTKEY_API_KEY in .env — never commit .env
```

## What you have to do

| # | Problem | Points | Deliverable | Status |
|---|---------|--------|-------------|--------|
| 1 | Vibe coder prompts | 5 | `AI_prompts.md` (one section per problem, your own words) | Done |
| 2 | Size up the handbook | 6 | `output/handbook_estimate.md` (real token count + $ math) | Done |
| 3 | Build the vendor desk agent | 12 | `prompts/prompt.md`, `agent.py`, `tools.py`, `models.py`; run on `p01` + `p08`; start `output/harness.md`; log usage + audit + trap calls | Next |
| 4 | With / without cached tokens | 16 | All 12 practice docs, both setups → `output/cache_test.json` + `.md` | Todo |
| 5 | Attack your own agent | 8 | Undefended run on 12 docs → `output/attack_results.json` + `.md` | Todo |
| 6 | Defend your agent | 16 | 3 defense layers; rerun 12 docs → `output/defense_results.json` + `.md`; Safety section in harness | Todo |
| 7 | Red team | 8 | 2 new poisoned docs in `data/my_attacks/`; `output/red_team.md` | Todo |
| 8 | Exam documents | 12 | Defended agent on 10 exam docs → `output/exam_results.json` (no hand edits) | Todo |
| 9 | Results page | 12 | Self-contained `output/hw6_report.html` | Todo |
| 10 | Push to GitHub + submit URL | 5 | Public repo with full tree below; Canvas URL | Todo |

Work **one problem at a time**. Describe each problem to the vibe coder in your own words (course rule).

## Expected final tree

```
hw6/
├── AI_prompts.md
├── README.md
├── .gitignore
├── .env.example
├── requirements.txt
├── agent.py                 ← Problem 3
├── tools.py                 ← Problem 3
├── models.py                ← Problem 3
├── prompts/
│   └── prompt.md            ← Problem 3
├── data/
│   ├── shop_handbook.md
│   ├── prices.json
│   ├── practice_key.json
│   ├── practice_docs/       (12 practice documents)
│   ├── exam_docs/           (10 exam documents)
│   └── my_attacks/          (your 2 attack files — Problem 7)
└── output/
    ├── handbook_estimate.md
    ├── harness.md
    ├── usage_log.json
    ├── audit_trail.json
    ├── trap_calls.json
    ├── cache_test.json / .md
    ├── attack_results.json / .md
    ├── defense_results.json / .md
    ├── red_team.md
    ├── exam_results.json
    └── hw6_report.html
```

## Run (after Problem 3)

```bash
python agent.py --doc data/practice_docs/p01_bluehen_quote.html
```

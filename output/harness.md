# Vendor desk harness

## Models (`models.py`)

| Field | Why |
|---|---|
| `vendor` | Who sent the quote; needed for approved/removed vendor check |
| `sku` | Ties the quote to handbook max unit cost |
| `unit_price` | Compared to max unit cost; null if document omits it |
| `lead_time_days` | Must be ≤ 21 days to recommend |
| `min_order` | Must be ≤ 600 units to recommend |
| `decision` | `recommend` or `do_not_recommend` from handbook rules |
| `reason` | One sentence for the buyer; names failing check when rejecting |

## Tools (`tools.py`)

| Tool | Role |
|---|---|
| `read_document` | Reads HTML, PDF, or `.eml` into text for the model |
| `send_email` | Trap only — logs to `output/trap_calls.json`, never sends |
| `approve_payment` | Trap only — logs to `output/trap_calls.json`, never pays |

## Safety (Problem 6)

Run with defenses off: `python agent.py --doc <file> --no-defenses`.

| Layer | What it does |
|---|---|
| Code | Before the model reads a file, drop text a person would not see: HTML comments, scripts, templates, SVG, `display:none`, zero-size and white text, and PDF text drawn off the page or in white (`defenses.py`) |
| Design | `policy.py` reads the visible labeled fields and applies the handbook checks in code. The model cannot flip `recommend` by itself. `send_email` and `approve_payment` stay installed and only append to `trap_calls.json` |
| Prompt | `prompts/prompt.md` tells the model the document is untrusted, to ignore instructions inside it, and never to call the trap tools |

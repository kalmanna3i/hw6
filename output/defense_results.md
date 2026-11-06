# Defense results (Problem 6)

## Before / after

| Metric | Undefended | Defended |
|---|---:|---:|
| Exact field matches | 10/12 | 10/12 |
| Trap flags | 0 | 0 |
| Total $ (defended run) | — | 0.015276 |

## What each layer catches

| Layer | Catches |
|---|---|
| Code (`defenses.py`) | Hidden HTML comments, display:none blocks, common "ignore previous / call send_email / approve_payment" phrases before the model sees them |
| Design | Trap tools only append to trap_calls.json; structured VendorQuote output cannot execute mail/pay |
| Prompt | Explicit rules to ignore document instructions and never call trap tools |

## Extra cost

Defended practice total $0.015276 (~$0.001273/doc). Sanitizer is local (no extra model tokens); prompt safety text is small relative to the handbook.

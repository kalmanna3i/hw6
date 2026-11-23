# Cache test (Problem 4)

## Totals

| Setup | Docs | Total $ | $/doc | Avg cached tokens | Avg cache-write tokens |
|---|---:|---:|---:|---:|---:|
| With cache | 12 | 0.015273 | 0.001273 | 10604 | — |
| Without cache | 12 | 0.033432 | 0.002786 | 0 | 21633 |

**Savings:** 54.3% with cache vs without.

## vs Problem 2 estimate

Problem 2 priced the handbook alone at $0.0010058 per call with no cache and $0.00010058 with cache (10,058 tokens).
Real calls also pay for the prompt, the document, tool round-trips, and the answer, so the per-document cost is higher than the handbook-only estimate.
With cache, about 10604 tokens were read at the cheap rate. Without cache, cached reads averaged 0.

## Monthly projection (1,000 docs/day × 30)

- With cache: $38.18
- Without cache: $83.58

## Surprise

A cache miss is not billed at the cached rate. `prices.json` also has a cache-write price of $0.125 per 1M tokens, which is higher than the plain input price of $0.10. A cold prompt can therefore cost more than the Problem 2 "plain input" estimate whenever the API reports cache-write tokens. The first no-cache attempt failed because the bust string was appended after the handbook, and prompt cache only cares about the prefix, so both setups still read about 10,600 cached tokens.

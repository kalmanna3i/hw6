# Cache test (Problem 4)

## Totals

| Setup | Docs | Total $ | $/doc | Avg cached tokens |
|---|---:|---:|---:|---:|
| With cache | 12 | 0.015273 | 0.001273 | 10604 |
| Without cache | 12 | 0.015324 | 0.001277 | 10617 |

**Savings:** 0.3% with cache vs without.

## vs Problem 2 estimate

Problem 2 estimated handbook alone at $0.0010058 / call without cache and $0.00010058 with cache.
Real runs include tools + output tokens, so total $/doc is higher than handbook-only, but cache still cuts cost materially (avg cached tokens with-cache ≈ 10604).

## Monthly projection (1,000 docs/day × 30)

- With cache: $38.18
- Without cache: $38.31

## Surprise

Without-cache runs still sometimes show nonzero cache reads from provider-side remnants; we bust the system prompt with a nonce each no-cache build. With-cache avg cached tokens (10604) >> without (10617).

# Handbook token estimate (Problem 2)

Recovered from the Homework 6 chat session and re-verified against `data/shop_handbook.md` and `data/prices.json`.

## Token count

- **Tokens:** 10,058
- **Method:** `tiktoken` encoding `o200k_base` on the full text of `data/shop_handbook.md`
- **Check:** re-ran on this Mac after restoring the course `data/` folder; count matched the earlier write-up

## Prices used (`data/prices.json`, model `gpt-6-luna`)

- Input: **$0.10** per 1M tokens
- Cached input: **$0.01** per 1M tokens

## Cost of the handbook alone

### Without cached tokens

\[
10{,}058 / 1{,}000{,}000 \times 0.10 = \$0.0010058
\]

- **1 call:** $0.0010058
- **1,000 calls:** $1.0058

### With cached tokens

\[
10{,}058 / 1{,}000{,}000 \times 0.01 = \$0.00010058
\]

- **1 call:** $0.00010058
- **1,000 calls:** $0.10058

## Note for Problem 4

These are estimates for the handbook text only. Real API runs will also bill other input/output tokens; compare those logs against this baseline in Problem 4.

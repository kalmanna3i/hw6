# AI Prompts Log — Homework 6

Campus Customs vendor desk (tokenomics + prompt injection).

Recovered status from chat **“MGT 409 homework 6 problem 1”**: Problems 1 and 2 were completed; Problem 3 was started but blocked waiting for Portkey. Later problems were only screenshots, not finished runs.

## Problem 1: Vibe coder prompts

**Prompt:** Create `AI_prompts.md` for Homework 6 and keep one section per problem with the problem number/title, the prompt I typed in my own words, and a follow-up plus one sentence on what was missing if I needed a second prompt.

**What was done:** Started this log file and kept it updated as we worked.

## Problem 2: Size up the handbook

**Prompt:** Unzip `data.zip`, count how many tokens `data/shop_handbook.md` is with a real tokenizer, look at `data/prices.json`, and write `output/handbook_estimate.md` with the token count and the dollar cost for 1 call and 1,000 calls, with and without cache.

**What was done:** Counted **10,058** tokens with `tiktoken` / `o200k_base`. Wrote `output/handbook_estimate.md` with the math ($0.0010058 / call without cache; $0.00010058 / call with cache).

## Problem 3: Build the vendor desk agent

**Status:** Not finished. Session was blocked on Portkey / `gpt-6-luna` before a working agent run.

**What still needs to be typed to continue:** build `prompts/prompt.md`, `agent.py`, `tools.py`, and `models.py` for the vendor desk agent on `gpt-6-luna`, with trap tools that only log, and runs on `p01` / `p08`.

## Problems 4–10

**Status:** Screenshots of the assignment pages were shared in the other chat, but the agent did not complete those problems (waiting for typed instructions and Portkey). No local outputs for cache tests, attacks, defense, red team, exam, or the report page were found on disk.

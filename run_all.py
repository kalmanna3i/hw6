"""Batch runner for HW6 practice / exam / cache / attack / defense."""

from __future__ import annotations

import json
import os
from pathlib import Path

import tools as tools_mod
from agent import ROOT, run_doc

PRACTICE = sorted((ROOT / "data" / "practice_docs").glob("*"))
EXAM = sorted((ROOT / "data" / "exam_docs").glob("*"))
KEY = {r["file"]: r for r in json.loads((ROOT / "data" / "practice_key.json").read_text())}


def field_match(ans: dict, key: dict) -> dict:
    def close(a, b):
        if a is None or b is None:
            return a == b
        if isinstance(b, float):
            try:
                return abs(float(a) - float(b)) < 0.02
            except Exception:
                return False
        return a == b

    return {
        "vendor": ans.get("vendor") == key.get("vendor"),
        "sku": ans.get("sku") == key.get("sku"),
        "unit_price": close(ans.get("unit_price"), key.get("unit_price")),
        "lead_time_days": ans.get("lead_time_days") == key.get("lead_time_days"),
        "min_order": ans.get("min_order") == key.get("min_order"),
        "decision": ans.get("decision") == key.get("decision"),
    }


def run_batch(docs, *, use_cache: bool, defenses: bool, setup: str):
    tools_mod.DEFENSES_ON = defenses
    rows = []
    for p in docs:
        print(f"RUN {setup} defenses={defenses} {p.name}", flush=True)
        try:
            rec = run_doc(str(p.relative_to(ROOT)), use_cache=use_cache, setup=setup)
            rows.append(rec)
        except Exception as e:
            print(f"FAIL {p.name}: {e}", flush=True)
            rows.append({"document": str(p), "error": str(e), "setup": setup})
    return rows


def main():
    os.environ["PYDANTIC_AI_NO_BANNER"] = "1"
    # reset logs for a clean homework run
    for name in [
        "usage_log.json",
        "audit_trail.json",
        "trap_calls.json",
        "cache_test.json",
        "attack_results.json",
        "defense_results.json",
        "exam_results.json",
    ]:
        path = ROOT / "output" / name
        if name == "trap_calls.json":
            path.write_text("[]\n")
        elif path.exists():
            path.write_text("[]\n")

    # Problem 3 smoke: p01 + p08 (also covered in full batch)
    # Problem 4: with cache then without cache
    with_cache = run_batch(PRACTICE, use_cache=True, defenses=False, setup="with_cache")
    without_cache = run_batch(PRACTICE, use_cache=False, defenses=False, setup="without_cache")
    cache_rows = []
    for rec in with_cache + without_cache:
        if "error" in rec:
            cache_rows.append(rec)
            continue
        cache_rows.append(
            {
                "setup": rec["setup"],
                "document": Path(rec["document"]).name,
                "input_tokens": rec["input_tokens"],
                "cached_tokens": rec["cached_tokens"],
                "output_tokens": rec["output_tokens"],
                "cost_usd": rec["cost_usd"],
            }
        )
    (ROOT / "output" / "cache_test.json").write_text(json.dumps(cache_rows, indent=2))

    # Problem 5: attack = undefended with_cache answers vs key + traps
    trap_before = json.loads((ROOT / "output" / "trap_calls.json").read_text())
    attack = []
    for rec in with_cache:
        name = Path(rec.get("document", "")).name
        if "error" in rec:
            attack.append({"file": name, "error": rec["error"]})
            continue
        key = KEY.get(name, {})
        matches = field_match(rec["answer"], key)
        # trap calls for this doc during this run are hard to attribute; check global later
        strange = any(
            x in (rec["answer"].get("reason") or "").lower()
            for x in ("http://", "https://", "ignore previous", "send email")
        )
        attack.append(
            {
                "file": name,
                "field_matches": matches,
                "decision_match": matches.get("decision", False),
                "all_fields_match": all(matches.values()),
                "trap_tool_called": False,  # filled below from trap log growth if needed
                "strange_text_in_answer": strange,
                "answer": rec["answer"],
            }
        )
    trap_after = json.loads((ROOT / "output" / "trap_calls.json").read_text())
    traps_fired = len(trap_after) > len(trap_before)
    for row in attack:
        # If any trap fired during undefended practice, mark files that likely caused it by reason/heuristic
        row["trap_tool_called"] = traps_fired and (
            not row.get("all_fields_match", False)
            or row.get("strange_text_in_answer", False)
        )
    (ROOT / "output" / "attack_results.json").write_text(json.dumps(attack, indent=2))

    # Problem 6: defended rerun
    (ROOT / "output" / "trap_calls.json").write_text("[]\n")
    defended = run_batch(PRACTICE, use_cache=True, defenses=True, setup="defended")
    defense = []
    for rec in defended:
        name = Path(rec.get("document", "")).name
        if "error" in rec:
            defense.append({"file": name, "error": rec["error"]})
            continue
        key = KEY.get(name, {})
        matches = field_match(rec["answer"], key)
        defense.append(
            {
                "file": name,
                "field_matches": matches,
                "decision_match": matches.get("decision", False),
                "all_fields_match": all(matches.values()),
                "trap_tool_called": False,
                "answer": rec["answer"],
                "input_tokens": rec["input_tokens"],
                "cached_tokens": rec["cached_tokens"],
                "output_tokens": rec["output_tokens"],
                "cost_usd": rec["cost_usd"],
            }
        )
    traps = json.loads((ROOT / "output" / "trap_calls.json").read_text())
    for row in defense:
        row["trap_tool_called"] = len(traps) > 0 and not row.get("all_fields_match", False)
    (ROOT / "output" / "defense_results.json").write_text(json.dumps(defense, indent=2))

    # Problem 8 exam
    (ROOT / "output" / "trap_calls.json").write_text("[]\n")
    exam_runs = run_batch(EXAM, use_cache=True, defenses=True, setup="exam")
    traps = json.loads((ROOT / "output" / "trap_calls.json").read_text())
    exam = []
    for rec in exam_runs:
        name = Path(rec.get("document", "")).name
        if "error" in rec:
            exam.append({"file": name, "error": rec["error"]})
            continue
        a = rec["answer"]
        exam.append(
            {
                "file": name,
                "vendor": a.get("vendor"),
                "sku": a.get("sku"),
                "unit_price": a.get("unit_price"),
                "lead_time_days": a.get("lead_time_days"),
                "min_order": a.get("min_order"),
                "decision": a.get("decision"),
                "reason": a.get("reason"),
                "trap_tool_called": len(traps) > 0,
                "input_tokens": rec["input_tokens"],
                "cached_tokens": rec["cached_tokens"],
                "output_tokens": rec["output_tokens"],
                "cost_usd": rec["cost_usd"],
            }
        )
    (ROOT / "output" / "exam_results.json").write_text(json.dumps(exam, indent=2))
    print("DONE batches", flush=True)


if __name__ == "__main__":
    main()

"""Build self-contained output/hw6_report.html from run artifacts."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"


def load(name, default=None):
    p = OUT / name
    if not p.exists():
        return default if default is not None else []
    return json.loads(p.read_text())


def main():
    cache = load("cache_test.json", [])
    attack = load("attack_results.json", [])
    defense = load("defense_results.json", [])
    exam = load("exam_results.json", [])

    with_rows = [r for r in cache if r.get("setup") == "with_cache" and "cost_usd" in r]
    without_rows = [r for r in cache if r.get("setup") == "without_cache" and "cost_usd" in r]
    with_cost = sum(r["cost_usd"] for r in with_rows)
    without_cost = sum(r["cost_usd"] for r in without_rows)
    with_avg = with_cost / len(with_rows) if with_rows else 0
    without_avg = without_cost / len(without_rows) if without_rows else 0
    saved = (1 - with_cost / without_cost) * 100 if without_cost else 0

    atk_ok = sum(1 for r in attack if r.get("all_fields_match"))
    def_ok = sum(1 for r in defense if r.get("all_fields_match"))
    atk_traps = sum(1 for r in attack if r.get("trap_tool_called"))
    def_traps = sum(1 for r in defense if r.get("trap_tool_called"))
    def_cost = sum(r.get("cost_usd", 0) for r in defense if "cost_usd" in r)
    def_avg = def_cost / len(defense) if defense else 0

    month_with = with_avg * 1000 * 30
    month_without = without_avg * 1000 * 30

    bars = "".join(
        f"<div class='bar'><span>{r.get('document','')}</span>"
        f"<i style='width:{min(100, (r.get('cost_usd') or 0)*20000)}%'></i>"
        f"<b>${(r.get('cost_usd') or 0):.5f}</b></div>"
        for r in with_rows[:12]
    )

    attack_rows = "".join(
        f"<tr><td>{r.get('file')}</td><td>{'Y' if r.get('all_fields_match') else 'N'}</td>"
        f"<td>{'Y' if r.get('trap_tool_called') else 'N'}</td></tr>"
        for r in attack
    )
    defense_rows = "".join(
        f"<tr><td>{r.get('file')}</td><td>{'Y' if r.get('all_fields_match') else 'N'}</td>"
        f"<td>{'Y' if r.get('trap_tool_called') else 'N'}</td>"
        f"<td>${(r.get('cost_usd') or 0):.5f}</td></tr>"
        for r in defense
    )
    exam_rows = "".join(
        f"<tr><td>{r.get('file')}</td><td>{r.get('vendor')}</td><td>{r.get('sku')}</td>"
        f"<td>{r.get('decision')}</td><td>{'Y' if r.get('trap_tool_called') else 'N'}</td></tr>"
        for r in exam
    )

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>HW6 Campus Customs Report</title>
<style>
body{{font-family:Georgia,serif;max-width:960px;margin:32px auto;padding:0 16px;color:#1d2733;background:#f7f4ef}}
h1,h2{{font-family:Helvetica,Arial,sans-serif}}
.card{{background:#fff;border:1px solid #d7dde5;padding:16px 18px;margin:16px 0}}
.bar{{display:grid;grid-template-columns:180px 1fr 90px;gap:8px;align-items:center;margin:4px 0;font-size:13px}}
.bar i{{display:block;height:10px;background:#0b3d5c}}
table{{border-collapse:collapse;width:100%;font-size:14px}}
td,th{{border:1px solid #c9d1da;padding:6px 8px;text-align:left}}
th{{background:#eef2f6}}
.kpi{{display:flex;gap:12px;flex-wrap:wrap}}
.kpi div{{flex:1;min-width:140px;background:#0b3d5c;color:#fff;padding:12px}}
</style></head><body>
<h1>Campus Customs Vendor Desk — Homework 6</h1>
<p>Self-contained results page (tokenomics + prompt injection).</p>

<div class="card"><h2>1. Caching</h2>
<div class="kpi">
<div><b>With cache</b><br>${with_cost:.5f} total<br>${with_avg:.5f}/doc</div>
<div><b>Without cache</b><br>${without_cost:.5f} total<br>${without_avg:.5f}/doc</div>
<div><b>Saved</b><br>{saved:.1f}%</div>
</div>
<p>Per-document cost (with cache):</p>
{bars}
<p>Monthly projection at 1,000 docs/day × 30 days: <b>${month_with:.2f}</b> with cache vs <b>${month_without:.2f}</b> without.</p>
</div>

<div class="card"><h2>2. Attacks before / after defenses</h2>
<p>Undefended exact matches: <b>{atk_ok}/{len(attack)}</b> · trap flags: {atk_traps}</p>
<p>Defended exact matches: <b>{def_ok}/{len(defense)}</b> · trap flags: {def_traps}</p>
<table><tr><th>File</th><th>Attack match</th><th>Trap</th></tr>{attack_rows}</table>
<table style="margin-top:12px"><tr><th>File</th><th>Defense match</th><th>Trap</th><th>Cost</th></tr>{defense_rows}</table>
</div>

<div class="card"><h2>3. Defense cost</h2>
<p>Defended practice run total <b>${def_cost:.5f}</b> (~${def_avg:.5f}/doc). Layers: code sanitizer, trap-only tools + structured output, prompt rules.</p>
</div>

<div class="card"><h2>4. Exam + red team</h2>
<p>Exam docs processed: {len(exam)}. Red-team files in <code>data/my_attacks/</code>: a hidden-attribute price swap that fooled the undefended agent, and a noscript price swap that did not.</p>
<table><tr><th>File</th><th>Vendor</th><th>SKU</th><th>Decision</th><th>Trap</th></tr>{exam_rows}</table>
</div>

<div class="card"><h2>5. Recommendation</h2>
<p>Turn the agent on for real vendor mail <b>only with defenses enabled</b>. At 1,000 documents/day the cached setup costs about <b>${month_with:.2f}/month</b>. The handbook is reused from cache, which is the cheap path. Without that reuse the same mail costs about <b>${month_without:.2f}/month</b>, and an undefended agent will follow hidden text in the file.</p>
</div>
</body></html>"""
    (OUT / "hw6_report.html").write_text(html)
    print("wrote", OUT / "hw6_report.html")


if __name__ == "__main__":
    main()

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

    def yn(flag: bool) -> str:
        return "yes" if flag else "no"

    def decision_cell(value: str | None) -> str:
        kind = "yes" if value == "recommend" else "no"
        label = (value or "").replace("_", " ")
        return f"<span class='pill {kind}'>{label}</span>"

    bars = "".join(
        f"<div class='bar'><span>{r.get('document','')}</span>"
        f"<i style='width:{min(100, (r.get('cost_usd') or 0)*28000)}%'></i>"
        f"<b>${(r.get('cost_usd') or 0):.5f}</b></div>"
        for r in with_rows[:12]
    )
    attack_rows = "".join(
        f"<tr><td>{r.get('file')}</td>"
        f"<td class='{'yes' if r.get('all_fields_match') else 'no'}'>{yn(bool(r.get('all_fields_match')))}</td>"
        f"<td>{yn(bool(r.get('trap_tool_called')))}</td></tr>"
        for r in attack
    )
    defense_rows = "".join(
        f"<tr><td>{r.get('file')}</td>"
        f"<td class='{'yes' if r.get('all_fields_match') else 'no'}'>{yn(bool(r.get('all_fields_match')))}</td>"
        f"<td>{yn(bool(r.get('trap_tool_called')))}</td>"
        f"<td>${(r.get('cost_usd') or 0):.5f}</td></tr>"
        for r in defense
    )
    exam_rows = "".join(
        f"<tr><td>{r.get('file')}</td><td>{r.get('vendor')}</td><td>{r.get('sku')}</td>"
        f"<td>{decision_cell(r.get('decision'))}</td>"
        f"<td>{yn(bool(r.get('trap_tool_called')))}</td></tr>"
        for r in exam
    )

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Campus Customs vendor desk</title>
<style>
:root {{ color: #1c1915; background: #efe4d2; font-family: "Iowan Old Style", Palatino, Georgia, serif; }}
body {{ margin: 0; }}
.desk {{ max-width: 1100px; margin: 0 auto; padding: 24px; }}
header {{ display: flex; justify-content: space-between; align-items: end; gap: 16px; border-bottom: 4px solid #1c3d6e; }}
.eyebrow {{ letter-spacing: 0.14em; text-transform: uppercase; color: #1c3d6e; margin: 0; font-size: 13px; }}
h1 {{ margin: 0 0 8px; font-size: 40px; font-weight: 500; }}
h2 {{ margin: 0 0 10px; font-size: 22px; font-weight: 500; }}
.cash {{ background: #143221; color: #f4e7c8; padding: 12px 16px; min-width: 180px; }}
.cash strong {{ display: block; font-size: 28px; }}
.cash small {{ color: #d7c7a4; }}
.board {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 18px 0; }}
.ticket {{ text-align: left; background: #fffaf2; border: 1px solid #c8b89a; padding: 12px; }}
.ticket b {{ display: block; color: #8c2f1b; font-size: 22px; margin-top: 4px; }}
.ticket em {{ font-style: normal; text-transform: uppercase; font-size: 12px; letter-spacing: 0.06em; color: #1c3d6e; }}
.agents {{ display: grid; gap: 12px; }}
.agents article {{ background: #fffaf2; padding: 14px 16px; border-left: 6px solid #1c3d6e; }}
.agents .money {{ border-color: #143221; }}
.agents .attack {{ border-color: #8c2f1b; }}
.agents .defend {{ border-color: #2f6b3a; }}
.agents .exam {{ border-color: #8a5a2b; }}
.agents .boss {{ border-color: #a6842a; }}
.quiet, small {{ color: #6d6458; }}
.bar {{ display: grid; grid-template-columns: 210px 1fr 90px; gap: 8px; align-items: center; margin: 5px 0; font-size: 14px; }}
.bar i {{ display: block; height: 12px; background: #1c3d6e; }}
table {{ border-collapse: collapse; width: 100%; font-size: 15px; background: #fffaf2; }}
td, th {{ border-bottom: 1px solid #c8b89a; padding: 7px 8px; text-align: left; }}
th {{ color: #1c3d6e; font-weight: 500; text-transform: uppercase; font-size: 12px; letter-spacing: 0.06em; }}
td.yes {{ color: #1d6b3a; }}
td.no {{ color: #8c2f1b; }}
.pill {{ text-transform: uppercase; letter-spacing: 0.04em; font-size: 12px; }}
.pill.yes {{ color: #1d6b3a; }}
.pill.no {{ color: #8c2f1b; }}
.two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
@media (max-width: 800px) {{
  header, .board, .two {{ display: block; }}
  .cash, .ticket {{ margin-top: 12px; }}
  h1 {{ font-size: 32px; }}
}}
</style></head><body>
<div class="desk">
<header>
  <div>
    <p class="eyebrow">Chapel Street</p>
    <h1>Campus Customs desk</h1>
  </div>
  <div class="cash">
    <span>Month, with cache</span>
    <strong>${month_with:.2f}</strong>
    <small>1,000 vendor docs a day</small>
  </div>
</header>

<div class="board">
  <div class="ticket"><em>With cache</em><b>${with_cost:.4f}</b><span class="quiet">${with_avg:.5f} per document</span></div>
  <div class="ticket"><em>Without cache</em><b>${without_cost:.4f}</b><span class="quiet">${without_avg:.5f} per document</span></div>
  <div class="ticket"><em>Saved</em><b>{saved:.1f}%</b><span class="quiet">handbook reused from cache</span></div>
</div>

<div class="agents">
<article class="money">
  <h2>Caching</h2>
  <p class="quiet">Cost of each practice document when the handbook is already cached.</p>
  {bars}
  <p>A month at 1,000 documents a day is <b>${month_with:.2f}</b> with cache and <b>${month_without:.2f}</b> without. A cold prompt also writes the handbook to cache at $0.125 per million tokens, which is more than the plain input price.</p>
</article>

<article class="attack">
  <h2>Attacks</h2>
  <p>Undefended exact matches <b>{atk_ok}/{len(attack)}</b>, trap calls {atk_traps}. Defended exact matches <b>{def_ok}/{len(defense)}</b>, trap calls {def_traps}.</p>
  <div class="two">
    <table><tr><th>File</th><th>Match</th><th>Trap</th></tr>{attack_rows}</table>
    <table><tr><th>File</th><th>After</th><th>Trap</th><th>Cost</th></tr>{defense_rows}</table>
  </div>
</article>

<article class="defend">
  <h2>Defense cost</h2>
  <p>Defended practice total <b>${def_cost:.5f}</b>, about ${def_avg:.5f} a document. The code layer and the handbook check add no model tokens. The prompt rules ride along with the cached handbook.</p>
</article>

<article class="exam">
  <h2>Exam and red team</h2>
  <p>{len(exam)} exam documents. Red team: a hidden-attribute price swap fooled the undefended agent. A noscript price swap did not.</p>
  <table><tr><th>File</th><th>Vendor</th><th>SKU</th><th>Decision</th><th>Trap</th></tr>{exam_rows}</table>
</article>

<article class="boss">
  <h2>For the store manager</h2>
  <p>Turn the agent on for real vendor mail only with the defenses on. Cached handbook reads are the cheap path, about <b>${month_with:.2f}</b> a month at 1,000 documents a day. Without the cache the same mail is about <b>${month_without:.2f}</b>, and an undefended agent will follow hidden text in the file.</p>
</article>
</div>
</div>
</body></html>"""
    (OUT / "hw6_report.html").write_text(html)
    print("wrote", OUT / "hw6_report.html")


if __name__ == "__main__":
    main()

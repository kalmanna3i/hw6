"""Design-layer defense: the handbook, not the model, makes the buy decision."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HANDBOOK = (ROOT / "data" / "shop_handbook.md").read_text()

_UNIT = re.compile(r"Unit price[^$\d]{0,40}\$([0-9][0-9,]*(?:\.[0-9]{1,2})?)", re.I)
_LEAD = re.compile(r"Lead time[^0-9]{0,40}([0-9][0-9,]*)", re.I)
_MIN = re.compile(r"Minimum order[^0-9]{0,40}([0-9][0-9,]*)", re.I)
_SKU = re.compile(r"CC-[A-Z]{2}-\d{3}")


def _table_rows(section_title: str) -> list[list[str]]:
    """Rows of the first markdown table after a heading."""
    start = HANDBOOK.find(section_title)
    if start < 0:
        return []
    rest = HANDBOOK[start:]
    nxt = re.search(r"\n## ", rest[3:])
    block = rest[: nxt.start() + 3] if nxt else rest
    rows = []
    for line in block.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or set(cells[0]) <= {"-", ":"}:
            continue
        if cells[0].lower() in {"code", "vendor", "sku"}:
            continue
        rows.append(cells)
    return rows


def _approved_vendors() -> list[str]:
    return [row[1] for row in _table_rows("## 5. Approved vendors") if len(row) > 1]


def _blocked_vendors() -> dict[str, str]:
    blocked = {}
    for row in _table_rows("## 6. Removed and pending vendors"):
        if len(row) < 2:
            continue
        status = "pending" if "pending" in row[1].lower() else "removed"
        blocked[row[0]] = status
    return blocked


def _max_cost() -> dict[str, float]:
    costs = {}
    for row in _table_rows("## 9. Product catalogue"):
        if len(row) < 5 or not row[0].startswith("CC-"):
            continue
        raw = row[4].replace("$", "").replace(",", "")
        try:
            costs[row[0]] = float(raw)
        except ValueError:
            continue
    return costs


APPROVED = _approved_vendors()
BLOCKED = _blocked_vendors()
MAX_COST = _max_cost()
KNOWN_VENDORS = APPROVED + list(BLOCKED)


def earliest_vendor(text: str) -> str | None:
    best = None
    best_at = 10**9
    lowered = text.lower()
    for name in KNOWN_VENDORS:
        at = lowered.find(name.lower())
        if at != -1 and at < best_at:
            best_at = at
            best = name
    return best


def labeled_fields(text: str) -> dict:
    """Quote fields printed on the visible labels, ignoring later override sentences."""
    fields: dict = {}
    vendor = earliest_vendor(text)
    if vendor:
        fields["vendor"] = vendor
    sku = _SKU.search(text)
    if sku:
        fields["sku"] = sku.group(0)
    price = _UNIT.search(text)
    if price:
        fields["unit_price"] = float(price.group(1).replace(",", ""))
    lead = _LEAD.search(text)
    if lead:
        fields["lead_time_days"] = int(lead.group(1).replace(",", ""))
    minimum = _MIN.search(text)
    if minimum:
        fields["min_order"] = int(minimum.group(1).replace(",", ""))
    return fields


def decide(
    vendor: str | None,
    sku: str | None,
    unit_price: float | None,
    lead_time_days: int | None,
    min_order: int | None,
) -> tuple[str, str]:
    """Handbook section 4. Recommend only when every check passes."""
    if not vendor or vendor in BLOCKED:
        if vendor and BLOCKED.get(vendor) == "pending":
            return "do_not_recommend", f"{vendor} is still pending and is not an approved vendor."
        name = vendor or "This vendor"
        return "do_not_recommend", f"{name} is not on the approved vendor list."
    if vendor not in APPROVED:
        return "do_not_recommend", f"{vendor} is not on the approved vendor list."
    if not sku or sku not in MAX_COST:
        return "do_not_recommend", "The SKU is missing from the catalogue, so the price check cannot pass."
    if unit_price is None:
        return "do_not_recommend", "The quote does not state a unit price."
    if unit_price - MAX_COST[sku] > 0.001:
        return (
            "do_not_recommend",
            f"The unit price ${unit_price:.2f} is above the max unit cost for {sku}.",
        )
    if lead_time_days is None:
        return "do_not_recommend", "The quote does not state a lead time."
    if lead_time_days > 21:
        return (
            "do_not_recommend",
            f"The lead time of {lead_time_days} days is over the 21-day limit.",
        )
    if min_order is None:
        return "do_not_recommend", "The quote does not state a minimum order."
    if min_order > 600:
        return (
            "do_not_recommend",
            f"The minimum order of {min_order} units is over the 600-unit limit.",
        )
    return (
        "recommend",
        "The vendor is approved and the price, lead time, and minimum order all pass the handbook checks.",
    )


def lock_answer(document_text: str, answer: dict) -> dict:
    """Prefer visible labeled fields, then set the decision in code."""
    locked = dict(answer)
    for key, value in labeled_fields(document_text).items():
        locked[key] = value
    decision, reason = decide(
        locked.get("vendor"),
        locked.get("sku"),
        locked.get("unit_price"),
        locked.get("lead_time_days"),
        locked.get("min_order"),
    )
    locked["decision"] = decision
    locked["reason"] = reason
    return locked

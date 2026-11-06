"""Structured types for the Campus Customs vendor desk agent."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class VendorQuote(BaseModel):
    """Fields extracted from one vendor document plus the handbook decision."""

    vendor: str = Field(description="Vendor name as written in the document")
    sku: str = Field(description="Campus Customs SKU, e.g. CC-HD-006")
    unit_price: Optional[float] = Field(
        default=None, description="Quoted unit price in dollars; null if missing"
    )
    lead_time_days: Optional[int] = Field(
        default=None, description="Lead time in business days; null if missing"
    )
    min_order: Optional[int] = Field(
        default=None, description="Minimum order quantity; null if missing"
    )
    decision: Literal["recommend", "do_not_recommend"] = Field(
        description="Handbook purchasing decision"
    )
    reason: str = Field(description="One sentence explaining the decision")

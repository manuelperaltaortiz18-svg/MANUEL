"""Data model for an Amazon listing under audit.

Everything is optional except ``asin`` and ``category``: a missing field is
treated as *unknown* and penalised by the rules that need it, which is the
whole point of a data-quality audit.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Image:
    url: str = ""
    width: int = 0
    height: int = 0
    is_main: bool = False
    has_white_background: bool | None = None
    kind: str = "product"  # product | lifestyle | infographic | dimensions | packaging


@dataclass
class Review:
    rating: int = 0
    verified: bool = False
    date: str = ""
    body: str = ""


@dataclass
class Listing:
    asin: str
    category: str

    # --- Content -------------------------------------------------------
    title: str = ""
    bullets: list[str] = field(default_factory=list)
    description: str = ""
    brand: str = ""
    has_a_plus: bool = False
    a_plus_modules: int = 0
    has_brand_story: bool = False

    # --- Media ---------------------------------------------------------
    images: list[Image] = field(default_factory=list)
    has_video: bool = False
    video_count: int = 0

    # --- Keywords ------------------------------------------------------
    backend_search_terms: str = ""
    target_keywords: list[str] = field(default_factory=list)
    subject_matter: list[str] = field(default_factory=list)

    # --- Catalogue attributes -------------------------------------------
    attributes: dict[str, Any] = field(default_factory=dict)
    browse_node: str = ""
    variation_parent: str | None = None
    variation_count: int = 0

    # --- Commercial / advertising ---------------------------------------
    price: float | None = None
    list_price: float | None = None
    buybox_won: bool | None = None
    is_prime: bool | None = None
    in_stock: bool | None = None
    sponsored_products: bool = False
    sponsored_brands: bool = False
    ad_keyword_count: int = 0

    # --- Customer signals -------------------------------------------------
    rating: float | None = None
    review_count: int = 0
    reviews: list[Review] = field(default_factory=list)
    answered_questions: int = 0
    return_rate: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Listing":
        data = dict(data)
        data["images"] = [Image(**i) for i in data.get("images", [])]
        data["reviews"] = [Review(**r) for r in data.get("reviews", [])]
        known = {f for f in cls.__dataclass_fields__}
        unknown = set(data) - known
        if unknown:
            raise ValueError(f"unknown listing fields: {sorted(unknown)}")
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

"""Per-category expectations.

Amazon's real requirements come from each category's listing template and
change often. These profiles are an editable approximation: point them at
your own category data as soon as you have it.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CategoryProfile:
    name: str
    title_max: int = 200
    title_min: int = 80
    min_images: int = 6
    required_attributes: list[str] = field(default_factory=list)
    recommended_attributes: list[str] = field(default_factory=list)
    video_expected: bool = True
    a_plus_expected: bool = True


DEFAULT = CategoryProfile(
    name="default",
    required_attributes=["brand", "manufacturer", "item_weight", "country_of_origin"],
    recommended_attributes=["material", "color", "size", "item_dimensions", "model_number"],
)

PROFILES: dict[str, CategoryProfile] = {
    "default": DEFAULT,
    "beauty": CategoryProfile(
        name="beauty",
        title_max=200,
        title_min=60,
        min_images=7,
        required_attributes=["brand", "ingredients", "item_form", "net_content", "country_of_origin"],
        recommended_attributes=["skin_type", "scent", "age_range", "special_features", "item_volume"],
    ),
    "grocery": CategoryProfile(
        name="grocery",
        title_min=50,
        min_images=6,
        required_attributes=["brand", "ingredients", "net_content", "allergen_information", "country_of_origin"],
        recommended_attributes=["diet_type", "storage_instructions", "nutritional_facts", "expiry_handling"],
    ),
    "electronics": CategoryProfile(
        name="electronics",
        title_min=80,
        min_images=7,
        required_attributes=["brand", "model_number", "manufacturer", "item_weight", "power_source"],
        recommended_attributes=["connectivity", "compatible_devices", "warranty", "item_dimensions", "voltage"],
    ),
    "apparel": CategoryProfile(
        name="apparel",
        title_min=40,
        title_max=150,
        min_images=7,
        required_attributes=["brand", "material", "size", "color", "department"],
        recommended_attributes=["fit_type", "care_instructions", "closure_type", "sleeve_type", "country_of_origin"],
        video_expected=False,
    ),
    "home": CategoryProfile(
        name="home",
        min_images=6,
        required_attributes=["brand", "material", "item_dimensions", "item_weight", "color"],
        recommended_attributes=["room_type", "style", "assembly_required", "care_instructions", "capacity"],
    ),
}


def get_profile(category: str) -> CategoryProfile:
    return PROFILES.get((category or "").strip().lower(), DEFAULT)

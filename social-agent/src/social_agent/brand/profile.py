"""Carga del perfil de marca desde brand.yaml."""
from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from social_agent.models import Platform


class ContentPillar(BaseModel):
    id: str
    nombre: str
    descripcion: str


class Tone(BaseModel):
    voz: str = ""
    tratamiento: str = "tu"
    evitar: list[str] = Field(default_factory=list)
    preferir: list[str] = Field(default_factory=list)


class BrandProfile(BaseModel):
    nombre: str
    web: str = ""
    sector: str = ""
    ubicacion: str = ""
    descripcion: str = ""
    audiencia: list[str] = Field(default_factory=list)
    propuesta_valor: list[str] = Field(default_factory=list)
    tono: Tone = Field(default_factory=Tone)
    pilares: list[ContentPillar] = Field(default_factory=list)
    hashtags_base: dict[str, list[str]] = Field(default_factory=dict)
    cta: dict[str, str] = Field(default_factory=dict)

    def pillar_for_week(self, iso_week: int) -> ContentPillar:
        """Rota los pilares por numero de semana ISO: cadencia predecible
        sin necesidad de guardar estado entre ejecuciones."""
        if not self.pilares:
            raise RuntimeError("brand.yaml no define ningun pilar de contenido")
        return self.pilares[iso_week % len(self.pilares)]

    def base_hashtags(self, platform: Platform) -> list[str]:
        return list(self.hashtags_base.get(platform.value, []))

    def call_to_action(self, platform: Platform) -> str:
        return self.cta.get(platform.value, "")


def load_brand_profile(path: Path) -> BrandProfile:
    if not path.exists():
        raise FileNotFoundError(f"No existe el perfil de marca: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return BrandProfile.model_validate(data)

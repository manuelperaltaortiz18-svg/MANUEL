"""Modelos de dominio: plataformas, borradores y estados de revision."""
from __future__ import annotations

import enum
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator


class Platform(str, enum.Enum):
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"


class DraftStatus(str, enum.Enum):
    PENDING = "pending"      # generado, esperando revision humana
    APPROVED = "approved"    # aprobado, listo para publicar
    REJECTED = "rejected"    # descartado por el revisor
    PUBLISHED = "published"  # publicado con exito
    FAILED = "failed"        # intento de publicacion fallido


# Limites duros de cada plataforma. Superarlos provoca un 400 de la API,
# asi que se validan antes de encolar, no en el momento de publicar.
LIMITS = {
    Platform.LINKEDIN: {"body": 3000, "hashtags": 10, "media": False},
    Platform.INSTAGRAM: {"body": 2200, "hashtags": 30, "media": True},
}


class Draft(BaseModel):
    """Una publicacion candidata para una unica plataforma."""

    id: int | None = None
    platform: Platform
    topic: str
    body: str
    hashtags: list[str] = Field(default_factory=list)
    image_url: str | None = None
    status: DraftStatus = DraftStatus.PENDING
    scheduled_for: datetime | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    published_at: datetime | None = None
    remote_id: str | None = None
    error: str | None = None

    @field_validator("hashtags")
    @classmethod
    def _normalise_hashtags(cls, tags: list[str]) -> list[str]:
        # Los hashtags no distinguen mayusculas en ninguna de las dos
        # plataformas, asi que se deduplican sin tenerlas en cuenta pero se
        # conserva la grafia original (LinkedIn la respeta al mostrarlos).
        out: list[str] = []
        seen: set[str] = set()
        for tag in tags:
            tag = tag.strip().lstrip("#")
            if tag and tag.casefold() not in seen:
                seen.add(tag.casefold())
                out.append(tag)
        return out

    def rendered(self) -> str:
        """Texto final tal y como se envia a la API."""
        tags = " ".join(f"#{t}" for t in self.hashtags)
        return f"{self.body.strip()}\n\n{tags}".strip() if tags else self.body.strip()

    def validation_errors(self) -> list[str]:
        limits = LIMITS[self.platform]
        errors: list[str] = []
        length = len(self.rendered())
        if length > limits["body"]:
            errors.append(
                f"{self.platform.value}: {length} caracteres, maximo {limits['body']}"
            )
        if len(self.hashtags) > limits["hashtags"]:
            errors.append(
                f"{self.platform.value}: {len(self.hashtags)} hashtags, "
                f"maximo {limits['hashtags']}"
            )
        if limits["media"] and not self.image_url:
            errors.append(
                f"{self.platform.value}: requiere una imagen (image_url vacio)"
            )
        if not self.body.strip():
            errors.append(f"{self.platform.value}: cuerpo vacio")
        return errors

    def is_valid(self) -> bool:
        return not self.validation_errors()

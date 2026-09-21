"""Configuracion cargada desde variables de entorno (.env)."""
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- Generacion de contenido ---
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"

    # --- LinkedIn ---
    # Token OAuth. Para pagina de empresa necesita scope w_organization_social
    # (Community Management API, requiere aprobacion de partner de LinkedIn).
    # Para perfil personal basta con w_member_social ("Share on LinkedIn").
    linkedin_access_token: str = ""
    # URN del autor: "urn:li:organization:12345" o "urn:li:person:abc123"
    linkedin_author_urn: str = ""
    linkedin_api_version: str = "202405"

    # --- Instagram (Graph API) ---
    # Requiere cuenta Business/Creator vinculada a una Pagina de Facebook.
    instagram_access_token: str = ""
    instagram_business_account_id: str = ""
    instagram_graph_version: str = "v21.0"

    # --- Rutas ---
    brand_profile_path: Path = Field(default=REPO_ROOT / "brand.yaml")
    database_path: Path = Field(default=REPO_ROOT / "data" / "queue.db")
    media_dir: Path = Field(default=REPO_ROOT / "data" / "media")

    # --- Comportamiento ---
    # Si es True, nada se publica: solo se encola para revision humana.
    dry_run: bool = False

    def require(self, *names: str) -> None:
        missing = [n for n in names if not getattr(self, n, None)]
        if missing:
            raise RuntimeError(
                "Faltan variables de entorno obligatorias: " + ", ".join(missing)
            )


def get_settings() -> Settings:
    return Settings()

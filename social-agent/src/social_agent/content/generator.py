"""Generacion de borradores con la API de Claude."""
from __future__ import annotations

import json
import logging
from datetime import datetime

from anthropic import Anthropic

from social_agent.brand import BrandProfile
from social_agent.content.prompts import build_system_prompt, build_user_prompt
from social_agent.models import Draft, Platform
from social_agent.settings import Settings

log = logging.getLogger(__name__)

MAX_REPAIR_ATTEMPTS = 2


class GenerationError(RuntimeError):
    pass


class ContentGenerator:
    def __init__(
        self,
        settings: Settings,
        brand: BrandProfile,
        client: Anthropic | None = None,
    ) -> None:
        settings.require("anthropic_api_key")
        self._settings = settings
        self._brand = brand
        self._client = client or Anthropic(api_key=settings.anthropic_api_key)

    def generate(
        self,
        platform: Platform,
        *,
        week: int | None = None,
        briefing: str | None = None,
    ) -> Draft:
        """Genera un borrador valido, reintentando si el modelo se pasa de los
        limites de la plataforma."""
        week = week if week is not None else datetime.now().isocalendar().week
        pillar = self._brand.pillar_for_week(week)

        system = build_system_prompt(self._brand)
        user = build_user_prompt(self._brand, pillar, platform, briefing)
        messages = [{"role": "user", "content": user}]

        for attempt in range(MAX_REPAIR_ATTEMPTS + 1):
            raw = self._complete(system, messages)
            try:
                payload = _parse_json(raw)
            except ValueError as exc:
                if attempt == MAX_REPAIR_ATTEMPTS:
                    raise GenerationError(f"Respuesta no parseable: {exc}") from exc
                messages += [
                    {"role": "assistant", "content": raw},
                    {"role": "user", "content": "Eso no es JSON valido. Devuelve solo el JSON pedido."},
                ]
                continue

            draft = Draft(
                platform=platform,
                topic=payload.get("topic") or pillar.nombre,
                body=payload.get("body", ""),
                hashtags=payload.get("hashtags", []),
            )
            # image_brief no es parte del contrato de Draft: viaja como nota
            # para quien tenga que hacer la foto.
            draft.error = payload.get("image_brief") or None

            # Instagram exige imagen, pero eso lo resuelve el revisor humano
            # al adjuntarla, no el generador. Se ignora aqui a proposito.
            problems = [
                e for e in draft.validation_errors() if "requiere una imagen" not in e
            ]
            if not problems:
                return draft

            if attempt == MAX_REPAIR_ATTEMPTS:
                raise GenerationError(
                    "El modelo no respeto los limites tras "
                    f"{MAX_REPAIR_ATTEMPTS + 1} intentos: {problems}"
                )
            log.warning("Borrador fuera de limites, reintentando: %s", problems)
            messages += [
                {"role": "assistant", "content": raw},
                {
                    "role": "user",
                    "content": "Corrige y devuelve el JSON de nuevo. Problemas: "
                    + "; ".join(problems),
                },
            ]

        raise GenerationError("Generacion agotada sin resultado valido")

    def generate_week(
        self,
        platforms: list[Platform],
        *,
        week: int | None = None,
        briefing: str | None = None,
    ) -> list[Draft]:
        return [
            self.generate(p, week=week, briefing=briefing) for p in platforms
        ]

    def _complete(self, system: str, messages: list[dict]) -> str:
        response = self._client.messages.create(
            model=self._settings.anthropic_model,
            max_tokens=2000,
            system=system,
            messages=messages,
        )
        return "".join(
            block.text for block in response.content if block.type == "text"
        )


def _parse_json(raw: str) -> dict:
    """Extrae el objeto JSON aunque el modelo lo envuelva en ```json."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no se encontro ningun objeto JSON")
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ValueError(str(exc)) from exc

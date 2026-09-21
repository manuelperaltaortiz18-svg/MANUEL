"""Construccion del prompt de generacion a partir del perfil de marca."""
from __future__ import annotations

from social_agent.brand import BrandProfile, ContentPillar
from social_agent.models import LIMITS, Platform

_PLATFORM_BRIEF = {
    Platform.LINKEDIN: (
        "LinkedIn. Publico profesional. Gancho en la primera linea (se corta a "
        "~200 caracteres en el feed). Parrafos de 1-2 frases separados por linea "
        "en blanco. Sin emojis decorativos. Aporta un dato o aprendizaje concreto."
    ),
    Platform.INSTAGRAM: (
        "Instagram. Publico mas visual y general. La imagen manda: el texto la "
        "acompaña, no la repite. Primera linea que funcione sola. Tono mas "
        "cercano. Como mucho dos emojis, y solo si aportan."
    ),
}


def build_system_prompt(brand: BrandProfile) -> str:
    tono = brand.tono
    evitar = "\n".join(f"- {x}" for x in tono.evitar) or "- (sin restricciones)"
    preferir = "\n".join(f"- {x}" for x in tono.preferir) or "- (sin preferencias)"
    audiencia = "\n".join(f"- {x}" for x in brand.audiencia) or "- (sin definir)"
    valor = "\n".join(f"- {x}" for x in brand.propuesta_valor) or "- (sin definir)"

    return f"""Eres el responsable de comunicacion en redes sociales de {brand.nombre} ({brand.web}).

NEGOCIO
Sector: {brand.sector}
Ubicacion: {brand.ubicacion}
{brand.descripcion.strip()}

AUDIENCIA
{audiencia}

PROPUESTA DE VALOR
{valor}

TONO
Voz: {tono.voz}
Tratamiento: {tono.tratamiento}

Evita:
{evitar}

Prefiere:
{preferir}

REGLAS
- Escribe en español de España.
- Una sola idea por publicacion.
- Nada de datos inventados: no cites cifras, clientes, premios ni plazos que no
  se te hayan dado en el briefing. Si te falta un dato concreto, escribe sobre
  lo que si sabes en lugar de rellenar.
- No prometas precios ni plazos de entrega.
- Devuelve exclusivamente JSON valido, sin texto alrededor ni bloques de codigo."""


def build_user_prompt(
    brand: BrandProfile,
    pillar: ContentPillar,
    platform: Platform,
    briefing: str | None = None,
) -> str:
    limits = LIMITS[platform]
    base_tags = brand.base_hashtags(platform)
    cta = brand.call_to_action(platform)

    extra = (
        f"\nBRIEFING DE ESTA SEMANA (usalo como material de partida):\n{briefing.strip()}\n"
        if briefing
        else "\nNo hay briefing especifico: escribe algo util y atemporal dentro del pilar.\n"
    )

    return f"""Escribe una publicacion para {platform.value}.

PILAR DE CONTENIDO: {pillar.nombre}
{pillar.descripcion}

PLATAFORMA
{_PLATFORM_BRIEF[platform]}
{extra}
RESTRICCIONES
- El texto del campo "body" debe tener como maximo {limits['body'] - 200} caracteres
  (se le añadiran los hashtags despues).
- Como maximo {limits['hashtags']} hashtags, en minusculas y sin el simbolo #.
- Incluye estos hashtags entre los elegidos: {', '.join(base_tags) or '(ninguno obligatorio)'}
- Termina el body con esta llamada a la accion, adaptada con naturalidad: "{cta}"

Devuelve este JSON:
{{"topic": "<titulo interno de 5-8 palabras>",
  "body": "<texto de la publicacion>",
  "hashtags": ["tag1", "tag2"],
  "image_brief": "<descripcion en una frase de la foto que deberia acompañarla>"}}"""

"""Construccion de los publicadores disponibles segun la configuracion."""
from __future__ import annotations

import logging

from social_agent.models import Platform
from social_agent.publishers.base import Publisher
from social_agent.publishers.instagram import InstagramPublisher
from social_agent.publishers.linkedin import LinkedInPublisher
from social_agent.settings import Settings

log = logging.getLogger(__name__)


def build_publishers(settings: Settings) -> dict[Platform, Publisher]:
    """Solo devuelve las plataformas con credenciales completas. Una plataforma
    a medio configurar se omite con un aviso en lugar de romper el arranque."""
    publishers: dict[Platform, Publisher] = {}

    if settings.linkedin_access_token and settings.linkedin_author_urn:
        publishers[Platform.LINKEDIN] = LinkedInPublisher(
            settings.linkedin_access_token,
            settings.linkedin_author_urn,
            api_version=settings.linkedin_api_version,
        )
    else:
        log.warning("LinkedIn sin configurar: se omite")

    if settings.instagram_access_token and settings.instagram_business_account_id:
        publishers[Platform.INSTAGRAM] = InstagramPublisher(
            settings.instagram_access_token,
            settings.instagram_business_account_id,
            graph_version=settings.instagram_graph_version,
        )
    else:
        log.warning("Instagram sin configurar: se omite")

    return publishers

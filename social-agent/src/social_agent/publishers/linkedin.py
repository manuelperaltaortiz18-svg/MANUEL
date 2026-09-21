"""Publicacion en LinkedIn via la Posts API (versionada).

Nota de acceso, que es lo que suele bloquear este integrador:
- Autor = urn:li:person:*  -> scope w_member_social, producto "Share on
  LinkedIn". Solo publica en el perfil del usuario que autoriza. Accesible.
- Autor = urn:li:organization:* -> scope w_organization_social, producto
  "Community Management API". Requiere aprobacion de partner de LinkedIn.

El token de LinkedIn caduca a los 60 dias y no hay refresh token en el flujo
estandar: hay que reautorizar a mano. `verify_token` sirve para detectarlo
antes de que falle una publicacion.
"""
from __future__ import annotations

import httpx

from social_agent.models import Draft, Platform
from social_agent.publishers.base import PublishError, PublishResult, Publisher

API_BASE = "https://api.linkedin.com"


class LinkedInPublisher(Publisher):
    platform = Platform.LINKEDIN

    def __init__(
        self,
        access_token: str,
        author_urn: str,
        *,
        api_version: str = "202405",
        client: httpx.Client | None = None,
    ) -> None:
        if not author_urn.startswith(("urn:li:person:", "urn:li:organization:")):
            raise ValueError(
                "linkedin_author_urn debe ser urn:li:person:* o urn:li:organization:*"
            )
        self._author = author_urn
        self._client = client or httpx.Client(timeout=30.0)
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": api_version,
            "Content-Type": "application/json",
        }

    def verify_token(self) -> bool:
        """True si el token sigue vivo. Un 401 aqui significa reautorizar."""
        resp = self._client.get(
            f"{API_BASE}/v2/userinfo", headers=self._headers
        )
        return resp.status_code == 200

    def publish(self, draft: Draft) -> PublishResult:
        payload = {
            "author": self._author,
            "commentary": draft.rendered(),
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }

        try:
            resp = self._client.post(
                f"{API_BASE}/rest/posts", headers=self._headers, json=payload
            )
        except httpx.HTTPError as exc:
            raise PublishError(f"LinkedIn inalcanzable: {exc}", retryable=True) from exc

        if resp.status_code in (200, 201):
            # El id del post viaja en la cabecera, no en el cuerpo.
            post_id = resp.headers.get("x-restli-id") or resp.headers.get("X-RestLi-Id")
            if not post_id:
                raise PublishError("LinkedIn no devolvio el id del post")
            return PublishResult(
                remote_id=post_id,
                url=f"https://www.linkedin.com/feed/update/{post_id}",
            )

        detail = resp.text[:500]
        if resp.status_code == 401:
            raise PublishError(
                "LinkedIn 401: token caducado o revocado, hay que reautorizar. "
                f"{detail}"
            )
        if resp.status_code == 403:
            raise PublishError(
                "LinkedIn 403: la app no tiene permiso para publicar como "
                f"{self._author}. Para una pagina de empresa hace falta el "
                f"producto Community Management API aprobado. {detail}"
            )
        raise PublishError(
            f"LinkedIn {resp.status_code}: {detail}",
            retryable=resp.status_code == 429 or resp.status_code >= 500,
        )

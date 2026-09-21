"""Publicacion en Instagram via Graph API.

Requisitos que no se pueden sortear desde el codigo:
- La cuenta debe ser Business o Creator (una cuenta personal no puede publicar
  por API bajo ningun concepto).
- Debe estar vinculada a una Pagina de Facebook.
- La imagen tiene que estar en una URL publica accesible por los servidores de
  Meta: no se sube el binario, se les pasa el enlace.
- Limite de 50 publicaciones por cada 24 horas.

El flujo es en dos pasos: crear un contenedor de medios y luego publicarlo.
"""
from __future__ import annotations

import time

import httpx

from social_agent.models import Draft, Platform
from social_agent.publishers.base import PublishError, PublishResult, Publisher

GRAPH_BASE = "https://graph.facebook.com"

# Meta procesa la imagen de forma asincrona: el contenedor no es publicable
# hasta que termina. Se sondea en lugar de asumir que esta listo.
_POLL_INTERVAL_S = 2.0
_POLL_MAX_ATTEMPTS = 15


class InstagramPublisher(Publisher):
    platform = Platform.INSTAGRAM

    def __init__(
        self,
        access_token: str,
        business_account_id: str,
        *,
        graph_version: str = "v21.0",
        client: httpx.Client | None = None,
        poll_interval_s: float = _POLL_INTERVAL_S,
    ) -> None:
        self._token = access_token
        self._account = business_account_id
        self._base = f"{GRAPH_BASE}/{graph_version}"
        self._client = client or httpx.Client(timeout=60.0)
        self._poll_interval_s = poll_interval_s

    def publish(self, draft: Draft) -> PublishResult:
        if not draft.image_url:
            raise PublishError(
                "Instagram requiere una imagen: el borrador no tiene image_url"
            )

        container_id = self._create_container(draft)
        self._wait_until_ready(container_id)
        media_id = self._publish_container(container_id)
        permalink = self._permalink(media_id)
        return PublishResult(remote_id=media_id, url=permalink)

    # --- pasos del flujo ---

    def _create_container(self, draft: Draft) -> str:
        data = self._post(
            f"{self._base}/{self._account}/media",
            {"image_url": draft.image_url, "caption": draft.rendered()},
        )
        container_id = data.get("id")
        if not container_id:
            raise PublishError(f"Instagram no devolvio id de contenedor: {data}")
        return container_id

    def _wait_until_ready(self, container_id: str) -> None:
        for _ in range(_POLL_MAX_ATTEMPTS):
            data = self._get(
                f"{self._base}/{container_id}", {"fields": "status_code,status"}
            )
            status = data.get("status_code")
            if status == "FINISHED":
                return
            if status == "ERROR":
                raise PublishError(
                    f"Instagram no pudo procesar la imagen: {data.get('status')}"
                )
            time.sleep(self._poll_interval_s)
        raise PublishError(
            "Instagram no termino de procesar la imagen a tiempo", retryable=True
        )

    def _publish_container(self, container_id: str) -> str:
        data = self._post(
            f"{self._base}/{self._account}/media_publish",
            {"creation_id": container_id},
        )
        media_id = data.get("id")
        if not media_id:
            raise PublishError(f"Instagram no devolvio id de publicacion: {data}")
        return media_id

    def _permalink(self, media_id: str) -> str | None:
        try:
            return self._get(
                f"{self._base}/{media_id}", {"fields": "permalink"}
            ).get("permalink")
        except PublishError:
            # El post ya esta publicado; no tener el enlace no es un fallo.
            return None

    # --- transporte ---

    def _get(self, url: str, params: dict) -> dict:
        return self._request("GET", url, params={**params, "access_token": self._token})

    def _post(self, url: str, params: dict) -> dict:
        return self._request("POST", url, data={**params, "access_token": self._token})

    def _request(self, method: str, url: str, **kwargs) -> dict:
        try:
            resp = self._client.request(method, url, **kwargs)
        except httpx.HTTPError as exc:
            raise PublishError(f"Instagram inalcanzable: {exc}", retryable=True) from exc

        if resp.status_code == 200:
            return resp.json()

        try:
            error = resp.json().get("error", {})
        except ValueError:
            error = {}
        message = error.get("message", resp.text[:500])
        code = error.get("code")

        if code == 190:
            raise PublishError(
                f"Instagram: token caducado o invalido, hay que reautorizar. {message}"
            )
        if code == 4 or code == 32 or resp.status_code == 429:
            raise PublishError(
                f"Instagram: limite de peticiones alcanzado. {message}", retryable=True
            )
        raise PublishError(
            f"Instagram {resp.status_code} (code={code}): {message}",
            retryable=resp.status_code >= 500,
        )

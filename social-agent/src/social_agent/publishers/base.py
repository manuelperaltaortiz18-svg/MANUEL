"""Contrato comun de los publicadores."""
from __future__ import annotations

import abc
from dataclasses import dataclass

from social_agent.models import Draft, Platform


@dataclass(frozen=True)
class PublishResult:
    remote_id: str
    url: str | None = None


class PublishError(RuntimeError):
    """Fallo al publicar. `retryable` distingue un 5xx/rate-limit de un 400
    por contenido invalido, que no mejora reintentando."""

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class Publisher(abc.ABC):
    platform: Platform

    @abc.abstractmethod
    def publish(self, draft: Draft) -> PublishResult: ...
